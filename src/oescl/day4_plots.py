from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _plot_lines(df: pd.DataFrame, y: str, yerr: str, ylabel: str, title: str, path: Path, logy: bool = False) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for scenario, group in df.groupby("display_name"):
        g = group.sort_values("launch_power_dbm")
        vals = np.maximum(g[y].to_numpy(float), 1e-8) if logy else g[y].to_numpy(float)
        ax.errorbar(
            g["launch_power_dbm"],
            vals,
            yerr=g[yerr] if yerr in g else None,
            marker="o",
            capsize=3,
            linewidth=1.5,
            label=scenario,
        )
    if logy:
        ax.set_yscale("log")
    ax.set_title(title)
    ax.set_xlabel("Launch power (dBm/channel)")
    ax.set_ylabel(ylabel)
    ax.grid(True, which="both", linewidth=0.4, alpha=0.5)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_day4_gmi(df: pd.DataFrame, path: Path) -> Path:
    return _plot_lines(df, "gmi_mean", "gmi_ci95", "Bit-metric GMI (bits/symbol)", "Day-4 SSFM-lite: exact bit-metric GMI", path)


def plot_day4_ngmi(df: pd.DataFrame, path: Path) -> Path:
    return _plot_lines(df, "ngmi_mean", "ngmi_ci95", "NGMI", "Day-4 SSFM-lite: NGMI", path)


def plot_day4_ber(df: pd.DataFrame, path: Path) -> Path:
    return _plot_lines(df, "ber_mean", "ber_ci95", "BER", "Day-4 SSFM-lite: BER", path, logy=True)


def plot_day4_gsnr(df: pd.DataFrame, path: Path) -> Path:
    return _plot_lines(df, "gsnr_db_mean", "gsnr_db_ci95", "GSNR (dB)", "Day-4 SSFM-lite: GSNR", path)


def plot_day4_rate(df: pd.DataFrame, path: Path) -> Path:
    return _plot_lines(df, "rate_tbps_mean", "rate_tbps_ci95", "Estimated net rate (Tb/s)", "Day-4 SSFM-lite: estimated net rate", path)


def plot_best_tradeoff(best_df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5.2))
    for _, row in best_df.iterrows():
        ax.scatter(row["rate_tbps_mean"], row["gsnr_db_mean"], s=70)
        ax.annotate(row["display_name"], (row["rate_tbps_mean"], row["gsnr_db_mean"]), textcoords="offset points", xytext=(7, 7), fontsize=8)
    ax.set_title("Day-4 best method trade-off")
    ax.set_xlabel("Estimated net rate (Tb/s)")
    ax.set_ylabel("GSNR (dB)")
    ax.grid(True, linewidth=0.4, alpha=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path
