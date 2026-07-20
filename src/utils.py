"""
src/utils.py
============
Figure generation from saved experiment artifacts only. No random values are
created inside plotting functions.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from .artifacts import save_results

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def generate_figures(cfg: dict[str, Any], metrics: dict[str, Any], rx_clean: dict[str, Any], band_plan: dict[str, Any], tx: dict[str, Any]) -> None:
    raw_dir = Path(cfg.get("output", {}).get("figures_raw", "figures/raw"))
    final_dir = Path(cfg.get("output", {}).get("figures_final", "figures/final"))
    raw_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)
    _plot_architecture(raw_dir, final_dir)
    _plot_spectrum(band_plan, raw_dir, final_dir)
    if "diagnostics" in rx_clean:
        _plot_ssfm_diagnostics(rx_clean["diagnostics"], raw_dir, final_dir)
    _plot_gmi_per_channel(metrics, band_plan, raw_dir, final_dir)
    _plot_ber_per_channel(metrics, band_plan, raw_dir, final_dir)
    _plot_snr_gain(rx_clean, raw_dir, final_dir)
    _plot_pcs_distribution(tx, raw_dir, final_dir)


def generate_figures_from_artifacts(artifact_dir: str | Path, output_dir: str | Path | None = None) -> None:
    artifact_dir = Path(artifact_dir)
    output_dir = Path(output_dir or artifact_dir / "figures")
    raw_dir = output_dir / "raw"
    final_dir = output_dir / "final"
    raw_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)
    metrics = _load_json(artifact_dir / "metrics.json")
    per_channel = _load_csv(artifact_dir / "per_channel.csv")
    _plot_per_channel_artifact(per_channel, "gmi", "GMI (bits/symbol)", "artifact_gmi_per_channel", raw_dir, final_dir)
    _plot_per_channel_artifact(per_channel, "snr_dB", "SNR (dB)", "artifact_snr_per_channel", raw_dir, final_dir)
    _plot_per_channel_artifact(per_channel, "ber_pre_fec", "Pre-FEC BER", "artifact_ber_per_channel", raw_dir, final_dir, semilogy=True)
    if (artifact_dir / "monte_carlo.csv").exists():
        _plot_monte_carlo(_load_csv(artifact_dir / "monte_carlo.csv"), raw_dir, final_dir)
    _write_figure_provenance(final_dir, {"source_artifact_dir": str(artifact_dir), "metrics_keys": list(metrics.keys())})


def _save_fig(fig: plt.Figure, name: str, raw_dir: Path, final_dir: Path, provenance: dict[str, Any] | None = None) -> None:
    fig.savefig(raw_dir / f"{name}.svg", format="svg")
    fig.savefig(final_dir / f"{name}.pdf", format="pdf")
    fig.savefig(final_dir / f"{name}.png", format="png", dpi=300)
    plt.close(fig)
    if provenance is not None:
        (final_dir / f"{name}.provenance.json").write_text(json.dumps(provenance, indent=2, default=str), encoding="utf-8")


def _plot_architecture(raw_dir: Path, final_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis("off")
    blocks = ["PCS/QAM", "WDM Grid", "SSFM Fiber", "Amplifiers", "DSP", "Neural NLI", "Metrics"]
    x = np.arange(len(blocks))
    for i, label in enumerate(blocks):
        ax.text(i, 0.5, label, ha="center", va="center", bbox={"boxstyle": "round", "facecolor": "white", "edgecolor": "black"})
        if i < len(blocks) - 1:
            ax.annotate("", xy=(i + 0.78, 0.5), xytext=(i + 0.22, 0.5), arrowprops={"arrowstyle": "->"})
    ax.set_xlim(-0.5, len(blocks) - 0.5)
    ax.set_ylim(0, 1)
    ax.set_title("System pipeline")
    _save_fig(fig, "fig1_architecture", raw_dir, final_dir, {"data_source": "pipeline blocks"})


def _plot_spectrum(band_plan: dict[str, Any], raw_dir: Path, final_dir: Path) -> None:
    metadata = band_plan.get("channel_metadata", [])
    if not metadata:
        raise ValueError("band_plan channel_metadata is required for spectrum figure")
    freqs = np.array([float(m["frequency_THz"]) for m in metadata])
    powers = np.array([float(m.get("launch_power_dBm", 0.0)) for m in metadata])
    bands = np.array([m["band"] for m in metadata])
    fig, ax = plt.subplots(figsize=(10, 4))
    for band in dict.fromkeys(bands):
        mask = bands == band
        ax.plot(freqs[mask], powers[mask], marker=".", linestyle="none", label=str(band))
    ax.set_xlabel("Frequency (THz)")
    ax.set_ylabel("Launch power (dBm/channel)")
    ax.set_title("Configured O+E+S+C+L WDM grid")
    ax.grid(True, alpha=0.3)
    ax.legend(ncol=5)
    _save_fig(fig, "fig2_spectrum", raw_dir, final_dir, {"data_source": "band_plan.channel_metadata"})


def _plot_ssfm_diagnostics(diagnostics: dict[str, Any], raw_dir: Path, final_dir: Path) -> None:
    if "z_km" not in diagnostics or "mean_power_W" not in diagnostics:
        return
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(np.asarray(diagnostics["z_km"]), np.asarray(diagnostics["mean_power_W"]), marker="o")
    ax.set_xlabel("Distance (km)")
    ax.set_ylabel("Mean power (W)")
    ax.set_title("SSFM power evolution")
    ax.grid(True, alpha=0.3)
    _save_fig(fig, "fig3_ssfm_diagnostics", raw_dir, final_dir, {"data_source": "rx_clean.diagnostics"})


def _plot_gmi_per_channel(metrics: dict[str, Any], band_plan: dict[str, Any], raw_dir: Path, final_dir: Path) -> None:
    gmi = np.asarray(metrics["gmi_per_channel"], dtype=float)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(np.arange(1, gmi.size + 1), gmi, linewidth=1)
    ax.axhline(float(metrics["gmi_mean"]), linestyle="--", label=f"Mean {metrics['gmi_mean']:.3f}")
    _add_band_boundaries(ax, band_plan)
    ax.set_xlabel("Channel index")
    ax.set_ylabel("GMI (bits/symbol)")
    ax.set_title("Measured per-channel GMI")
    ax.grid(True, alpha=0.3)
    ax.legend()
    _save_fig(fig, "fig7_gmi_per_channel", raw_dir, final_dir, {"data_source": "metrics.gmi_per_channel"})


def _plot_ber_per_channel(metrics: dict[str, Any], band_plan: dict[str, Any], raw_dir: Path, final_dir: Path) -> None:
    ber = np.asarray(metrics["ber_pre_fec"], dtype=float)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.semilogy(np.arange(1, ber.size + 1), np.maximum(ber, 1e-12), linewidth=1)
    threshold = metrics.get("targets", {}).get("ber_target_pre_fec")
    if threshold is not None:
        ax.axhline(float(threshold), linestyle="--", label="FEC threshold")
    _add_band_boundaries(ax, band_plan)
    ax.set_xlabel("Channel index")
    ax.set_ylabel("Pre-FEC BER")
    ax.set_title("Measured BER per channel")
    ax.grid(True, alpha=0.3, which="both")
    ax.legend()
    _save_fig(fig, "fig4_ber_per_channel", raw_dir, final_dir, {"data_source": "metrics.ber_pre_fec"})


def _plot_snr_gain(rx_clean: dict[str, Any], raw_dir: Path, final_dir: Path) -> None:
    if "snr_gain_dB" not in rx_clean:
        return
    gain = np.asarray(rx_clean["snr_gain_dB"], dtype=float)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(np.arange(1, gain.size + 1), gain, linewidth=1)
    ax.set_xlabel("Channel index")
    ax.set_ylabel("SNR gain (dB)")
    ax.set_title("Measured neural NLI SNR gain")
    ax.grid(True, alpha=0.3)
    _save_fig(fig, "fig5_nli_snr_gain", raw_dir, final_dir, {"data_source": "rx_clean.snr_gain_dB"})


def _plot_pcs_distribution(tx: dict[str, Any], raw_dir: Path, final_dir: Path) -> None:
    const = np.asarray(tx["constellation"])
    probs = np.asarray(tx["probabilities"], dtype=float)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(const.real, const.imag, s=np.maximum(probs / probs.max(), 0.05) * 250)
    ax.set_xlabel("I")
    ax.set_ylabel("Q")
    ax.set_title(f"PCS distribution, H={tx.get('entropy_bits', float('nan')):.3f} bits")
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal", adjustable="box")
    _save_fig(fig, "fig6_pcs_constellation", raw_dir, final_dir, {"data_source": "tx.probabilities"})


def _add_band_boundaries(ax: plt.Axes, band_plan: dict[str, Any]) -> None:
    counts = [len(v) for v in band_plan.get("channels", {}).values()]
    labels = list(band_plan.get("channels", {}).keys())
    boundaries = np.cumsum([0] + counts)
    for i in range(1, len(boundaries)):
        ax.axvline(boundaries[i], linestyle=":", alpha=0.35)
        if i - 1 < len(labels):
            ax.text((boundaries[i - 1] + boundaries[i]) / 2, 0.98, labels[i - 1], transform=ax.get_xaxis_transform(), ha="center", va="top")


def _plot_per_channel_artifact(rows: list[dict[str, str]], column: str, ylabel: str, name: str, raw_dir: Path, final_dir: Path, semilogy: bool = False) -> None:
    x = np.array([int(float(row["index"])) + 1 for row in rows])
    y = np.array([float(row[column]) for row in rows])
    fig, ax = plt.subplots(figsize=(10, 4))
    if semilogy:
        ax.semilogy(x, np.maximum(y, 1e-12))
    else:
        ax.plot(x, y)
    ax.set_xlabel("Channel index")
    ax.set_ylabel(ylabel)
    ax.set_title(ylabel)
    ax.grid(True, alpha=0.3, which="both")
    _save_fig(fig, name, raw_dir, final_dir, {"data_source": f"per_channel.csv:{column}"})


def _plot_monte_carlo(rows: list[dict[str, str]], raw_dir: Path, final_dir: Path) -> None:
    run = np.array([int(float(r["run"])) for r in rows])
    gmi = np.array([float(r["gmi_mean"]) for r in rows])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(run, gmi, marker="o")
    ax.set_xlabel("Monte Carlo run")
    ax.set_ylabel("Mean GMI")
    ax.set_title("Monte Carlo GMI trace")
    ax.grid(True, alpha=0.3)
    _save_fig(fig, "fig10_monte_carlo_gmi", raw_dir, final_dir, {"data_source": "monte_carlo.csv"})


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_figure_provenance(final_dir: Path, payload: dict[str, Any]) -> None:
    (final_dir / "figure_provenance.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
