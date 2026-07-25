from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _err(ax, g, x, y, yerr, label):
    ax.errorbar(g[x], g[y], yerr=g[yerr], marker="o", capsize=3, linewidth=1.5, label=label)


def plot_day8_gmi_vs_nu(df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    for s, g in df.groupby("scenario_group"):
        _err(ax, g.sort_values("pcs_nu"), "pcs_nu", "gmi_mean", "gmi_ci95", s)
    ax.set_xlabel("PCS shaping coefficient, nu")
    ax.set_ylabel("BMD-GMI (bits/symbol)")
    ax.grid(True, linewidth=0.3, alpha=0.55)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_day8_rate_gain(df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    y = "air_gain_mean" if "air_gain_mean" in df.columns else "rate_gain_mean"
    yerr = "air_gain_ci95" if "air_gain_ci95" in df.columns else "rate_gain_ci95"
    for s, g in df.groupby("scenario_group"):
        _err(ax, g.sort_values("pcs_nu"), "pcs_nu", y, yerr, s)
    ax.axhline(0, linewidth=1)
    ax.set_xlabel("PCS shaping coefficient, nu")
    ax.set_ylabel("AIR gain (Tb/s/channel)")
    ax.grid(True, linewidth=0.3, alpha=0.55)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_day8_ber(df: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    for s, g in df.groupby("scenario_group"):
        g = g.sort_values("pcs_nu")
        ax.errorbar(
            g["pcs_nu"],
            np.maximum(g["ber_mean"], 1e-10),
            yerr=g["ber_ci95"],
            marker="o",
            capsize=3,
            linewidth=1.5,
            label=s,
        )
    ax.set_yscale("log")
    ax.set_xlabel("PCS shaping coefficient, nu")
    ax.set_ylabel("BER")
    ax.grid(True, which="both", linewidth=0.3, alpha=0.55)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_day8_heatmap(df: pd.DataFrame, path: Path) -> Path:
    pivot = df.pivot_table(index="scenario_group", columns="spans", values="best_gmi_gain", aggfunc="mean")
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    data = pivot.to_numpy(float)
    im = ax.imshow(data, aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([str(c) for c in pivot.columns])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(list(pivot.index))
    ax.set_xlabel("Span count")
    fig.colorbar(im, ax=ax).set_label("BMD-GMI gain")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, f"{data[i, j]:.3f}", ha="center", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_day8_aggregate_rate(df: pd.DataFrame, path: Path) -> Path:
    y = "aggregate_air_gain_mean" if "aggregate_air_gain_mean" in df.columns else "aggregate_rate_gain_mean"
    fig, ax = plt.subplots(figsize=(8, 4.5))
    g = df.sort_values(y, ascending=False)
    ax.bar(g["scenario_group"], g[y])
    ax.set_ylabel("Aggregate AIR gain (Tb/s)")
    ax.grid(True, axis="y", linewidth=0.3, alpha=0.55)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path
