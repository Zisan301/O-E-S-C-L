from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def constellation_plot(tx, rx_raw, rx_lin, rx_neural, path: Path) -> Path:
    datasets = [
        ("TX", tx),
        ("Raw RX", rx_raw),
        ("Linear EQ", rx_lin),
        ("Neural", rx_neural),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    for ax, (title, z) in zip(axes.ravel(), datasets):
        sample = z[: min(len(z), 2500)]
        ax.scatter(sample.real, sample.imag, s=4, alpha=0.45)
        ax.set_title(title)
        ax.set_xlabel("I")
        ax.set_ylabel("Q")
        ax.grid(True, linewidth=0.3, alpha=0.5)
        ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def sanity_bar(df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(df))
    ax.bar(x, df["ber"])
    ax.set_xticks(x)
    ax.set_xticklabels(df["test"], rotation=20, ha="right")
    ax.set_yscale("log")
    ax.set_ylabel("BER, log scale")
    ax.set_title("Day-4 calibration sanity tests")
    ax.grid(True, which="both", linewidth=0.3, alpha=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def regime_plot(df: pd.DataFrame, metric: str, ylabel: str, title: str, path: Path, logy: bool = False) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    for name, group in df.groupby("display_name"):
        g = group.sort_values("launch_power_dbm")
        vals = g[f"{metric}_mean"].to_numpy(dtype=float)
        if logy:
            vals = np.maximum(vals, 1e-8)
        ax.errorbar(
            g["launch_power_dbm"],
            vals,
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


def best_tradeoff(df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    for _, row in df.iterrows():
        ax.scatter(row["rate_tbps_mean"], row["gmi_mean"], s=70)
        ax.annotate(row["display_name"], (row["rate_tbps_mean"], row["gmi_mean"]), textcoords="offset points", xytext=(7, 7), fontsize=8)
    ax.set_xlabel("Estimated rate (Tb/s/channel)")
    ax.set_ylabel("Bit-metric GMI (bits/symbol)")
    ax.set_title("Calibrated Day-4 best operating-point trade-off")
    ax.grid(True, linewidth=0.3, alpha=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path
