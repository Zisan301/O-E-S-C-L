from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_day6_pcs_metric(df: pd.DataFrame, metric: str, ylabel: str, title: str, path: Path, logy: bool = False) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for name, group in df.groupby("display_name"):
        g = group.sort_values("pcs_nu")
        y = g[f"{metric}_mean"].astype(float).to_numpy()
        if logy:
            y = np.maximum(y, 1e-10)
        ax.errorbar(
            g["pcs_nu"],
            y,
            yerr=g.get(f"{metric}_ci95", None),
            marker="o",
            capsize=3,
            linewidth=1.6,
            label=name,
        )
    if logy:
        ax.set_yscale("log")
    ax.set_xlabel("PCS shaping coefficient, nu")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="both", linewidth=0.3, alpha=0.55)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_day6_gain(gain_df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5.2))
    g = gain_df.sort_values("pcs_nu")
    ax.errorbar(
        g["pcs_nu"],
        g["gmi_gain_mean"],
        yerr=g["gmi_gain_ci95"],
        marker="o",
        capsize=3,
        linewidth=1.7,
        label="PCS raw - Uniform raw",
    )
    ax.axhline(0.0, linewidth=1.0)
    ax.set_xlabel("PCS shaping coefficient, nu")
    ax.set_ylabel("GMI gain (bits/symbol)")
    ax.set_title("Day-6 confirmed PCS gain over uniform signaling")
    ax.grid(True, linewidth=0.3, alpha=0.55)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_day6_constellation(tx, uniform, pcs, path: Path) -> Path:
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8))
    data = [("TX", tx), ("Uniform RX", uniform), ("Best PCS RX", pcs)]
    for ax, (title, z) in zip(axes, data):
        s = z[: min(len(z), 2500)]
        ax.scatter(s.real, s.imag, s=4, alpha=0.45)
        ax.set_title(title)
        ax.set_xlabel("I")
        ax.set_ylabel("Q")
        ax.grid(True, linewidth=0.3, alpha=0.55)
        ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path
