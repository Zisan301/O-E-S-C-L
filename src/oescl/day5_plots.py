from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_constellations(tx, raw, linear, memory, path: Path) -> Path:
    fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    data = [("TX", tx), ("Raw RX", raw), ("Linear EQ", linear), ("Memory neural", memory)]
    for ax, (title, z) in zip(axes.ravel(), data):
        s = z[: min(len(z), 2500)]
        ax.scatter(s.real, s.imag, s=4, alpha=0.45)
        ax.set_title(title)
        ax.set_xlabel("I")
        ax.set_ylabel("Q")
        ax.grid(True, linewidth=0.3, alpha=0.5)
        ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_metric_vs_power(df: pd.DataFrame, metric: str, ylabel: str, title: str, path: Path, logy: bool = False) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for name, group in df.groupby("display_name"):
        g = group.sort_values("launch_power_dbm")
        y = g[f"{metric}_mean"].to_numpy(float)
        if logy:
            y = np.maximum(y, 1e-9)
        ax.errorbar(
            g["launch_power_dbm"],
            y,
            yerr=g.get(f"{metric}_ci95", None),
            marker="o",
            capsize=3,
            linewidth=1.5,
            label=name,
        )
    if logy:
        ax.set_yscale("log")
    ax.set_xlabel("Launch power (dBm/channel)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="both", linewidth=0.3, alpha=0.5)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_pcs_sweep(df: pd.DataFrame, metric: str, ylabel: str, title: str, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for name, group in df.groupby("display_name"):
        g = group.sort_values("pcs_nu")
        ax.errorbar(
            g["pcs_nu"],
            g[f"{metric}_mean"],
            yerr=g.get(f"{metric}_ci95", None),
            marker="o",
            capsize=3,
            linewidth=1.5,
            label=name,
        )
    ax.set_xlabel("PCS shaping coefficient, nu")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, linewidth=0.3, alpha=0.5)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_best_tradeoff(best_df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    for _, row in best_df.iterrows():
        ax.scatter(row["rate_tbps_mean"], row["gmi_mean"], s=80)
        ax.annotate(row["display_name"], (row["rate_tbps_mean"], row["gmi_mean"]), textcoords="offset points", xytext=(6, 6), fontsize=8)
    ax.set_xlabel("Estimated rate (Tb/s/channel)")
    ax.set_ylabel("Bit-metric GMI (bits/symbol)")
    ax.set_title("Day-5 best operating-point trade-off")
    ax.grid(True, linewidth=0.3, alpha=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path
