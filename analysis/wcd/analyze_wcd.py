#!/usr/bin/env python3
"""Prepare, analyze, and replot reproducible WCD campaigns of any duration."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import platform
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Keep script execution and importlib-based tests equally portable.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scientific_plots import plot_all as plot_all_scientific


COMPONENTS = ("electromagnetic", "muonic", "hadronic", "unknown")
COMPONENT_LABEL = {
    "electromagnetic": "Electromagnetic",
    "muonic": "Muonic",
    "hadronic": "Hadronic",
    "unknown": "Unknown",
}
COMPONENT_COLOR = {
    "electromagnetic": "#2563eb",
    "muonic": "#dc2626",
    "hadronic": "#059669",
    "unknown": "#64748b",
}

# Códigos CORSIKA presentes o aceptados por MEIGA. Los núcleos (>=100) se
# clasifican de manera genérica como hadrones.
CORSIKA_TO_PARTICLE: dict[int, tuple[int, str, str]] = {
    1: (22, "gamma", "electromagnetic"),
    2: (-11, "e+", "electromagnetic"),
    3: (11, "e-", "electromagnetic"),
    5: (-13, "mu+", "muonic"),
    6: (13, "mu-", "muonic"),
    7: (111, "pi0", "hadronic"),
    8: (211, "pi+", "hadronic"),
    9: (-211, "pi-", "hadronic"),
    10: (130, "K0L", "hadronic"),
    11: (321, "K+", "hadronic"),
    12: (-321, "K-", "hadronic"),
    13: (2112, "n", "hadronic"),
    14: (2212, "p", "hadronic"),
    15: (-2212, "anti-p", "hadronic"),
    16: (310, "K0S", "hadronic"),
    17: (221, "eta", "hadronic"),
    18: (3122, "Lambda", "hadronic"),
    19: (3222, "Sigma+", "hadronic"),
    20: (3212, "Sigma0", "hadronic"),
    21: (3112, "Sigma-", "hadronic"),
    22: (3322, "Xi0", "hadronic"),
    23: (3312, "Xi-", "hadronic"),
    24: (3332, "Omega-", "hadronic"),
}


@dataclass(frozen=True)
class FluxParticle:
    original_index: int
    raw_line: str
    corsika_id: int
    pdg_id: int
    species: str
    component: str
    px_gev: float
    py_gev: float
    pz_gev: float
    x_cm: float
    y_cm: float
    z_cm: float
    shower_id: int
    primary_corsika_id: int
    primary_energy_gev: float
    primary_theta_deg: float
    primary_phi_deg: float

    @property
    def momentum_gev(self) -> float:
        return math.sqrt(self.px_gev**2 + self.py_gev**2 + self.pz_gev**2)

    @property
    def zenith_deg(self) -> float:
        if self.momentum_gev == 0:
            return float("nan")
        cosine = max(-1.0, min(1.0, self.pz_gev / self.momentum_gev))
        return math.degrees(math.acos(cosine))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def particle_info(corsika_id: int) -> tuple[int, str, str]:
    if corsika_id in CORSIKA_TO_PARTICLE:
        return CORSIKA_TO_PARTICLE[corsika_id]
    if 100 <= corsika_id < 9900:
        mass_number, atomic_number = divmod(corsika_id, 100)
        pdg = 1_000_000_000 + 1000 * atomic_number + mass_number
        return pdg, f"nucleus-A{mass_number}-Z{atomic_number}", "hadronic"
    return 0, f"corsika-{corsika_id}", "unknown"


def read_flux(path: Path) -> tuple[list[str], list[FluxParticle]]:
    headers: list[str] = []
    particles: list[FluxParticle] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                headers.append(line if line.endswith("\n") else line + "\n")
                continue
            fields = stripped.split()
            if len(fields) != 12:
                raise ValueError(
                    f"{path}:{line_number}: se esperaban 12 columnas y hay {len(fields)}"
                )
            corsika_id = int(fields[0])
            pdg_id, species, component = particle_info(corsika_id)
            particles.append(
                FluxParticle(
                    original_index=len(particles),
                    raw_line=stripped,
                    corsika_id=corsika_id,
                    pdg_id=pdg_id,
                    species=species,
                    component=component,
                    px_gev=float(fields[1]),
                    py_gev=float(fields[2]),
                    pz_gev=float(fields[3]),
                    x_cm=float(fields[4]),
                    y_cm=float(fields[5]),
                    z_cm=float(fields[6]),
                    shower_id=int(fields[7]),
                    primary_corsika_id=int(fields[8]),
                    primary_energy_gev=float(fields[9]),
                    primary_theta_deg=float(fields[10]),
                    primary_phi_deg=float(fields[11]),
                )
            )
    if not particles:
        raise ValueError(f"El flujo no contiene partículas: {path}")
    return headers, particles


def stratified_sample(
    particles: Sequence[FluxParticle], maximum: int
) -> list[FluxParticle]:
    if maximum <= 0 or maximum >= len(particles):
        return list(particles)
    buckets: dict[str, list[FluxParticle]] = defaultdict(list)
    for particle in particles:
        buckets[particle.component].append(particle)
    selected: list[FluxParticle] = []
    cursors = {component: 0 for component in COMPONENTS}
    while len(selected) < maximum:
        progressed = False
        for component in COMPONENTS:
            cursor = cursors[component]
            if cursor < len(buckets[component]) and len(selected) < maximum:
                selected.append(buckets[component][cursor])
                cursors[component] += 1
                progressed = True
        if not progressed:
            break
    return sorted(selected, key=lambda particle: particle.original_index)


def write_flux(path: Path, headers: Sequence[str], particles: Sequence[FluxParticle]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.writelines(headers)
        for particle in particles:
            stream.write(particle.raw_line + "\n")


def read_json(path: Path) -> dict[str, Any]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=False)
        stream.write("\n")


def make_meiga_config(
    seed: int,
    create_visualization: bool = False,
    simulation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    simulation = simulation or {}
    return {
        "Input": {
            "Mode": "UseARTI",
            "InputFileName": "./input.shw",
            "InputNParticles": 0,
        },
        "DetectorList": "./DetectorList.xml",
        "DetectorProperties": "./DetectorProperties.xml",
        "Output": {
            "OutputFile": "./output.json",
            "CompressOutput": True,
            "SaveInput": True,
            "SavePETimeDistribution": True,
            "SaveComponentsPETimeDistribution": False,
            "SaveTraces": False,
            "SaveEnergy": True,
            "SaveComponentsEnergy": False,
            "SaveCharge": True,
            "SaveCounts": False,
        },
        "Simulation": {
            "SimulationMode": simulation.get("mode", "eFast"),
            "GeoVisOn": create_visualization,
            "TrajVisOn": False,
            "CheckOverlaps": bool(simulation.get("check_overlaps", False)),
            "RenderFile": "VRML2FILE",
            "PhysicsName": simulation.get("physics_list", "QGSP_BERT_HP"),
            "RandomSeed": seed,
            "DeterministicEventSeeds": bool(simulation.get("deterministic_event_seeds", False)),
            "Verbosity": int(simulation.get("verbosity", 0)),
        },
    }


def prepare_campaign(args: argparse.Namespace) -> None:
    experiment = args.experiment.resolve()
    run_dir = args.run_dir.resolve()
    detector_list = experiment / "DetectorList.xml"
    detector_properties = experiment / "DetectorProperties.xml"
    campaign_path = experiment / "campaign.json"
    for required in (detector_list, detector_properties, campaign_path):
        if not required.is_file():
            raise FileNotFoundError(required)
    campaign = read_json(campaign_path)
    source = experiment / str(campaign["input_file"])
    if not source.is_file():
        raise FileNotFoundError(source)

    requested = [item.strip() for item in args.scenarios.split(",") if item.strip()]
    allowed = {"all", "electromagnetic", "muonic", "hadronic"}
    invalid = set(requested) - allowed
    if invalid:
        raise ValueError(f"Escenarios desconocidos: {sorted(invalid)}")
    if "all" not in requested:
        raise ValueError("La campaña debe incluir el escenario 'all'")

    headers, all_particles = read_flux(source)
    selected = stratified_sample(all_particles, args.max_particles)
    scenarios_root = run_dir / "scenarios"
    scenarios_root.mkdir(parents=True, exist_ok=True)
    scenario_counts: dict[str, dict[str, int]] = {}
    for scenario_index, scenario in enumerate(requested):
        scenario_particles = (
            selected
            if scenario == "all"
            else [particle for particle in selected if particle.component == scenario]
        )
        if not scenario_particles:
            raise ValueError(f"El escenario {scenario} no tiene partículas")
        scenario_dir = scenarios_root / scenario
        scenario_dir.mkdir(parents=True, exist_ok=False)
        write_flux(scenario_dir / "input.shw", headers, scenario_particles)
        shutil.copy2(detector_list, scenario_dir / "DetectorList.xml")
        shutil.copy2(detector_properties, scenario_dir / "DetectorProperties.xml")
        # Una corrida puede contener varios escenarios, pero solo `all` escribe
        # la geometría VRML. Así se obtiene exactamente un .wrl por corrida.
        write_json(
            scenario_dir / "config.json",
            make_meiga_config(
                args.seed + scenario_index,
                create_visualization=scenario == "all",
                simulation=campaign.get("simulation", {}),
            ),
        )
        scenario_counts[scenario] = dict(Counter(p.component for p in scenario_particles))

    complete_exposure = len(selected) == len(all_particles)
    preparation = {
        "campaign": campaign,
        "source": {
            "path": str(source),
            "sha256": sha256(source),
            "particles_full": len(all_particles),
            "particles_selected": len(selected),
            "complete_exposure": complete_exposure,
            "complete_30s_exposure": complete_exposure and float(campaign["duration_s"]) == 30.0,
            "component_counts_full": dict(Counter(p.component for p in all_particles)),
            "species_counts_full": dict(Counter(p.species for p in all_particles)),
        },
        "requested_scenarios": requested,
        "scenario_component_counts": scenario_counts,
        "visualization": {
            "format": "VRML2",
            "scenario": "all",
            "output_file": "visualization.wrl",
            "trajectories": False,
        },
        "random_seed_base": args.seed,
        "python": sys.version,
    }
    write_json(run_dir / "preparation.json", preparation)
    print(json.dumps(preparation, ensure_ascii=False, indent=2))


def sorted_event_items(document: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    events: list[tuple[int, dict[str, Any]]] = []
    for name, value in document.get("Output", {}).items():
        if name.startswith("Event_"):
            events.append((int(name.rsplit("_", 1)[1]), value))
    return sorted(events)


def percentile(values: Sequence[float], probability: float) -> float | None:
    if not values:
        return None
    return float(np.quantile(np.asarray(values, dtype=float), probability))


def event_timing(times: Sequence[float]) -> dict[str, float | int | None]:
    if not times:
        return {
            "n_times": 0,
            "time_first_ns": None,
            "time_mean_ns": None,
            "time_rms_ns": None,
            "time_t10_ns": None,
            "time_t50_ns": None,
            "time_t90_ns": None,
            "time_width_10_90_ns": None,
            "late_fraction_50ns": None,
        }
    array = np.sort(np.asarray(times, dtype=float))
    relative = array - array[0]
    q10, q50, q90 = np.quantile(relative, [0.1, 0.5, 0.9])
    return {
        "n_times": int(array.size),
        "time_first_ns": float(array[0]),
        "time_mean_ns": float(np.mean(array)),
        "time_rms_ns": float(np.std(relative)),
        "time_t10_ns": float(q10),
        "time_t50_ns": float(q50),
        "time_t90_ns": float(q90),
        "time_width_10_90_ns": float(q90 - q10),
        "late_fraction_50ns": float(np.mean(relative > 50.0)),
    }


def extract_scenario(
    scenario_dir: Path, scenario: str, acquisition_window_ns: float
) -> list[dict[str, Any]]:
    _, flux = read_flux(scenario_dir / "input.shw")
    output_path = scenario_dir / "output.json.gz"
    if not output_path.is_file():
        output_path = scenario_dir / "output.json"
    if not output_path.is_file():
        raise FileNotFoundError(f"Falta salida para {scenario}: {output_path}")
    document = read_json(output_path)
    output_events = sorted_event_items(document)
    if len(output_events) != len(flux):
        raise ValueError(
            f"{scenario}: entrada={len(flux)} eventos, salida={len(output_events)} eventos"
        )

    rows: list[dict[str, Any]] = []
    for particle, (event_id, event) in zip(flux, output_events):
        input_flux = event.get("InputFlux", {})
        detector = event.get("Detector_0", {})
        device = detector.get("OptDevice_0", {})
        times = [float(value) for value in device.get("PETimeDistribution", [])]
        gated_times = [value for value in times if 0.0 <= value <= acquisition_window_ns]
        output_pdg = int(input_flux.get("ID", particle.pdg_id))
        if output_pdg != particle.pdg_id:
            raise ValueError(
                f"{scenario}/Event_{event_id}: PDG de salida {output_pdg} != {particle.pdg_id}"
            )
        timing = event_timing(gated_times)
        raw_charge = int(device.get("Charge", len(times)))
        row: dict[str, Any] = {
            "scenario": scenario,
            "event_id": event_id,
            "source_index": particle.original_index,
            "shower_id": particle.shower_id,
            "corsika_id": particle.corsika_id,
            "pdg_id": particle.pdg_id,
            "species": particle.species,
            "component": particle.component,
            "momentum_GeV_c": particle.momentum_gev,
            "zenith_deg": particle.zenith_deg,
            "primary_energy_GeV": particle.primary_energy_gev,
            "primary_theta_deg": particle.primary_theta_deg,
            "primary_phi_deg": particle.primary_phi_deg,
            "energy_deposit_MeV": float(detector.get("EnergyDeposit", 0.0)),
            "charge_pe": len(gated_times),
            "charge_raw_meiga_pe": raw_charge,
            "pe_outside_acquisition_window": raw_charge - len(gated_times),
            "time_max_raw_ns": max(times) if times else None,
            **timing,
            "_times_ns": times,
            "_times_gate_ns": gated_times,
        }
        if raw_charge != len(times):
            raise ValueError(
                f"{scenario}/Event_{event_id}: Charge={raw_charge} pero hay {len(times)} tiempos"
            )
        rows.append(row)
    return rows


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> list[float | None]:
    if trials == 0:
        return [None, None]
    proportion = successes / trials
    denominator = 1 + z * z / trials
    center = (proportion + z * z / (2 * trials)) / denominator
    half_width = (
        z
        * math.sqrt(proportion * (1 - proportion) / trials + z * z / (4 * trials * trials))
        / denominator
    )
    return [center - half_width, center + half_width]


def group_summary(rows: Sequence[dict[str, Any]], duration: float) -> dict[str, Any]:
    charges = [int(row["charge_pe"]) for row in rows]
    positive_charges = [charge for charge in charges if charge > 0]
    energies = [float(row["energy_deposit_MeV"]) for row in rows]
    widths = [
        float(row["time_width_10_90_ns"])
        for row in rows
        if row["time_width_10_90_ns"] is not None
    ]
    late = [
        float(row["late_fraction_50ns"])
        for row in rows
        if row["late_fraction_50ns"] is not None
    ]
    n_events = len(rows)
    n_triggered = len(positive_charges)
    efficiency = n_triggered / n_events if n_events else 0.0
    return {
        "injected": n_events,
        "triggered_q_ge_1pe": n_triggered,
        "trigger_efficiency": efficiency,
        "trigger_efficiency_wilson95": wilson_interval(n_triggered, n_events),
        "injected_rate_Hz": n_events / duration,
        "trigger_rate_Hz": n_triggered / duration,
        "trigger_rate_poisson_error_Hz": math.sqrt(n_triggered) / duration,
        "zero_charge_fraction": 1.0 - efficiency,
        "charge_sum_pe": int(sum(charges)),
        "charge_raw_meiga_sum_pe": int(sum(row["charge_raw_meiga_pe"] for row in rows)),
        "pe_outside_acquisition_window": int(
            sum(row["pe_outside_acquisition_window"] for row in rows)
        ),
        "charge_mean_all_pe": float(np.mean(charges)) if charges else 0.0,
        "charge_mean_triggered_pe": float(np.mean(positive_charges)) if positive_charges else None,
        "charge_quantiles_triggered_pe": {
            "p10": percentile(positive_charges, 0.10),
            "p50": percentile(positive_charges, 0.50),
            "p90": percentile(positive_charges, 0.90),
            "p99": percentile(positive_charges, 0.99),
            "p999": percentile(positive_charges, 0.999),
        },
        "energy_deposit_sum_MeV": float(sum(energies)),
        "energy_deposit_mean_MeV": float(np.mean(energies)) if energies else 0.0,
        "pulse_width_10_90_median_ns": percentile(widths, 0.50),
        "pulse_width_10_90_p90_ns": percentile(widths, 0.90),
        "late_fraction_50ns_mean": float(np.mean(late)) if late else None,
    }


def summarize_full(rows: Sequence[dict[str, Any]], duration: float, radius: float) -> dict[str, Any]:
    total_charge = sum(int(row["charge_pe"]) for row in rows)
    total_energy = sum(float(row["energy_deposit_MeV"]) for row in rows)
    summary: dict[str, Any] = {
        "duration_s": duration,
        "injection_radius_m": radius,
        "injection_area_m2": math.pi * radius * radius,
        "incident_flux_on_injection_disk_m-2_s-1": len(rows)
        / (duration * math.pi * radius * radius),
        "total": group_summary(rows, duration),
        "components": {},
        "species": {},
    }
    for component in COMPONENTS:
        selected = [row for row in rows if row["component"] == component]
        if not selected:
            continue
        entry = group_summary(selected, duration)
        entry["fraction_of_injected"] = len(selected) / len(rows)
        entry["fraction_of_total_charge"] = (
            sum(int(row["charge_pe"]) for row in selected) / total_charge
            if total_charge
            else 0.0
        )
        entry["fraction_of_total_deposited_energy"] = (
            sum(float(row["energy_deposit_MeV"]) for row in selected) / total_energy
            if total_energy
            else 0.0
        )
        summary["components"][component] = entry
    for species in sorted({str(row["species"]) for row in rows}):
        selected = [row for row in rows if row["species"] == species]
        summary["species"][species] = group_summary(selected, duration)
    return summary


CSV_COLUMNS = [
    "scenario",
    "event_id",
    "source_index",
    "shower_id",
    "corsika_id",
    "pdg_id",
    "species",
    "component",
    "momentum_GeV_c",
    "zenith_deg",
    "primary_energy_GeV",
    "primary_theta_deg",
    "primary_phi_deg",
    "energy_deposit_MeV",
    "charge_pe",
    "charge_raw_meiga_pe",
    "pe_outside_acquisition_window",
    "time_max_raw_ns",
    "n_times",
    "time_first_ns",
    "time_mean_ns",
    "time_rms_ns",
    "time_t10_ns",
    "time_t50_ns",
    "time_t90_ns",
    "time_width_10_90_ns",
    "late_fraction_50ns",
]


def write_event_table(rows: Sequence[dict[str, Any]], path: Path) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in CSV_COLUMNS})


def build_shower_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[int(row["shower_id"])].append(row)
    result: list[dict[str, Any]] = []
    for shower_id, events in sorted(groups.items()):
        item: dict[str, Any] = {
            "shower_id": shower_id,
            "multiplicity": len(events),
            "triggered_particles": sum(int(row["charge_pe"] > 0) for row in events),
            "charge_total_pe": sum(int(row["charge_pe"]) for row in events),
            "energy_deposit_total_MeV": sum(float(row["energy_deposit_MeV"]) for row in events),
            "primary_energy_GeV": float(events[0]["primary_energy_GeV"]),
            "primary_theta_deg": float(events[0]["primary_theta_deg"]),
        }
        for component in COMPONENTS:
            item[f"charge_{component}_pe"] = sum(
                int(row["charge_pe"]) for row in events if row["component"] == component
            )
        result.append(item)
    return result


def write_shower_table(rows: Sequence[dict[str, Any]], path: Path) -> None:
    if not rows:
        return
    columns = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def setup_plot_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "#f8fafc",
            "axes.edgecolor": "#475569",
            "axes.labelcolor": "#0f172a",
            "axes.titleweight": "bold",
            "font.size": 10,
            "grid.color": "#cbd5e1",
            "grid.alpha": 0.55,
            "legend.frameon": False,
            "text.color": "#0f172a",
        }
    )


def component_rows(rows: Sequence[dict[str, Any]], component: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["component"] == component]


def present_components(rows: Sequence[dict[str, Any]]) -> list[str]:
    return [component for component in COMPONENTS if component_rows(rows, component)]


def positive_log_edges(values: Sequence[float], bins: int = 55) -> np.ndarray:
    positive = np.asarray([value for value in values if value > 0], dtype=float)
    if positive.size == 0:
        return np.geomspace(0.5, 1.5, bins)
    upper = max(1.5, float(np.quantile(positive, 0.999)) * 1.05)
    return np.geomspace(0.5, upper, bins)


def save_figure(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_composition(rows: Sequence[dict[str, Any]], duration: float, path: Path) -> None:
    components = present_components(rows)
    injected = [len(component_rows(rows, component)) / duration for component in components]
    triggered = [
        sum(row["charge_pe"] > 0 for row in component_rows(rows, component)) / duration
        for component in components
    ]
    charge_sums = [
        sum(row["charge_pe"] for row in component_rows(rows, component))
        for component in components
    ]
    total_charge = sum(charge_sums) or 1
    x = np.arange(len(components))
    width = 0.36
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    axes[0].bar(x - width / 2, injected, width, label="Inyectadas", color="#94a3b8")
    axes[0].bar(
        x + width / 2,
        triggered,
        width,
        label="Q ≥ 1 PE",
        color=[COMPONENT_COLOR[c] for c in components],
    )
    axes[0].set_xticks(x, [COMPONENT_LABEL[c] for c in components])
    axes[0].set_ylabel("Tasa de la campaña [s⁻¹]")
    axes[0].set_title("Flujo inyectado y respuesta")
    axes[0].set_yscale("log")
    axes[0].grid(axis="y")
    axes[0].legend()
    fractions = [100 * value / total_charge for value in charge_sums]
    axes[1].bar(
        [COMPONENT_LABEL[c] for c in components],
        fractions,
        color=[COMPONENT_COLOR[c] for c in components],
    )
    axes[1].set_ylabel("Fracción de la carga total [%]")
    axes[1].set_title("Aporte al histograma de carga")
    axes[1].grid(axis="y")
    for index, value in enumerate(fractions):
        axes[1].text(index, value, f"{value:.1f}%", ha="center", va="bottom")
    save_figure(fig, path)


def plot_charge_total(rows: Sequence[dict[str, Any]], path: Path) -> None:
    charges = np.asarray([row["charge_pe"] for row in rows], dtype=float)
    triggered = charges[charges > 0]
    upper = max(10.0, float(np.quantile(charges, 0.995)))
    linear_edges = np.linspace(-0.5, upper + 0.5, 70)
    log_edges = positive_log_edges(triggered)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.7))
    axes[0].hist(charges, bins=linear_edges, color="#2563eb", alpha=0.75)
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Carga [PE]")
    axes[0].set_ylabel("Eventos")
    axes[0].set_title("Todos los secundarios (incluye Q=0)")
    axes[0].grid(axis="y")
    overflow = int(np.sum(charges > upper))
    axes[0].text(
        0.98,
        0.96,
        f"Q=0: {np.mean(charges == 0):.1%}\nFuera del rango: {overflow}",
        transform=axes[0].transAxes,
        ha="right",
        va="top",
    )
    axes[1].hist(triggered, bins=log_edges, histtype="step", linewidth=2, color="#dc2626")
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Carga [PE]")
    axes[1].set_ylabel("Eventos")
    axes[1].set_title("Eventos con señal")
    axes[1].grid(which="both")
    for probability, linestyle in ((0.5, "--"), (0.9, ":"), (0.99, "-.")):
        if triggered.size:
            value = float(np.quantile(triggered, probability))
            axes[1].axvline(value, color="#475569", linestyle=linestyle, linewidth=1.2)
            axes[1].text(value, 0.96, f"P{int(100*probability)}={value:.0f}", rotation=90,
                         transform=axes[1].get_xaxis_transform(), va="top", ha="right")
    save_figure(fig, path)


def plot_charge_components(rows: Sequence[dict[str, Any]], path: Path) -> None:
    components = present_components(rows)
    values = [
        np.asarray([row["charge_pe"] for row in component_rows(rows, c) if row["charge_pe"] > 0])
        for c in components
    ]
    edges = positive_log_edges([value for array in values for value in array])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.7))
    axes[0].hist(
        values,
        bins=edges,
        stacked=True,
        label=[COMPONENT_LABEL[c] for c in components],
        color=[COMPONENT_COLOR[c] for c in components],
        alpha=0.82,
    )
    axes[0].set_xscale("log")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Carga [PE]")
    axes[0].set_ylabel("Eventos")
    axes[0].set_title("Contribución aditiva")
    axes[0].grid(which="both")
    axes[0].legend()
    for component, array in zip(components, values):
        if array.size:
            axes[1].hist(
                array,
                bins=edges,
                density=True,
                histtype="step",
                linewidth=2,
                label=COMPONENT_LABEL[component],
                color=COMPONENT_COLOR[component],
            )
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Carga [PE]")
    axes[1].set_ylabel("Densidad condicionada a Q>0")
    axes[1].set_title("Forma de cada componente")
    axes[1].grid(which="both")
    axes[1].legend()
    save_figure(fig, path)


def plot_charge_species(rows: Sequence[dict[str, Any]], path: Path) -> None:
    counts = Counter(row["species"] for row in rows)
    species = [name for name, _ in counts.most_common(8)]
    all_positive = [row["charge_pe"] for row in rows if row["charge_pe"] > 0]
    edges = positive_log_edges(all_positive)
    fig, axis = plt.subplots(figsize=(9.5, 5.2))
    for index, name in enumerate(species):
        values = [row["charge_pe"] for row in rows if row["species"] == name and row["charge_pe"] > 0]
        if values:
            axis.hist(values, bins=edges, histtype="step", linewidth=1.8, label=f"{name} (N={counts[name]})")
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("Carga [PE]")
    axis.set_ylabel("Eventos")
    axis.set_title("Respuesta por especie secundaria")
    axis.grid(which="both")
    axis.legend(ncol=2)
    save_figure(fig, path)


def deterministic_subsample(rows: Sequence[dict[str, Any]], maximum: int = 5000) -> list[dict[str, Any]]:
    if len(rows) <= maximum:
        return list(rows)
    indices = np.linspace(0, len(rows) - 1, maximum, dtype=int)
    return [rows[index] for index in indices]


def plot_energy_charge(rows: Sequence[dict[str, Any]], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.7))
    for component in present_components(rows):
        selected = [
            row for row in component_rows(rows, component)
            if row["energy_deposit_MeV"] > 0 and row["charge_pe"] > 0
        ]
        selected = deterministic_subsample(selected)
        if selected:
            axes[0].scatter(
                [row["energy_deposit_MeV"] for row in selected],
                [row["charge_pe"] for row in selected],
                s=8,
                alpha=0.28,
                label=COMPONENT_LABEL[component],
                color=COMPONENT_COLOR[component],
            )
    axes[0].set_xscale("log")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Energía depositada [MeV]")
    axes[0].set_ylabel("Carga [PE]")
    axes[0].set_title("Conversión energía–luz")
    axes[0].grid(which="both")
    axes[0].legend()
    efficiencies: list[list[float]] = []
    labels: list[str] = []
    for component in present_components(rows):
        values = [
            row["charge_pe"] / row["energy_deposit_MeV"]
            for row in component_rows(rows, component)
            if row["energy_deposit_MeV"] > 0 and row["charge_pe"] > 0
        ]
        if values:
            efficiencies.append(values)
            labels.append(COMPONENT_LABEL[component])
    axes[1].boxplot(efficiencies, labels=labels, showfliers=False)
    axes[1].set_yscale("log")
    axes[1].set_ylabel("Respuesta aparente [PE/MeV]")
    axes[1].set_title("Dispersión evento a evento")
    axes[1].grid(axis="y")
    save_figure(fig, path)


def threshold_values(rows: Sequence[dict[str, Any]]) -> np.ndarray:
    charges = np.asarray([row["charge_pe"] for row in rows], dtype=float)
    positive = charges[charges > 0]
    upper = max(1.0, float(np.quantile(positive, 0.999))) if positive.size else 1.0
    return np.unique(np.rint(np.geomspace(1, upper, 50)).astype(int))


def plot_threshold_scan(rows: Sequence[dict[str, Any]], duration: float, path: Path) -> None:
    thresholds = threshold_values(rows)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.7))
    selections = [("total", list(rows))] + [
        (component, component_rows(rows, component)) for component in present_components(rows)
    ]
    for name, selected in selections:
        charges = np.asarray([row["charge_pe"] for row in selected], dtype=float)
        rates = np.asarray([np.sum(charges >= threshold) / duration for threshold in thresholds])
        efficiencies = rates * duration / len(selected)
        color = "#0f172a" if name == "total" else COMPONENT_COLOR[name]
        label = "Total" if name == "total" else COMPONENT_LABEL[name]
        axes[0].plot(thresholds, rates, label=label, color=color, linewidth=2)
        axes[1].plot(thresholds, efficiencies, label=label, color=color, linewidth=2)
    for axis in axes:
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlabel("Umbral [PE]")
        axis.grid(which="both")
    axes[0].set_ylabel("Tasa de la campaña [s⁻¹]")
    axes[0].set_title("Tasa frente al umbral")
    axes[1].set_ylabel("Fracción de secundarios")
    axes[1].set_title("Eficiencia frente al umbral")
    axes[0].legend()
    save_figure(fig, path)


def flattened_times(
    rows: Sequence[dict[str, Any]], relative: bool, gated: bool = True
) -> np.ndarray:
    arrays: list[np.ndarray] = []
    for row in rows:
        field = "_times_gate_ns" if gated else "_times_ns"
        times = np.asarray(row[field], dtype=float)
        if times.size:
            arrays.append(times - np.min(times) if relative else times)
    return np.concatenate(arrays) if arrays else np.asarray([], dtype=float)


def empirical_survival(values: np.ndarray, maximum_points: int = 2500) -> tuple[np.ndarray, np.ndarray]:
    if values.size == 0:
        return np.asarray([]), np.asarray([])
    ordered = np.sort(values)
    if ordered.size > maximum_points:
        indices = np.linspace(0, ordered.size - 1, maximum_points, dtype=int)
        ordered = ordered[indices]
        survival = 1.0 - indices / values.size
    else:
        survival = 1.0 - np.arange(ordered.size) / ordered.size
    return ordered, survival


def plot_timing_total(
    rows: Sequence[dict[str, Any]], acquisition_window_ns: float, path: Path
) -> None:
    absolute = flattened_times(rows, relative=False, gated=True)
    absolute_raw = flattened_times(rows, relative=False, gated=False)
    relative = flattened_times(rows, relative=True)
    triggered_events = max(1, sum(row["charge_pe"] > 0 for row in rows))
    absolute_upper = max(10.0, float(np.quantile(absolute, 0.999))) if absolute.size else 10.0
    relative_upper = max(100.0, float(np.quantile(relative, 0.999))) if relative.size else 100.0
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.6))
    axes[0].hist(absolute, bins=np.linspace(0, absolute_upper, 140), color="#2563eb", alpha=0.8)
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Tiempo desde la inyección [ns]")
    axes[0].set_ylabel("Fotoelectrones")
    axes[0].set_title("Llegada absoluta")
    axes[0].grid(axis="y")
    prompt_upper = min(100.0, relative_upper)
    counts, edges = np.histogram(relative, bins=np.arange(0, prompt_upper + 1.0, 1.0))
    centers = (edges[:-1] + edges[1:]) / 2
    axes[1].step(centers, counts / triggered_events, where="mid", color="#dc2626", linewidth=1.8)
    axes[1].set_xlabel("Tiempo desde el primer PE [ns]")
    axes[1].set_ylabel("PE por evento disparado y ns")
    axes[1].set_title("Perfil prompt medio")
    axes[1].grid()
    x, survival = empirical_survival(relative)
    axes[2].plot(x, survival, color="#7c3aed", linewidth=2)
    axes[2].set_yscale("log")
    axes[2].set_xlim(0, relative_upper)
    axes[2].set_xlabel("Tiempo desde el primer PE [ns]")
    axes[2].set_ylabel("Fracción de PE más tardíos")
    axes[2].set_title("Cola temporal (supervivencia)")
    axes[2].grid(which="both")
    positive_raw = absolute_raw[absolute_raw > 0]
    if positive_raw.size:
        delay_edges = np.geomspace(
            max(0.1, float(np.min(positive_raw))),
            max(1.0, float(np.max(positive_raw)) * 1.001),
            100,
        )
        axes[3].hist(positive_raw, bins=delay_edges, histtype="step", linewidth=1.8, color="#059669")
    axes[3].axvline(
        acquisition_window_ns,
        color="#dc2626",
        linestyle="--",
        linewidth=1.5,
        label=f"Ventana: {acquisition_window_ns:g} ns",
    )
    axes[3].set_xscale("log")
    axes[3].set_yscale("log")
    axes[3].set_xlabel("Tiempo desde la inyección [ns]")
    axes[3].set_ylabel("Fotoelectrones")
    axes[3].set_title("Señales retardadas brutas")
    axes[3].grid(which="both")
    axes[3].legend()
    save_figure(fig, path)


def plot_timing_components(rows: Sequence[dict[str, Any]], path: Path) -> None:
    components = present_components(rows)
    all_relative = flattened_times(rows, relative=True)
    upper = max(100.0, float(np.quantile(all_relative, 0.999))) if all_relative.size else 100.0
    edges = np.linspace(0, upper, 130)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.7))
    for component in components:
        selected = component_rows(rows, component)
        times = flattened_times(selected, relative=True)
        triggered = max(1, sum(row["charge_pe"] > 0 for row in selected))
        counts, _ = np.histogram(times, bins=edges)
        centers = (edges[:-1] + edges[1:]) / 2
        axes[0].step(
            centers,
            counts / triggered,
            where="mid",
            linewidth=1.8,
            color=COMPONENT_COLOR[component],
            label=COMPONENT_LABEL[component],
        )
        x, survival = empirical_survival(times)
        axes[1].plot(x, survival, linewidth=1.8, color=COMPONENT_COLOR[component], label=COMPONENT_LABEL[component])
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Tiempo desde el primer PE [ns]")
    axes[0].set_ylabel("PE por evento disparado / bin")
    axes[0].set_title("Perfil temporal por componente")
    axes[1].set_yscale("log")
    axes[1].set_xlim(0, upper)
    axes[1].set_xlabel("Tiempo desde el primer PE [ns]")
    axes[1].set_ylabel("Fracción de PE más tardíos")
    axes[1].set_title("Comparación de colas")
    for axis in axes:
        axis.grid(which="both")
        axis.legend()
    save_figure(fig, path)


def plot_pulse_features(rows: Sequence[dict[str, Any]], path: Path) -> None:
    components = present_components(rows)
    widths: list[list[float]] = []
    late: list[list[float]] = []
    labels: list[str] = []
    for component in components:
        selected = component_rows(rows, component)
        component_widths = [row["time_width_10_90_ns"] for row in selected if row["time_width_10_90_ns"] is not None]
        component_late = [row["late_fraction_50ns"] for row in selected if row["late_fraction_50ns"] is not None]
        if component_widths:
            widths.append(component_widths)
            late.append(component_late)
            labels.append(COMPONENT_LABEL[component])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.7))
    axes[0].boxplot(widths, labels=labels, showfliers=False)
    axes[0].set_yscale("log")
    axes[0].set_ylabel("t90 − t10 [ns]")
    axes[0].set_title("Anchura temporal por evento")
    axes[1].boxplot(late, labels=labels, showfliers=False)
    axes[1].set_ylabel("Fracción de PE después de 50 ns")
    axes[1].set_ylim(-0.02, 1.02)
    axes[1].set_title("Contenido tardío")
    for axis in axes:
        axis.grid(axis="y")
    save_figure(fig, path)


def plot_shower_response(shower_rows: Sequence[dict[str, Any]], path: Path) -> None:
    charges = np.asarray([row["charge_total_pe"] for row in shower_rows], dtype=float)
    positive = charges[charges > 0]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.7))
    axes[0].hist(positive, bins=positive_log_edges(positive), histtype="step", linewidth=2, color="#7c3aed")
    axes[0].set_xscale("log")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Carga sumada por cascada [PE]")
    axes[0].set_ylabel("Cascadas")
    axes[0].set_title("Respuesta agregada de la EAS")
    axes[0].grid(which="both")
    multiplicity = np.asarray([row["multiplicity"] for row in shower_rows], dtype=float)
    signal = charges > 0
    if np.any(signal):
        axes[1].hexbin(
            multiplicity[signal],
            charges[signal],
            gridsize=45,
            mincnt=1,
            xscale="log",
            yscale="log",
            cmap="viridis",
        )
    axes[1].set_xlabel("Multiplicidad de secundarios")
    axes[1].set_ylabel("Carga sumada [PE]")
    axes[1].set_title("Multiplicidad frente a señal")
    axes[1].grid(which="both")
    save_figure(fig, path)


def plot_balance(rows: Sequence[dict[str, Any]], path: Path) -> None:
    components = present_components(rows)
    metrics = {
        "Inyectadas": [len(component_rows(rows, c)) for c in components],
        "Disparadas": [sum(row["charge_pe"] > 0 for row in component_rows(rows, c)) for c in components],
        "Carga": [sum(row["charge_pe"] for row in component_rows(rows, c)) for c in components],
        "Energía depositada": [sum(row["energy_deposit_MeV"] for row in component_rows(rows, c)) for c in components],
    }
    fig, axis = plt.subplots(figsize=(10, 5))
    x = np.arange(len(metrics))
    bottom = np.zeros(len(metrics))
    for component_index, component in enumerate(components):
        values = []
        for series in metrics.values():
            total = sum(series) or 1
            values.append(100 * series[component_index] / total)
        axis.bar(x, values, bottom=bottom, label=COMPONENT_LABEL[component], color=COMPONENT_COLOR[component])
        bottom += values
    axis.set_xticks(x, list(metrics))
    axis.set_ylabel("Composición [%]")
    axis.set_ylim(0, 100)
    axis.set_title("Cómo cambia la composición al atravesar la cadena de detección")
    axis.grid(axis="y")
    axis.legend(ncol=len(components), loc="upper center")
    save_figure(fig, path)


def plot_momentum(rows: Sequence[dict[str, Any]], duration: float, path: Path) -> None:
    momenta = np.asarray([row["momentum_GeV_c"] for row in rows], dtype=float)
    positive = momenta[momenta > 0]
    lower = max(1e-3, float(np.quantile(positive, 0.001)))
    upper = float(np.quantile(positive, 0.999))
    edges = np.geomspace(lower, upper, 45)
    centers = np.sqrt(edges[:-1] * edges[1:])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.7))
    for component in present_components(rows):
        selected = component_rows(rows, component)
        momentum = np.asarray([row["momentum_GeV_c"] for row in selected])
        triggered = np.asarray([row["charge_pe"] > 0 for row in selected])
        incident, _ = np.histogram(momentum, bins=edges)
        detected, _ = np.histogram(momentum[triggered], bins=edges)
        axes[0].step(centers, incident / duration, where="mid", linewidth=1.8,
                     color=COMPONENT_COLOR[component], label=COMPONENT_LABEL[component])
        efficiency = np.divide(
            detected,
            incident,
            out=np.full_like(detected, np.nan, dtype=float),
            where=incident > 0,
        )
        valid = incident >= 20
        valid_centers = centers[valid]
        valid_efficiency = efficiency[valid]
        lower: list[float] = []
        upper_ci: list[float] = []
        for successes, trials in zip(detected[valid], incident[valid]):
            low, high = wilson_interval(int(successes), int(trials))
            lower.append(float(low))
            upper_ci.append(float(high))
        axes[1].plot(
            valid_centers,
            valid_efficiency,
            marker=".",
            linewidth=1.4,
            color=COMPONENT_COLOR[component],
            label=COMPONENT_LABEL[component],
        )
        axes[1].fill_between(
            valid_centers,
            lower,
            upper_ci,
            color=COMPONENT_COLOR[component],
            alpha=0.12,
            linewidth=0,
        )
    for axis in axes:
        axis.set_xscale("log")
        axis.set_xlabel("Momento [GeV/c]")
        axis.grid(which="both")
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Secundarios por segundo y bin")
    axes[0].set_title("Espectro incidente")
    axes[1].set_ylabel("P(Q ≥ 1 PE)")
    axes[1].set_ylim(0, 1.02)
    axes[1].set_title("Aceptancia efectiva (N≥20 por bin, IC 95 %)")
    axes[0].legend()
    save_figure(fig, path)


def make_plots(
    rows: Sequence[dict[str, Any]],
    shower_rows: Sequence[dict[str, Any]],
    duration: float,
    acquisition_window_ns: float,
    plot_dir: Path,
) -> list[str]:
    return plot_all_scientific(
        rows=rows,
        showers=shower_rows,
        duration=duration,
        acquisition_window=acquisition_window_ns,
        plot_dir=plot_dir,
    )


def scenario_comparison(all_rows: Sequence[dict[str, Any]], scenario_rows: dict[str, list[dict[str, Any]]], duration: float) -> dict[str, Any]:
    comparison: dict[str, Any] = {}
    for scenario, rows in scenario_rows.items():
        comparison[scenario] = group_summary(rows, duration)
        if scenario != "all":
            reference = component_rows(all_rows, scenario)
            comparison[scenario]["reference_from_all"] = group_summary(reference, duration)
            comparison[scenario]["note"] = (
                "La ejecución separada usa una semilla independiente; se compara "
                "estadísticamente, no evento a evento."
            )
    return comparison


def make_report(
    summary: dict[str, Any],
    preparation: dict[str, Any],
    plots: Sequence[str],
    analysis_dir: Path,
    plot_dir: Path,
) -> None:
    total = summary["total"]
    complete = bool(preparation["source"].get("complete_exposure", preparation["source"].get("complete_30s_exposure", False)))
    duration = float(summary["duration_s"])
    title = f"WCD exposure of {duration:g} s" if complete else "Partial WCD pipeline test"
    lines = [
        f"# Informe: {title}",
        "",
        "## Alcance",
        "",
        f"- Partículas inyectadas: **{total['injected']:,}**.",
        f"- Duración nominal: **{summary['duration_s']:.1f} s**.",
        f"- Disco de inyección: radio **{summary['injection_radius_m']:.2f} m**; "
        f"flujo incidente asociado: **{summary['incident_flux_on_injection_disk_m-2_s-1']:.2f} m⁻² s⁻¹**.",
        f"- Exposición completa de {duration:g} s: **{'sí' if complete else 'no'}**.",
        "- Modo: `eFast`; salida de carga en fotoelectrones.",
        f"- Ventana instrumental aplicada: **{summary['acquisition_window_ns']:g} ns** desde la inyección.",
        "",
        "## Respuesta instrumental",
        "",
        f"- Eventos con Q ≥ 1 PE: **{total['triggered_q_ge_1pe']:,}** "
        f"({100*total['trigger_efficiency']:.2f} %).",
        f"- Tasa de la campaña para Q ≥ 1 PE: **{total['trigger_rate_Hz']:.3f} ± "
        f"{total['trigger_rate_poisson_error_Hz']:.3f} s⁻¹** (error de conteo).",
        f"- Carga total: **{total['charge_sum_pe']:,} PE**.",
        f"- Carga bruta de MEIGA antes de la ventana: **{total['charge_raw_meiga_sum_pe']:,} PE**; "
        f"fuera de ventana: **{total['pe_outside_acquisition_window']:,} PE**.",
        f"- Energía total depositada en el agua: **{total['energy_deposit_sum_MeV']/1000:.2f} GeV**.",
        f"- Mediana de Q condicionada a Q>0: **{total['charge_quantiles_triggered_pe']['p50'] or 0:.1f} PE**.",
        f"- Percentil 99 de Q condicionada a Q>0: **{total['charge_quantiles_triggered_pe']['p99'] or 0:.1f} PE**.",
        "",
        "## Componentes de la cascada",
        "",
        "| Componente | Inyectadas | Disparadas | Eficiencia | Aporte de carga | Aporte de energía |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for component in COMPONENTS:
        if component not in summary["components"]:
            continue
        value = summary["components"][component]
        lines.append(
            f"| {COMPONENT_LABEL[component]} | {value['injected']:,} | "
            f"{value['triggered_q_ge_1pe']:,} | {100*value['trigger_efficiency']:.2f} % | "
            f"{100*value['fraction_of_total_charge']:.2f} % | "
            f"{100*value['fraction_of_total_deposited_energy']:.2f} % |"
        )
    lines.extend(
        [
            "",
            "## Figuras",
            "",
        ]
    )
    for filename in plots:
        label = filename.removesuffix(".png").replace("_", " ").lstrip("0123456789 ")
        lines.append(f"- [{label}](../plots/{filename})")
    if preparation.get("visualization"):
        lines.extend(
            [
                "",
                "## Visualización tridimensional",
                "",
                "- [WCD geometry in VRML](../run/visualization.wrl).",
                "- Se genera una sola escena por corrida desde el escenario `all`; no incluye "
                "trayectorias de las 34 mil partículas.",
            ]
        )
    lines.extend(
        [
            "",
            "## Límites de interpretación",
            "",
            "- `Charge` es número de fotoelectrones; todavía no incluye ganancia, ruido, "
            "afterpulses, ADC, saturación ni trigger electrónico.",
            "- La escala muónica de esta muestra no es por sí sola una calibración VEM: "
            "incluye trayectorias inclinadas y eventos que rozan el tanque.",
            "- El formato de 12 columnas no conserva el tiempo de llegada de cada secundario. "
            "No se pueden inferir pile-up, tiempo muerto o coincidencias absolutas dentro de los 30 s.",
            "- `eCircle` vuelve a muestrear la posición sobre el disco; las tasas dependen de "
            "esa área y de la aceptancia simulada.",
            "- Las cascadas se reconstruyen por `shower_id` y sus cargas se suman, pero sin una "
            "marca temporal no se construye una forma de pulso colectiva de la EAS.",
            "",
            "## Archivos reproducibles",
            "",
            "- `events.csv.gz`: observable por secundario.",
            "- `showers.csv`: respuesta sumada por cascada primaria.",
            "- `summary.json`: estadísticas y contribuciones.",
            "- `manifest.json`: hashes, versiones, configuración y ejecutable.",
        ]
    )
    if preparation.get("visualization"):
        lines.append("- `visualization.wrl`: single VRML2 geometry scene for the run.")
    (analysis_dir / "analysis_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze_campaign(args: argparse.Namespace) -> None:
    run_dir = args.run_dir.resolve()
    analysis_dir = args.analysis_dir.resolve()
    plot_dir = args.plot_dir.resolve()
    analysis_dir.mkdir(parents=True, exist_ok=True)
    plot_dir.mkdir(parents=True, exist_ok=True)
    preparation = read_json(run_dir / "preparation.json")

    scenario_rows: dict[str, list[dict[str, Any]]] = {}
    for scenario_dir in sorted((run_dir / "scenarios").iterdir()):
        if scenario_dir.is_dir() and (
            (scenario_dir / "output.json.gz").is_file()
            or (scenario_dir / "output.json").is_file()
        ):
            scenario_rows[scenario_dir.name] = extract_scenario(
                scenario_dir, scenario_dir.name, args.acquisition_window
            )
    if "all" not in scenario_rows:
        raise ValueError("No existe una salida completa en scenarios/all")
    full_rows = scenario_rows["all"]
    shower_rows = build_shower_rows(full_rows)
    summary = summarize_full(full_rows, args.duration, args.injection_radius)
    summary["acquisition_window_ns"] = args.acquisition_window
    summary["separate_scenarios"] = scenario_comparison(
        full_rows, scenario_rows, args.duration
    )
    summary["interpretation"] = {
        "charge_unit": "photoelectrons",
        "energy_deposit_unit": "MeV",
        "time_unit": "ns",
        "trigger_definition": "Charge >= 1 PE",
        "acquisition_window_ns": args.acquisition_window,
        "absolute_electronics_modeled": False,
        "per_secondary_arrival_timestamps_available": False,
        "vem_calibration": False,
    }

    all_rows = [row for rows in scenario_rows.values() for row in rows]
    write_event_table(all_rows, analysis_dir / "events.csv.gz")
    write_shower_table(shower_rows, analysis_dir / "showers.csv")
    write_json(analysis_dir / "summary.json", summary)
    plots = make_plots(
        full_rows,
        shower_rows,
        args.duration,
        args.acquisition_window,
        plot_dir,
    )

    tracked_files: list[Path] = [run_dir / "preparation.json"]
    if preparation.get("visualization"):
        visualization = run_dir / "visualization.wrl"
        if not visualization.is_file() or visualization.stat().st_size == 0:
            raise ValueError("Missing or empty visualization.wrl")
        tracked_files.append(visualization)
    for scenario_dir in sorted((run_dir / "scenarios").iterdir()):
        if not scenario_dir.is_dir():
            continue
        tracked_files.extend(
            path for path in (
                scenario_dir / "input.shw",
                scenario_dir / "DetectorList.xml",
                scenario_dir / "DetectorProperties.xml",
                scenario_dir / "config.json",
                scenario_dir / "output.json.gz",
                scenario_dir / "output.json",
                scenario_dir / "run.log",
            ) if path.is_file()
        )
    manifest = {
        "run_id": run_dir.name,
        "complete_exposure": preparation["source"].get("complete_exposure", preparation["source"].get("complete_30s_exposure", False)),
        "executable": args.executable,
        "executable_sha256": args.executable_sha256,
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "matplotlib": matplotlib.__version__,
        "files": {
            str(path.relative_to(run_dir)): {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in tracked_files
        },
    }
    write_json(analysis_dir / "manifest.json", manifest)
    make_report(summary, preparation, plots, analysis_dir, plot_dir)
    print(
        json.dumps(
            {
                "run_id": run_dir.name,
                "events": len(full_rows),
                "showers": len(shower_rows),
                "plots": [str(plot_dir / filename) for filename in plots],
                "summary": str(analysis_dir / "summary.json"),
                "report": str(analysis_dir / "analysis_report.md"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _optional_number(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    return float(value)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def load_normalized_events(
    event_table: Path,
    output_file: Path | None,
    acquisition_window_ns: float,
) -> list[dict[str, Any]]:
    """Load either legacy event-table schema into the canonical WCD schema."""
    source_rows = _read_csv_rows(event_table)
    output_events: dict[int, dict[str, Any]] = {}
    if output_file is not None:
        output_events = dict(sorted_event_items(read_json(output_file)))

    normalized: list[dict[str, Any]] = []
    for index, source in enumerate(source_rows):
        event_id = int(source.get("event_id") or source.get("event") or index)
        corsika_id = int(source.get("corsika_id") or 0)
        pdg_id, default_species, default_component = particle_info(corsika_id)
        event = output_events.get(event_id, {})
        detector = event.get("Detector_0", {})
        device = detector.get("OptDevice_0", {})
        times = [float(value) for value in device.get("PETimeDistribution", [])]
        gated_times = [value for value in times if 0.0 <= value <= acquisition_window_ns]
        timing = event_timing(gated_times) if times else {
            "n_times": int(float(source.get("n_times") or source.get("charge_pe") or 0)),
            "time_first_ns": _optional_number(source.get("time_first_ns") or source.get("first_pe_time_ns")),
            "time_mean_ns": _optional_number(source.get("time_mean_ns")),
            "time_rms_ns": _optional_number(source.get("time_rms_ns")),
            "time_t10_ns": _optional_number(source.get("time_t10_ns")),
            "time_t50_ns": _optional_number(source.get("time_t50_ns")),
            "time_t90_ns": _optional_number(source.get("time_t90_ns")),
            "time_width_10_90_ns": _optional_number(source.get("time_width_10_90_ns") or source.get("pulse_width_10_90_ns")),
            "late_fraction_50ns": _optional_number(source.get("late_fraction_50ns")),
        }
        table_charge = int(float(source.get("charge_pe") or 0))
        raw_charge = int(float(source.get("charge_raw_meiga_pe") or source.get("charge_raw_pe") or table_charge))
        charge = len(gated_times) if times else table_charge
        row: dict[str, Any] = {
            "scenario": source.get("scenario") or "all",
            "event_id": event_id,
            "source_index": int(float(source.get("source_index") or event_id)),
            "shower_id": int(float(source.get("shower_id") or 0)),
            "corsika_id": corsika_id,
            "pdg_id": int(float(source.get("pdg_id") or pdg_id)),
            "species": source.get("species") or default_species,
            "component": source.get("component") or default_component,
            "momentum_GeV_c": float(source.get("momentum_GeV_c") or source.get("secondary_momentum_GeV_c") or 0.0),
            "zenith_deg": float(source.get("zenith_deg") or source.get("secondary_zenith_deg") or 0.0),
            "primary_energy_GeV": float(source.get("primary_energy_GeV") or 0.0),
            "primary_theta_deg": float(source.get("primary_theta_deg") or 0.0),
            "primary_phi_deg": float(source.get("primary_phi_deg") or 0.0),
            "energy_deposit_MeV": float(source.get("energy_deposit_MeV") or detector.get("EnergyDeposit", 0.0)),
            "charge_pe": charge,
            "charge_raw_meiga_pe": raw_charge,
            "pe_outside_acquisition_window": int(float(source.get("pe_outside_acquisition_window") or source.get("pe_outside_window") or (raw_charge - charge))),
            "time_max_raw_ns": max(times) if times else _optional_number(source.get("time_max_raw_ns")),
            **timing,
            "_times_ns": times,
            "_times_gate_ns": gated_times,
        }
        normalized.append(row)
    if output_events and len(output_events) != len(normalized):
        raise ValueError(
            f"Event-table/output mismatch: {len(normalized)} rows versus {len(output_events)} output events"
        )
    return normalized


def make_generic_report(
    summary: dict[str, Any], plot_names: Sequence[str], analysis_dir: Path, plot_dir: Path
) -> None:
    total = summary["total"]
    lines = [
        "# WCD analysis report",
        "",
        "## Exposure and detector response",
        "",
        f"- Exposure: **{summary['duration_s']:g} s**.",
        f"- Injected particles: **{total['injected']:,}**.",
        f"- Events with Q >= 1 PE: **{total['triggered_q_ge_1pe']:,}** ({100 * total['trigger_efficiency']:.3f}%).",
        f"- Trigger rate: **{total['trigger_rate_Hz']:.3f} +/- {total['trigger_rate_poisson_error_Hz']:.3f} s^-1**.",
        f"- Total charge: **{total['charge_sum_pe']:,} PE**.",
        f"- Deposited energy: **{total['energy_deposit_sum_MeV'] / 1000:.3f} GeV**.",
        "",
        "## Shower components",
        "",
        "| Component | Injected | Triggered | Efficiency | Charge fraction | Deposited-energy fraction |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for component in COMPONENTS:
        if component not in summary["components"]:
            continue
        value = summary["components"][component]
        lines.append(
            f"| {COMPONENT_LABEL[component]} | {value['injected']:,} | {value['triggered_q_ge_1pe']:,} | "
            f"{100 * value['trigger_efficiency']:.3f}% | {100 * value['fraction_of_total_charge']:.3f}% | "
            f"{100 * value['fraction_of_total_deposited_energy']:.3f}% |"
        )
    lines.extend(["", "## Figures", ""])
    relative_plot_dir = Path(Path(plot_dir).name)
    for filename in plot_names:
        label = filename.removesuffix(".png").replace("_", " ").lstrip("0123456789 ")
        lines.append(f"- [{label}](../../plots/{relative_plot_dir.as_posix()}/{filename})")
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "- Charge is expressed in photoelectrons; PMT gain, electronics noise, ADC response, saturation, and an electronic trigger are not modeled.",
            "- The simulated campaign rate depends on the injection area and the chosen detector configuration.",
            "- The secondary-particle input does not preserve an absolute arrival timestamp, so pile-up and detector dead time cannot be inferred.",
        ]
    )
    (analysis_dir / "analysis_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def replot_results(args: argparse.Namespace) -> None:
    """Regenerate the same scientific figure set from a normalized event table."""
    analysis_dir = args.analysis_dir.resolve()
    plot_dir = args.plot_dir.resolve()
    analysis_dir.mkdir(parents=True, exist_ok=True)
    rows = load_normalized_events(
        args.event_table.resolve(),
        args.output_file.resolve() if args.output_file else None,
        args.acquisition_window,
    )
    showers = build_shower_rows(rows)
    summary = summarize_full(rows, args.duration, args.injection_radius)
    summary["acquisition_window_ns"] = args.acquisition_window
    write_event_table(rows, analysis_dir / "events.csv.gz")
    write_shower_table(showers, analysis_dir / "showers.csv")
    write_json(analysis_dir / "summary.json", summary)
    plots = make_plots(rows, showers, args.duration, args.acquisition_window, plot_dir)
    make_generic_report(summary, plots, analysis_dir, plot_dir)
    print(
        json.dumps(
            {
                "events": len(rows),
                "showers": len(showers),
                "analysis": str(analysis_dir),
                "plots": [str(plot_dir / filename) for filename in plots],
            },
            indent=2,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare", help="Crea escenarios autocontenidos")
    prepare.add_argument("--experiment", type=Path, required=True)
    prepare.add_argument("--run-dir", type=Path, required=True)
    prepare.add_argument("--scenarios", default="all")
    prepare.add_argument("--seed", type=int, default=2026072230)
    prepare.add_argument("--max-particles", type=int, default=0)
    prepare.set_defaults(function=prepare_campaign)

    analyze = subparsers.add_parser("analyze", help="Analiza salidas y genera figuras")
    analyze.add_argument("--run-dir", type=Path, required=True)
    analyze.add_argument("--analysis-dir", type=Path, required=True)
    analyze.add_argument("--plot-dir", type=Path, required=True)
    analyze.add_argument("--duration", type=float, default=30.0)
    analyze.add_argument("--injection-radius", type=float, default=1.5)
    analyze.add_argument("--acquisition-window", type=float, default=500.0)
    analyze.add_argument("--executable", default="unknown")
    analyze.add_argument("--executable-sha256", default="unknown")
    analyze.set_defaults(function=analyze_campaign)

    replot = subparsers.add_parser(
        "replot", help="Create the unified scientific plot set from an event table"
    )
    replot.add_argument("--event-table", type=Path, required=True)
    replot.add_argument("--output-file", type=Path)
    replot.add_argument("--analysis-dir", type=Path, required=True)
    replot.add_argument("--plot-dir", type=Path, required=True)
    replot.add_argument("--duration", type=float, required=True)
    replot.add_argument("--injection-radius", type=float, default=1.5)
    replot.add_argument("--acquisition-window", type=float, default=500.0)
    replot.set_defaults(function=replot_results)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "seed") and args.seed <= 0:
        parser.error("--seed debe ser mayor que cero")
    if hasattr(args, "max_particles") and args.max_particles < 0:
        parser.error("--max-particles no puede ser negativo")
    if hasattr(args, "duration") and args.duration <= 0:
        parser.error("--duration debe ser mayor que cero")
    if hasattr(args, "acquisition_window") and args.acquisition_window <= 0:
        parser.error("--acquisition-window debe ser mayor que cero")
    args.function(args)


if __name__ == "__main__":
    main()
