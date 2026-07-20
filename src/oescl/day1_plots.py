from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCENARIO_ORDER = ["Uniform baseline", "PCS only", "Neural NLI only", "PCS + Neural NLI"]


def _ordered(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["display_name"] = pd.Categorical(df["display_name"], categories=SCENARIO_ORDER, ordered=True)
    return df.sort_values(["display_name", "launch_power_dbm"])


def plot_system_architecture(path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.axis("off")
    blocks = [
        ("Input bits", 0.05),
        ("16-QAM / PCS\nmapper", 0.20),
        ("O/E/S/C/L WDM\nchannel model", 0.38),
        ("ASE + NLI +\nimplementation noise", 0.57),
        ("Neural residual\ncompensator", 0.75),
        ("BER / GSNR /\nGMI / NGMI / Rate", 0.92),
    ]
    y, w, h = 0.55, 0.13, 0.22
    for label, x in blocks:
        ax.add_patch(plt.Rectangle((x-w/2, y-h/2), w, h, fill=False, linewidth=1.8))
        ax.text(x, y, label, ha="center", va="center", fontsize=10)
    for i in range(len(blocks)-1):
        ax.annotate("", xy=(blocks[i+1][1]-w/2, y), xytext=(blocks[i][1]+w/2, y), arrowprops=dict(arrowstyle="->", lw=1.8))
    ax.text(0.5, 0.88, "Proposed validation-aware O/E/S/C/L simulation pipeline", ha="center", fontsize=14)
    ax.text(0.38, 0.24, "Multi-band WDM, launch-power sweep, multi-seed aggregation", ha="center", fontsize=9)
    ax.text(0.75, 0.24, "Compact MLP residual regressor\n6 features -> 32 -> 16 -> 2", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_launch_power_metric(ci_df: pd.DataFrame, metric_mean_col: str, metric_ci_col: str, ylabel: str, title: str, path: Path) -> Path:
    df = _ordered(ci_df)
    fig, ax = plt.subplots(figsize=(9, 5.4))
    for display_name in SCENARIO_ORDER:
        subset = df[df["display_name"] == display_name]
        if subset.empty:
            continue
        ax.errorbar(subset["launch_power_dbm"], subset[metric_mean_col], yerr=subset[metric_ci_col], marker="o", capsize=3, linewidth=1.5, label=display_name)
    ax.set_title(title)
    ax.set_xlabel("Launch power (dBm/channel)")
    ax.set_ylabel(ylabel)
    ax.grid(True, linewidth=0.4, alpha=0.5)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_launch_power_ber(ci_df: pd.DataFrame, path: Path) -> Path:
    df = _ordered(ci_df)
    fig, ax = plt.subplots(figsize=(9, 5.4))
    floor = 1e-6
    for display_name in SCENARIO_ORDER:
        subset = df[df["display_name"] == display_name]
        if subset.empty:
            continue
        mean_vals = np.maximum(subset["mean_ber_mean"].to_numpy(dtype=float), floor)
        ci_vals = subset["mean_ber_ci95"].to_numpy(dtype=float)
        ax.errorbar(subset["launch_power_dbm"], mean_vals, yerr=ci_vals, marker="o", capsize=3, linewidth=1.5, label=display_name)
    ax.set_yscale("log")
    ax.set_title("Launch-power sweep: estimated pre-FEC BER")
    ax.set_xlabel("Launch power (dBm/channel)")
    ax.set_ylabel("Mean BER, log scale")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.5)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_complexity_clean(ci_df: pd.DataFrame, path: Path) -> Path:
    pwr = float(ci_df["launch_power_dbm"].max())
    df = _ordered(ci_df[ci_df["launch_power_dbm"] == pwr])
    fig, ax = plt.subplots(figsize=(8, 5.2))
    for _, row in df.iterrows():
        ax.scatter(row["mean_inference_time_ms_per_channel_mean"], row["mean_residual_mse_improvement_percent_mean"], s=60)
        ax.annotate(row["display_name"], (row["mean_inference_time_ms_per_channel_mean"], row["mean_residual_mse_improvement_percent_mean"]), textcoords="offset points", xytext=(6,6), fontsize=8)
    ax.set_title(f"Complexity/performance trade-off at {pwr:.1f} dBm")
    ax.set_xlabel("Mean inference time per channel (ms)")
    ax.set_ylabel("Residual MSE improvement (%)")
    ax.grid(True, linewidth=0.4, alpha=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_band_heatmap(channel_df: pd.DataFrame, path: Path) -> Path:
    df = channel_df[channel_df["scenario"] == "proposed_pcs_neural"].copy()
    heat = df.groupby(["band", "launch_power_dbm"], as_index=False).agg(mean_gsnr_db=("gsnr_db", "mean")).pivot(index="band", columns="launch_power_dbm", values="mean_gsnr_db").sort_index()
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    im = ax.imshow(heat.values, aspect="auto")
    ax.set_xticks(np.arange(len(heat.columns)))
    ax.set_xticklabels([str(c) for c in heat.columns])
    ax.set_yticks(np.arange(len(heat.index)))
    ax.set_yticklabels(heat.index)
    ax.set_xlabel("Launch power (dBm/channel)")
    ax.set_ylabel("Band")
    ax.set_title("Proposed method: band-wise GSNR heatmap")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Mean GSNR (dB)")
    for i in range(heat.shape[0]):
        for j in range(heat.shape[1]):
            ax.text(j, i, f"{heat.values[i,j]:.1f}", ha="center", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path
