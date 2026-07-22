"""Publication-ready plots shared by every WCD campaign.

The plotting layer consumes a normalized event table.  It intentionally knows
nothing about whether the events came from a 30 s teaching run or a 5 min
project run, which keeps every campaign visually and statistically consistent.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Callable, Sequence

import matplotlib.pyplot as plt
import numpy as np


COMPONENTS = ("electromagnetic", "muonic", "hadronic", "unknown")
COMPONENT_LABEL = {
    "electromagnetic": "Electromagnetic",
    "muonic": "Muonic",
    "hadronic": "Hadronic",
    "unknown": "Unknown",
}
COMPONENT_STYLE = {
    "electromagnetic": {"color": "#0072B2", "linestyle": "-", "marker": "o"},
    "muonic": {"color": "#D55E00", "linestyle": "--", "marker": "s"},
    "hadronic": {"color": "#009E73", "linestyle": "-.", "marker": "^"},
    "unknown": {"color": "#6B7280", "linestyle": ":", "marker": "D"},
}
TOTAL_STYLE = {"color": "#111827", "linestyle": "-", "marker": "o"}


def setup_style() -> None:
    """Apply one journal-like, color-blind-safe style to every figure."""
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#252525",
            "axes.linewidth": 0.8,
            "axes.labelcolor": "#111111",
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "axes.titleweight": "semibold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.family": "serif",
            "font.serif": ["DejaVu Serif", "STIXGeneral", "Times New Roman"],
            "font.size": 8.5,
            "mathtext.fontset": "stix",
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.major.size": 3.5,
            "ytick.major.size": 3.5,
            "xtick.minor.size": 2.0,
            "ytick.minor.size": 2.0,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7.5,
            "legend.frameon": False,
            "grid.color": "#D1D5DB",
            "grid.linewidth": 0.45,
            "grid.alpha": 0.55,
            "lines.linewidth": 1.45,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def _finish_axis(axis: plt.Axes, grid: str = "y") -> None:
    axis.minorticks_on()
    if grid:
        axis.grid(True, axis=grid, which="major")
    axis.tick_params(which="both", top=False, right=False)


def save_figure(fig: plt.Figure, png_path: Path) -> None:
    """Write a 300 dpi PNG and a vector PDF with the same basename."""
    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(pad=0.7)
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(png_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def _component_rows(rows: Sequence[dict[str, Any]], component: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["component"] == component]


def _present_components(rows: Sequence[dict[str, Any]]) -> list[str]:
    found = {str(row["component"]) for row in rows}
    return [component for component in COMPONENTS if component in found]


def _positive_log_edges(values: Sequence[float], bins: int = 52) -> np.ndarray:
    positive = np.asarray([value for value in values if np.isfinite(value) and value > 0], dtype=float)
    if positive.size == 0:
        return np.geomspace(0.5, 1.5, bins)
    low = max(1e-4, float(np.quantile(positive, 0.001)) * 0.85)
    high = max(low * 1.2, float(np.quantile(positive, 0.999)) * 1.15)
    return np.geomspace(low, high, bins)


def _subsample(rows: Sequence[dict[str, Any]], maximum: int = 6000) -> list[dict[str, Any]]:
    if len(rows) <= maximum:
        return list(rows)
    indices = np.linspace(0, len(rows) - 1, maximum, dtype=int)
    return [rows[index] for index in indices]


def _wilson(successes: np.ndarray, trials: np.ndarray, z: float = 1.96) -> tuple[np.ndarray, np.ndarray]:
    trials = trials.astype(float)
    proportion = np.divide(successes, trials, out=np.zeros_like(trials), where=trials > 0)
    denominator = 1.0 + z**2 / trials
    center = (proportion + z**2 / (2.0 * trials)) / denominator
    half = z * np.sqrt(proportion * (1.0 - proportion) / trials + z**2 / (4.0 * trials**2)) / denominator
    return center - half, center + half


def plot_flux_composition(rows: Sequence[dict[str, Any]], duration: float, path: Path) -> None:
    components = _present_components(rows)
    injected = np.asarray([len(_component_rows(rows, c)) / duration for c in components])
    triggered = np.asarray([sum(row["charge_pe"] > 0 for row in _component_rows(rows, c)) / duration for c in components])
    charge = np.asarray([sum(row["charge_pe"] for row in _component_rows(rows, c)) for c in components])
    x = np.arange(len(components))
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    width = 0.36
    axes[0].bar(x - width / 2, injected, width, label="Injected", color="#9CA3AF", edgecolor="white")
    axes[0].bar(x + width / 2, triggered, width, label=r"$Q\geq1$ PE", color=[COMPONENT_STYLE[c]["color"] for c in components], edgecolor="white")
    axes[0].set_xticks(x, [COMPONENT_LABEL[c] for c in components])
    axes[0].set_yscale("log")
    axes[0].set_ylabel(r"Campaign rate [s$^{-1}$]")
    axes[0].set_title("Incident flux and detector response")
    axes[0].legend()
    _finish_axis(axes[0])
    fractions = 100.0 * charge / max(1.0, float(np.sum(charge)))
    axes[1].bar(x, fractions, color=[COMPONENT_STYLE[c]["color"] for c in components], edgecolor="white")
    axes[1].set_xticks(x, [COMPONENT_LABEL[c] for c in components])
    axes[1].set_ylabel("Fraction of total charge [%]")
    axes[1].set_title("Contribution to the charge spectrum")
    for index, value in enumerate(fractions):
        axes[1].text(index, value, f"{value:.1f}%", ha="center", va="bottom", fontsize=7)
    _finish_axis(axes[1])
    save_figure(fig, path)


def plot_total_charge(rows: Sequence[dict[str, Any]], path: Path) -> None:
    charge = np.asarray([row["charge_pe"] for row in rows], dtype=float)
    positive = charge[charge > 0]
    upper = max(10.0, float(np.quantile(charge, 0.995)))
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    axes[0].hist(charge, bins=np.linspace(-0.5, upper + 0.5, 65), color="#4C78A8", alpha=0.85)
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Charge [PE]")
    axes[0].set_ylabel("Events")
    axes[0].set_title(r"All injected particles ($Q=0$ included)")
    axes[0].text(0.97, 0.95, f"Zero signal: {np.mean(charge == 0):.1%}", transform=axes[0].transAxes, ha="right", va="top")
    _finish_axis(axes[0])
    axes[1].hist(positive, bins=_positive_log_edges(positive), histtype="step", color="#B2182B", linewidth=1.6)
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Charge [PE]")
    axes[1].set_ylabel("Triggered events")
    axes[1].set_title(r"Triggered sample ($Q>0$)")
    for probability, linestyle in ((0.5, "--"), (0.9, ":"), (0.99, "-.")):
        if positive.size:
            value = float(np.quantile(positive, probability))
            axes[1].axvline(value, color="#555555", linestyle=linestyle, linewidth=0.9)
            axes[1].text(value, 0.97, f"P{int(100 * probability)}={value:.0f}", rotation=90, transform=axes[1].get_xaxis_transform(), va="top", ha="right", fontsize=6.7)
    _finish_axis(axes[1], "both")
    save_figure(fig, path)


def _plot_component_distribution(
    rows: Sequence[dict[str, Any]], field: str, xlabel: str, path: Path, facets: bool
) -> None:
    components = _present_components(rows)
    values = {
        component: np.asarray([float(row[field]) for row in _component_rows(rows, component) if float(row[field]) > 0])
        for component in components
    }
    edges = _positive_log_edges([value for array in values.values() for value in array])
    if facets:
        fig, axes = plt.subplots(1, len(components), figsize=(2.45 * len(components), 2.7), sharex=True, sharey=True, squeeze=False)
        for axis, component in zip(axes[0], components):
            axis.hist(values[component], bins=edges, histtype="stepfilled", alpha=0.22, color=COMPONENT_STYLE[component]["color"])
            axis.hist(values[component], bins=edges, histtype="step", color=COMPONENT_STYLE[component]["color"])
            axis.set_title(COMPONENT_LABEL[component])
            axis.set_xscale("log")
            axis.set_yscale("log")
            axis.set_xlabel(xlabel)
            _finish_axis(axis, "both")
        axes[0, 0].set_ylabel("Events")
    else:
        fig, axis = plt.subplots(figsize=(3.65, 3.0))
        for component in components:
            style = COMPONENT_STYLE[component]
            axis.hist(values[component], bins=edges, histtype="step", linewidth=1.55, linestyle=style["linestyle"], color=style["color"], label=COMPONENT_LABEL[component])
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlabel(xlabel)
        axis.set_ylabel("Events")
        axis.legend()
        _finish_axis(axis, "both")
    save_figure(fig, path)


def plot_charge_species(rows: Sequence[dict[str, Any]], path: Path) -> None:
    counts = Counter(str(row["species"]) for row in rows)
    species = [name for name, _ in counts.most_common(8)]
    positive = [float(row["charge_pe"]) for row in rows if row["charge_pe"] > 0]
    edges = _positive_log_edges(positive)
    fig, axis = plt.subplots(figsize=(5.0, 3.2))
    colors = plt.get_cmap("tab10").colors
    for index, name in enumerate(species):
        values = [row["charge_pe"] for row in rows if str(row["species"]) == name and row["charge_pe"] > 0]
        if values:
            axis.hist(values, bins=edges, histtype="step", color=colors[index % len(colors)], label=f"{name} ($N={counts[name]:,}$)")
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("Charge [PE]")
    axis.set_ylabel("Events")
    axis.set_title("Detector response by secondary-particle species")
    axis.legend(ncol=2)
    _finish_axis(axis, "both")
    save_figure(fig, path)


def plot_energy_charge(rows: Sequence[dict[str, Any]], path: Path, facets: bool) -> None:
    components = _present_components(rows)
    if facets:
        fig, axes = plt.subplots(1, len(components), figsize=(2.55 * len(components), 2.75), sharex=True, sharey=True, squeeze=False)
        axis_list = list(axes[0])
    else:
        fig, axis = plt.subplots(figsize=(3.75, 3.15))
        axis_list = [axis] * len(components)
    for axis, component in zip(axis_list, components):
        selected = _subsample([row for row in _component_rows(rows, component) if row["energy_deposit_MeV"] > 0 and row["charge_pe"] > 0])
        style = COMPONENT_STYLE[component]
        if selected:
            axis.scatter([row["energy_deposit_MeV"] for row in selected], [row["charge_pe"] for row in selected], s=5.5, alpha=0.20 if not facets else 0.28, color=style["color"], marker=style["marker"], linewidths=0, label=COMPONENT_LABEL[component])
        if facets:
            axis.set_title(COMPONENT_LABEL[component])
    for axis in dict.fromkeys(axis_list):
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlabel("Deposited energy [MeV]")
        _finish_axis(axis, "both")
    axis_list[0].set_ylabel("Charge [PE]")
    if not facets:
        axis_list[0].set_title("Energy deposition and photoelectron yield")
        axis_list[0].legend(markerscale=2)
    save_figure(fig, path)


def _thresholds(rows: Sequence[dict[str, Any]]) -> np.ndarray:
    positive = np.asarray([row["charge_pe"] for row in rows if row["charge_pe"] > 0], dtype=float)
    upper = max(1.0, float(np.quantile(positive, 0.999))) if positive.size else 1.0
    return np.unique(np.rint(np.geomspace(1, upper, 45)).astype(int))


def plot_threshold_response(rows: Sequence[dict[str, Any]], duration: float, path: Path, facets: bool) -> None:
    thresholds = _thresholds(rows)
    components = _present_components(rows)
    if facets:
        fig, axes = plt.subplots(1, len(components), figsize=(2.55 * len(components), 2.75), sharex=True, sharey=True, squeeze=False)
        selections = zip(axes[0], components)
    else:
        fig, axis = plt.subplots(figsize=(3.75, 3.15))
        selections = [(axis, "total"), *[(axis, component) for component in components]]
    for axis, name in selections:
        selected = list(rows) if name == "total" else _component_rows(rows, name)
        charge = np.asarray([row["charge_pe"] for row in selected], dtype=float)
        rate = np.asarray([np.sum(charge >= threshold) / duration for threshold in thresholds])
        style = TOTAL_STYLE if name == "total" else COMPONENT_STYLE[name]
        label = "All components" if name == "total" else COMPONENT_LABEL[name]
        axis.plot(thresholds, rate, color=style["color"], linestyle=style["linestyle"], label=label)
        if facets:
            axis.set_title(label)
    axes_to_format = list(axes[0]) if facets else [axis]
    for item in axes_to_format:
        item.set_xscale("log")
        item.set_yscale("log")
        item.set_xlabel("Charge threshold [PE]")
        _finish_axis(item, "both")
    axes_to_format[0].set_ylabel(r"Trigger rate [s$^{-1}$]")
    if not facets:
        axis.set_title("Rate above threshold")
        axis.legend()
    save_figure(fig, path)


def _relative_times(rows: Sequence[dict[str, Any]]) -> np.ndarray:
    arrays: list[np.ndarray] = []
    for row in rows:
        values = np.asarray(row.get("_times_gate_ns", []), dtype=float)
        if values.size:
            arrays.append(values - np.min(values))
    return np.concatenate(arrays) if arrays else np.asarray([], dtype=float)


def _survival(values: np.ndarray, maximum: int = 2500) -> tuple[np.ndarray, np.ndarray]:
    ordered = np.sort(values)
    if ordered.size == 0:
        return ordered, ordered
    indices = np.arange(ordered.size)
    if ordered.size > maximum:
        indices = np.linspace(0, ordered.size - 1, maximum, dtype=int)
        ordered = ordered[indices]
    return ordered, 1.0 - indices / max(1, values.size)


def plot_timing_total(rows: Sequence[dict[str, Any]], acquisition_window: float, path: Path) -> None:
    relative = _relative_times(rows)
    raw_arrays = [np.asarray(row.get("_times_ns", []), dtype=float) for row in rows if row.get("_times_ns")]
    raw = np.concatenate(raw_arrays) if raw_arrays else np.asarray([], dtype=float)
    triggered = max(1, sum(row["charge_pe"] > 0 for row in rows))
    upper = max(100.0, float(np.quantile(relative, 0.999))) if relative.size else 100.0
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.8))
    edges = np.linspace(0, min(upper, 250.0), 126)
    counts, edges = np.histogram(relative, bins=edges)
    axes[0].step((edges[:-1] + edges[1:]) / 2, counts / triggered, where="mid", color="#0072B2")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Time after first PE [ns]")
    axes[0].set_ylabel("PE per triggered event / bin")
    axes[0].set_title("Mean pulse profile")
    x, survival = _survival(relative)
    axes[1].plot(x, survival, color="#CC79A7")
    axes[1].set_yscale("log")
    axes[1].set_xlim(0, upper)
    axes[1].set_xlabel("Time after first PE [ns]")
    axes[1].set_ylabel("PE survival fraction")
    axes[1].set_title("Late-light tail")
    if raw.size:
        axes[2].hist(raw[raw > 0], bins=_positive_log_edges(raw[raw > 0], 70), histtype="step", color="#009E73")
    axes[2].axvline(acquisition_window, color="#D55E00", linestyle="--", label=f"Gate: {acquisition_window:g} ns")
    axes[2].set_xscale("log")
    axes[2].set_yscale("log")
    axes[2].set_xlabel("Time after injection [ns]")
    axes[2].set_ylabel("Photoelectrons")
    axes[2].set_title("Acquisition gate")
    axes[2].legend()
    for axis in axes:
        _finish_axis(axis, "both")
    save_figure(fig, path)


def plot_timing_components(rows: Sequence[dict[str, Any]], path: Path, facets: bool) -> None:
    components = _present_components(rows)
    all_times = _relative_times(rows)
    upper = max(100.0, float(np.quantile(all_times, 0.999))) if all_times.size else 100.0
    edges = np.linspace(0, min(upper, 300.0), 121)
    if facets:
        fig, axes = plt.subplots(1, len(components), figsize=(2.55 * len(components), 2.75), sharex=True, sharey=True, squeeze=False)
        targets = list(axes[0])
    else:
        fig, axis = plt.subplots(figsize=(3.75, 3.15))
        targets = [axis] * len(components)
    for axis, component in zip(targets, components):
        selected = _component_rows(rows, component)
        values = _relative_times(selected)
        triggered = max(1, sum(row["charge_pe"] > 0 for row in selected))
        counts, _ = np.histogram(values, bins=edges)
        style = COMPONENT_STYLE[component]
        axis.step((edges[:-1] + edges[1:]) / 2, counts / triggered, where="mid", color=style["color"], linestyle=style["linestyle"], label=COMPONENT_LABEL[component])
        if facets:
            axis.set_title(COMPONENT_LABEL[component])
    for axis in dict.fromkeys(targets):
        axis.set_yscale("log")
        axis.set_xlabel("Time after first PE [ns]")
        _finish_axis(axis, "both")
    targets[0].set_ylabel("PE per triggered event / bin")
    if not facets:
        targets[0].set_title("Pulse-time distribution by shower component")
        targets[0].legend()
    save_figure(fig, path)


def plot_pulse_metrics(rows: Sequence[dict[str, Any]], path: Path) -> None:
    components = _present_components(rows)
    widths = [[row["time_width_10_90_ns"] for row in _component_rows(rows, c) if row.get("time_width_10_90_ns") is not None] for c in components]
    late = [[row["late_fraction_50ns"] for row in _component_rows(rows, c) if row.get("late_fraction_50ns") is not None] for c in components]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    for axis, values, ylabel, title in (
        (axes[0], widths, r"$t_{90}-t_{10}$ [ns]", "Pulse width"),
        (axes[1], late, "Fraction of PE after 50 ns", "Late-light content"),
    ):
        boxes = axis.boxplot(values, labels=[COMPONENT_LABEL[c] for c in components], showfliers=False, patch_artist=True, widths=0.55)
        for patch, component in zip(boxes["boxes"], components):
            patch.set_facecolor(COMPONENT_STYLE[component]["color"])
            patch.set_alpha(0.25)
        axis.set_ylabel(ylabel)
        axis.set_title(title)
        _finish_axis(axis)
    axes[0].set_yscale("log")
    axes[1].set_ylim(-0.02, 1.02)
    save_figure(fig, path)


def plot_shower_response(showers: Sequence[dict[str, Any]], path: Path) -> None:
    charge = np.asarray([row["charge_total_pe"] for row in showers], dtype=float)
    multiplicity = np.asarray([row["multiplicity"] for row in showers], dtype=float)
    signal = charge > 0
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    axes[0].hist(charge[signal], bins=_positive_log_edges(charge[signal]), histtype="step", color="#7B3294")
    axes[0].set_xscale("log")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Summed shower charge [PE]")
    axes[0].set_ylabel("Air showers")
    axes[0].set_title("Shower-integrated response")
    if np.any(signal):
        axes[1].hexbin(multiplicity[signal], charge[signal], gridsize=38, mincnt=1, xscale="log", yscale="log", cmap="cividis")
    axes[1].set_xlabel("Secondary-particle multiplicity")
    axes[1].set_ylabel("Summed shower charge [PE]")
    axes[1].set_title("Multiplicity and detector signal")
    for axis in axes:
        _finish_axis(axis, "both")
    save_figure(fig, path)


def plot_detection_chain(rows: Sequence[dict[str, Any]], path: Path) -> None:
    components = _present_components(rows)
    metrics = {
        "Injected": [len(_component_rows(rows, c)) for c in components],
        "Triggered": [sum(row["charge_pe"] > 0 for row in _component_rows(rows, c)) for c in components],
        "Charge": [sum(row["charge_pe"] for row in _component_rows(rows, c)) for c in components],
        "Deposited energy": [sum(row["energy_deposit_MeV"] for row in _component_rows(rows, c)) for c in components],
    }
    fig, axis = plt.subplots(figsize=(4.8, 3.1))
    x = np.arange(len(metrics))
    bottom = np.zeros(len(metrics))
    for index, component in enumerate(components):
        values = np.asarray([100.0 * series[index] / max(1.0, sum(series)) for series in metrics.values()])
        axis.bar(x, values, bottom=bottom, label=COMPONENT_LABEL[component], color=COMPONENT_STYLE[component]["color"], edgecolor="white")
        bottom += values
    axis.set_xticks(x, list(metrics))
    axis.set_ylabel("Component fraction [%]")
    axis.set_ylim(0, 100)
    axis.set_title("Composition through the detection chain")
    axis.legend(ncol=len(components), loc="lower center", bbox_to_anchor=(0.5, 1.01))
    _finish_axis(axis)
    save_figure(fig, path)


def _response_bins(rows: Sequence[dict[str, Any]], field: str, logarithmic: bool) -> np.ndarray:
    values = np.asarray([float(row[field]) for row in rows], dtype=float)
    values = values[np.isfinite(values)]
    if logarithmic:
        values = values[values > 0]
        return np.geomspace(max(1e-5, float(np.quantile(values, 0.001))), float(np.quantile(values, 0.999)), 38)
    return np.linspace(float(np.quantile(values, 0.001)), float(np.quantile(values, 0.999)), 35)


def plot_binned_response(
    rows: Sequence[dict[str, Any]], field: str, xlabel: str, path: Path, facets: bool, logarithmic: bool
) -> None:
    components = _present_components(rows)
    edges = _response_bins(rows, field, logarithmic)
    centers = np.sqrt(edges[:-1] * edges[1:]) if logarithmic else (edges[:-1] + edges[1:]) / 2
    if facets:
        fig, axes = plt.subplots(1, len(components), figsize=(2.55 * len(components), 2.75), sharex=True, sharey=True, squeeze=False)
        targets = list(axes[0])
    else:
        fig, axis = plt.subplots(figsize=(3.75, 3.15))
        targets = [axis] * len(components)
    for axis, component in zip(targets, components):
        selected = _component_rows(rows, component)
        x = np.asarray([float(row[field]) for row in selected])
        detected_mask = np.asarray([row["charge_pe"] > 0 for row in selected])
        incident, _ = np.histogram(x, bins=edges)
        detected, _ = np.histogram(x[detected_mask], bins=edges)
        valid = incident >= 20
        efficiency = np.divide(detected, incident, out=np.full_like(detected, np.nan, dtype=float), where=incident > 0)
        low, high = _wilson(detected[valid].astype(float), incident[valid].astype(float))
        style = COMPONENT_STYLE[component]
        axis.plot(centers[valid], efficiency[valid], color=style["color"], linestyle=style["linestyle"], marker=style["marker"], markersize=3, label=COMPONENT_LABEL[component])
        axis.fill_between(centers[valid], low, high, color=style["color"], alpha=0.12, linewidth=0)
        if facets:
            axis.set_title(COMPONENT_LABEL[component])
    for axis in dict.fromkeys(targets):
        if logarithmic:
            axis.set_xscale("log")
        axis.set_ylim(0, 1.02)
        axis.set_xlabel(xlabel)
        _finish_axis(axis)
    targets[0].set_ylabel(r"Detection efficiency $P(Q\geq1\ \mathrm{PE})$")
    if not facets:
        targets[0].legend()
    save_figure(fig, path)


def plot_all(
    rows: Sequence[dict[str, Any]],
    showers: Sequence[dict[str, Any]],
    duration: float,
    acquisition_window: float,
    plot_dir: Path,
) -> list[str]:
    """Generate the complete, identical figure set for any WCD exposure."""
    setup_style()
    jobs: list[tuple[str, Callable[[Path], None]]] = [
        ("01_flux_composition.png", lambda p: plot_flux_composition(rows, duration, p)),
        ("02_total_charge_distribution.png", lambda p: plot_total_charge(rows, p)),
        ("03_charge_by_component_combined.png", lambda p: _plot_component_distribution(rows, "charge_pe", "Charge [PE]", p, False)),
        ("04_charge_by_component_facets.png", lambda p: _plot_component_distribution(rows, "charge_pe", "Charge [PE]", p, True)),
        ("05_charge_by_species.png", lambda p: plot_charge_species(rows, p)),
        ("06_deposited_energy_by_component_combined.png", lambda p: _plot_component_distribution(rows, "energy_deposit_MeV", "Deposited energy [MeV]", p, False)),
        ("07_deposited_energy_by_component_facets.png", lambda p: _plot_component_distribution(rows, "energy_deposit_MeV", "Deposited energy [MeV]", p, True)),
        ("08_energy_vs_charge_combined.png", lambda p: plot_energy_charge(rows, p, False)),
        ("09_energy_vs_charge_facets.png", lambda p: plot_energy_charge(rows, p, True)),
        ("10_threshold_response_combined.png", lambda p: plot_threshold_response(rows, duration, p, False)),
        ("11_threshold_response_facets.png", lambda p: plot_threshold_response(rows, duration, p, True)),
        ("12_time_distribution_total.png", lambda p: plot_timing_total(rows, acquisition_window, p)),
        ("13_time_distribution_by_component_combined.png", lambda p: plot_timing_components(rows, p, False)),
        ("14_time_distribution_by_component_facets.png", lambda p: plot_timing_components(rows, p, True)),
        ("15_pulse_shape_metrics.png", lambda p: plot_pulse_metrics(rows, p)),
        ("16_air_shower_response.png", lambda p: plot_shower_response(showers, p)),
        ("17_detection_chain_composition.png", lambda p: plot_detection_chain(rows, p)),
        ("18_momentum_response_combined.png", lambda p: plot_binned_response(rows, "momentum_GeV_c", "Secondary momentum [GeV/c]", p, False, True)),
        ("19_momentum_response_facets.png", lambda p: plot_binned_response(rows, "momentum_GeV_c", "Secondary momentum [GeV/c]", p, True, True)),
        ("20_primary_energy_response_combined.png", lambda p: plot_binned_response(rows, "primary_energy_GeV", "Primary energy [GeV]", p, False, True)),
        ("21_primary_energy_response_facets.png", lambda p: plot_binned_response(rows, "primary_energy_GeV", "Primary energy [GeV]", p, True, True)),
        ("22_primary_zenith_response_combined.png", lambda p: plot_binned_response(rows, "primary_theta_deg", "Primary zenith angle [deg]", p, False, False)),
        ("23_primary_zenith_response_facets.png", lambda p: plot_binned_response(rows, "primary_theta_deg", "Primary zenith angle [deg]", p, True, False)),
    ]
    plot_dir.mkdir(parents=True, exist_ok=True)
    for filename, function in jobs:
        function(plot_dir / filename)
    return [filename for filename, _ in jobs]
