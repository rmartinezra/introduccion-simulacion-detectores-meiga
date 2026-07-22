#!/usr/bin/env python3
"""Generate reproducible tables and publication-ready WCD optical plots."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import statistics
from pathlib import Path
from typing import Any, Iterable

import matplotlib.pyplot as plt


COURSE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS = COURSE_ROOT / "results"


def read_json(path: Path) -> dict[str, Any]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def iter_detector_rows(document: dict[str, Any], mode: str) -> Iterable[dict[str, Any]]:
    for event_name, event in document.get("Output", {}).items():
        if not event_name.startswith("Event_"):
            continue
        for detector_name, detector in event.items():
            if not detector_name.startswith("Detector_"):
                continue
            energy = float(detector.get("EnergyDeposit", 0.0))
            devices = [
                (name, value)
                for name, value in detector.items()
                if name.startswith("OptDevice_") and isinstance(value, dict)
            ]
            if not devices:
                yield {
                    "mode": mode,
                    "event": event_name,
                    "detector": detector_name,
                    "device": "",
                    "energy_MeV": energy,
                    "charge_pe": 0,
                    "times_ns": [],
                }
                continue
            for device_name, device in devices:
                yield {
                    "mode": mode,
                    "event": event_name,
                    "detector": detector_name,
                    "device": device_name,
                    "energy_MeV": energy,
                    "charge_pe": int(device.get("Charge", 0)),
                    "times_ns": [
                        float(value)
                        for value in device.get("PETimeDistribution", [])
                    ],
                }


def mean_or_zero(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def standard_error(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values) / math.sqrt(len(values))


def write_tables(rows: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    analysis_dir = output_dir / "analysis" / "wcd" / "optical-validation"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    csv_path = analysis_dir / "events.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "mode",
                "event",
                "detector",
                "device",
                "energy_MeV",
                "charge_pe",
                "n_times",
                "time_min_ns",
                "time_mean_ns",
                "time_max_ns",
            ],
        )
        writer.writeheader()
        for row in rows:
            times = row["times_ns"]
            writer.writerow(
                {
                    **{key: row[key] for key in writer.fieldnames[:6]},
                    "n_times": len(times),
                    "time_min_ns": min(times) if times else "",
                    "time_mean_ns": mean_or_zero(times) if times else "",
                    "time_max_ns": max(times) if times else "",
                }
            )

    summary: dict[str, Any] = {"nota": (
        "La comparación incluida es una prueba de integración. Para validar "
        "eFast frente a eFull se requieren muchos eventos."
    )}
    for mode in sorted({row["mode"] for row in rows}):
        selected = [row for row in rows if row["mode"] == mode]
        energies = [float(row["energy_MeV"]) for row in selected]
        charges = [float(row["charge_pe"]) for row in selected]
        times = [time for row in selected for time in row["times_ns"]]
        summary[mode] = {
            "events": len(selected),
            "energy_mean_MeV": mean_or_zero(energies),
            "energy_standard_error_MeV": standard_error(energies),
            "charge_mean_pe": mean_or_zero(charges),
            "charge_standard_error_pe": standard_error(charges),
            "photoelectron_times": len(times),
            "time_min_ns": min(times) if times else None,
            "time_mean_ns": mean_or_zero(times) if times else None,
            "time_max_ns": max(times) if times else None,
        }

    with (analysis_dir / "summary.json").open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return summary


def setup_plot() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#252525",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "semibold",
            "font.family": "serif",
            "font.serif": ["DejaVu Serif", "STIXGeneral", "Times New Roman"],
            "mathtext.fontset": "stix",
            "grid.color": "#d1d5db",
            "grid.alpha": 0.55,
            "font.size": 8.5,
            "legend.frameon": False,
            "pdf.fonttype": 42,
        }
    )


def save_plot(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def plot_event_response(rows: list[dict[str, Any]], plot_dir: Path) -> None:
    modes = [mode for mode in ("eFull", "eFast") if any(r["mode"] == mode for r in rows)]
    energies = [mean_or_zero([r["energy_MeV"] for r in rows if r["mode"] == mode]) for mode in modes]
    charges = [mean_or_zero([r["charge_pe"] for r in rows if r["mode"] == mode]) for mode in modes]
    colors = ["#2563eb", "#f59e0b"][: len(modes)]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    axes[0].bar(modes, energies, color=colors, width=0.6)
    axes[0].set_ylabel("Deposited energy [MeV]")
    axes[0].set_title("Energy deposition in water")
    axes[1].bar(modes, charges, color=colors, width=0.6)
    axes[1].set_ylabel("Charge [PE]")
    axes[1].set_title("PMT response")
    for axis, values in zip(axes, (energies, charges)):
        axis.grid(axis="y")
        for index, value in enumerate(values):
            axis.text(index, value, f"{value:.1f}", ha="center", va="bottom")
    fig.suptitle("WCD: 1 GeV/c vertical muon (integration test)", fontweight="semibold")
    fig.text(0.5, 0.01, "One event per mode; not a statistical comparison.", ha="center", color="#9A3412")
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    save_plot(fig, plot_dir / "wcd_event_response.png")


def plot_pe_times(rows: list[dict[str, Any]], plot_dir: Path) -> None:
    fig, axis = plt.subplots(figsize=(9, 5))
    colors = {"eFull": "#2563eb", "eFast": "#f59e0b"}
    all_times = [time for row in rows for time in row["times_ns"]]
    upper = max(all_times) if all_times else 1.0
    bins = max(25, min(80, int(math.sqrt(max(1, len(all_times)))) * 2))
    for mode in ("eFull", "eFast"):
        times = [time for row in rows if row["mode"] == mode for time in row["times_ns"]]
        if times:
            axis.hist(
                times,
                bins=bins,
                range=(0, upper),
                histtype="step",
                linewidth=2.0,
                density=True,
                color=colors[mode],
                label=f"{mode} ({len(times)} PE)",
            )
    axis.set_xlabel("Photoelectron arrival time [ns]")
    axis.set_ylabel("Normalized density")
    axis.set_title("Photoelectron time distribution")
    axis.grid()
    axis.legend()
    fig.tight_layout()
    save_plot(fig, plot_dir / "wcd_photoelectron_times.png")


def plot_water_optics(plot_dir: Path) -> None:
    energy_ev = [
        2.08, 2.16, 2.19, 2.23, 2.27, 2.32, 2.36, 2.41, 2.46, 2.50,
        2.56, 2.61, 2.67, 2.72, 2.79, 2.85, 2.92, 2.99, 3.06, 3.14,
        3.22, 3.31, 3.40, 3.49, 3.59, 3.70, 3.81, 3.94, 4.07, 4.20,
    ]
    absorption_m = [
        9.2, 13.3, 18.0, 20.3, 22.6, 25.8, 28.4, 30.2, 40.3, 56.0,
        73.5, 81.8, 92.3, 92.3, 99.3, 99.3, 100.0, 94.1, 88.9, 84.2,
        75.4, 65.5, 48.0, 38.0, 31.1, 25.7, 21.2, 17.1, 13.7, 10.2,
    ]
    rayleigh_m = [
        824.085, 704.531, 665.251, 616.967, 572.906, 523.114,
        487.050, 446.141, 409.347, 382.549, 346.238, 319.139,
        289.938, 268.048, 240.663, 219.843, 198.231, 179.126,
        162.191, 145.127, 130.165, 115.475, 102.714, 91.588,
        80.853, 70.709, 62.021, 53.308, 45.979, 39.784,
    ]
    refractive_index = [
        1.3331390, 1.3338383, 1.3341040, 1.3344615, 1.3348230,
        1.3352809, 1.3356522, 1.3361230, 1.3366017, 1.3369905,
        1.3375838, 1.3380881, 1.3387053, 1.3392301, 1.3399815,
        1.3406416, 1.3414311, 1.3422422, 1.3430756, 1.3440565,
        1.3450688, 1.3462465, 1.3474672, 1.3487325, 1.3501931,
        1.3518693, 1.3536220, 1.3557974, 1.3580925, 1.3605150,
    ]
    wavelength_nm = [1239.841984 / energy for energy in energy_ev]
    ordered = sorted(zip(wavelength_nm, absorption_m, rayleigh_m, refractive_index))
    wavelength_nm, absorption_m, rayleigh_m, refractive_index = map(list, zip(*ordered))

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    axes[0].plot(wavelength_nm, absorption_m, color="#0072B2", linewidth=1.6, label="Absorption")
    axes[0].plot(wavelength_nm, rayleigh_m, color="#7c3aed", linewidth=2.2, label="Rayleigh")
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Mean free path [m]")
    axes[0].set_title("Optical transport in water")
    axes[0].legend()
    axes[0].grid(which="both")
    axes[1].plot(wavelength_nm, refractive_index, color="#059669", linewidth=2.2)
    axes[1].set_xlabel("Wavelength [nm]")
    axes[1].set_ylabel("Refractive index")
    axes[1].set_title("IAPWS R9-97 dispersion at 20 °C")
    axes[1].grid()
    fig.tight_layout()
    save_plot(fig, plot_dir / "water_optical_properties.png")


def plot_pmt_efficiency(plot_dir: Path) -> None:
    wavelength_nm = [
        270, 280, 300, 320, 340, 360, 380, 400, 420, 440,
        460, 480, 500, 520, 540, 560, 580, 600, 625, 650,
    ]
    qe = [
        0.0000, 0.0688, 0.1233, 0.2063, 0.2300, 0.2371,
        0.2371, 0.2371, 0.2300, 0.2134, 0.1921, 0.1755,
        0.1518, 0.1138, 0.0688, 0.0451, 0.0308, 0.0200,
        0.0100, 0.0000,
    ]
    collection_efficiency = 0.70
    pde = [value * collection_efficiency for value in qe]

    fig, axis = plt.subplots(figsize=(9, 5))
    axis.plot(wavelength_nm, [100 * value for value in qe], linewidth=1.6, color="#0072B2", label="Photocathode QE")
    axis.plot(wavelength_nm, [100 * value for value in pde], linewidth=1.6, color="#D55E00", linestyle="--", label="QE × collection (70%)")
    axis.scatter([420], [23], color="#2563eb", zorder=3)
    axis.annotate("23% at 420 nm", (420, 23), xytext=(445, 24.5), arrowprops={"arrowstyle": "->", "color": "#475569"})
    axis.set_xlabel("Wavelength [nm]")
    axis.set_ylabel("Efficiency [%]")
    axis.set_title("Default XP1805 PMT spectral response")
    axis.set_ylim(0, 27)
    axis.grid()
    axis.legend()
    fig.tight_layout()
    save_plot(fig, plot_dir / "xp1805_pmt_efficiency.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", type=Path, required=True, help="Salida JSON de eFull")
    parser.add_argument("--fast", type=Path, required=True, help="Salida JSON de eFast")
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS, help="Directorio raíz de resultados")
    args = parser.parse_args()

    rows = [
        *iter_detector_rows(read_json(args.full), "eFull"),
        *iter_detector_rows(read_json(args.fast), "eFast"),
    ]
    output_dir = args.results.resolve()
    plot_dir = output_dir / "plots" / "wcd" / "optical-validation"
    plot_dir.mkdir(parents=True, exist_ok=True)
    setup_plot()
    summary = write_tables(rows, output_dir)
    plot_event_response(rows, plot_dir)
    plot_pe_times(rows, plot_dir)
    plot_water_optics(plot_dir)
    plot_pmt_efficiency(plot_dir)
    print(json.dumps({"plots": str(plot_dir), "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
