from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _choose_representative_condition(pcs_ci: pd.DataFrame) -> tuple[int, float]:
    pcs = pcs_ci[pcs_ci["scenario"] == "pcs_only"].copy()
    if pcs.empty:
        return int(pcs_ci["spans"].iloc[0]), float(pcs_ci["launch_power_dbm"].iloc[0])
    # Select a challenging but useful point: max average score over nu.
    grouped = (
        pcs.groupby(["spans", "launch_power_dbm"], as_index=False)
        .agg(score=("mean_score_mean", "max"))
        .sort_values("score", ascending=False)
    )
    row = grouped.iloc[0]
    return int(row["spans"]), float(row["launch_power_dbm"])


def plot_pcs_nu_rate(pcs_ci: pd.DataFrame, path: Path) -> Path:
    spans, power = _choose_representative_condition(pcs_ci)
    df = pcs_ci[
        (pcs_ci["scenario"] == "pcs_only")
        & (pcs_ci["spans"] == spans)
        & (pcs_ci["launch_power_dbm"] == power)
    ].sort_values("pcs_nu")

    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.errorbar(
        df["pcs_nu"],
        df["total_net_rate_tbps_mean"],
        yerr=df["total_net_rate_tbps_ci95"],
        marker="o",
        capsize=3,
        linewidth=1.7,
    )
    ax.set_title(f"PCS shaping sweep: rate at {spans} spans, {power:.1f} dBm")
    ax.set_xlabel("PCS shaping coefficient, ν")
    ax.set_ylabel("Estimated total net rate (Tb/s)")
    ax.grid(True, linewidth=0.4, alpha=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_pcs_nu_ber(pcs_ci: pd.DataFrame, path: Path) -> Path:
    spans, power = _choose_representative_condition(pcs_ci)
    df = pcs_ci[
        (pcs_ci["scenario"] == "pcs_only")
        & (pcs_ci["spans"] == spans)
        & (pcs_ci["launch_power_dbm"] == power)
    ].sort_values("pcs_nu")

    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    vals = np.maximum(df["mean_ber_mean"].to_numpy(dtype=float), 1e-7)
    ax.errorbar(
        df["pcs_nu"],
        vals,
        yerr=df["mean_ber_ci95"],
        marker="o",
        capsize=3,
        linewidth=1.7,
    )
    ax.set_yscale("log")
    ax.set_title(f"PCS shaping sweep: BER at {spans} spans, {power:.1f} dBm")
    ax.set_xlabel("PCS shaping coefficient, ν")
    ax.set_ylabel("Estimated BER, log scale")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_best_nu_heatmap(pcs_ci: pd.DataFrame, path: Path) -> Path:
    pcs = pcs_ci[pcs_ci["scenario"] == "pcs_only"].copy()
    best = (
        pcs.sort_values("mean_score_mean", ascending=False)
        .groupby(["spans", "launch_power_dbm"], as_index=False)
        .head(1)
    )
    heat = best.pivot(index="spans", columns="launch_power_dbm", values="pcs_nu").sort_index()

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    im = ax.imshow(heat.values, aspect="auto")
    ax.set_xticks(np.arange(len(heat.columns)))
    ax.set_xticklabels([str(c) for c in heat.columns])
    ax.set_yticks(np.arange(len(heat.index)))
    ax.set_yticklabels([str(i) for i in heat.index])
    ax.set_xlabel("Launch power (dBm/channel)")
    ax.set_ylabel("Span count")
    ax.set_title("Best PCS shaping coefficient ν by validation score")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Selected ν")

    for i in range(heat.shape[0]):
        for j in range(heat.shape[1]):
            ax.text(j, i, f"{heat.values[i, j]:.2f}", ha="center", va="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_span_power_rate_surface(pcs_ci: pd.DataFrame, path: Path) -> Path:
    pcs = pcs_ci[pcs_ci["scenario"] == "pcs_only"].copy()
    best = (
        pcs.sort_values("mean_score_mean", ascending=False)
        .groupby(["spans", "launch_power_dbm"], as_index=False)
        .head(1)
    )
    heat = best.pivot(index="spans", columns="launch_power_dbm", values="total_net_rate_tbps_mean").sort_index()

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    im = ax.imshow(heat.values, aspect="auto")
    ax.set_xticks(np.arange(len(heat.columns)))
    ax.set_xticklabels([str(c) for c in heat.columns])
    ax.set_yticks(np.arange(len(heat.index)))
    ax.set_yticklabels([str(i) for i in heat.index])
    ax.set_xlabel("Launch power (dBm/channel)")
    ax.set_ylabel("Span count")
    ax.set_title("Best PCS-only rate over span and launch-power grid")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Estimated rate (Tb/s)")

    for i in range(heat.shape[0]):
        for j in range(heat.shape[1]):
            ax.text(j, i, f"{heat.values[i, j]:.2f}", ha="center", va="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_neural_candidate_comparison(all_ci: pd.DataFrame, path: Path) -> Path:
    df = all_ci[all_ci["scenario"].isin(["uniform_baseline", "pcs_only", "neural_only", "proposed_pcs_neural"])].copy()
    neural_points = df[df["scenario"].isin(["neural_only", "proposed_pcs_neural"])]
    if neural_points.empty:
        # Fallback plot
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.text(0.5, 0.5, "No neural candidate results found", ha="center", va="center")
        ax.axis("off")
        fig.savefig(path, dpi=300)
        plt.close(fig)
        return path

    # Choose most frequent neural candidate condition.
    cond = (
        neural_points.groupby(["spans", "launch_power_dbm"], as_index=False)
        .size()
        .sort_values("size", ascending=False)
        .iloc[0]
    )
    spans = int(cond["spans"])
    power = float(cond["launch_power_dbm"])

    subset = df[(df["spans"] == spans) & (df["launch_power_dbm"] == power)].copy()
    subset = subset.sort_values("display_name")

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    ax.bar(subset["display_name"], subset["mean_gsnr_db_mean"])
    ax.set_title(f"Candidate comparison: GSNR at {spans} spans, {power:.1f} dBm")
    ax.set_ylabel("Mean GSNR (dB)")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def plot_day2_final_tradeoff(all_ci: pd.DataFrame, path: Path) -> Path:
    df = all_ci.copy()
    best = (
        df.sort_values("mean_score_mean", ascending=False)
        .groupby("scenario", as_index=False)
        .head(1)
    )

    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    for _, row in best.iterrows():
        ax.scatter(row["total_net_rate_tbps_mean"], row["mean_gsnr_db_mean"], s=70)
        ax.annotate(
            row["display_name"],
            (row["total_net_rate_tbps_mean"], row["mean_gsnr_db_mean"]),
            textcoords="offset points",
            xytext=(7, 7),
            fontsize=8,
        )

    ax.set_title("Best operating-point trade-off by scenario")
    ax.set_xlabel("Estimated total net rate (Tb/s)")
    ax.set_ylabel("Mean GSNR (dB)")
    ax.grid(True, linewidth=0.4, alpha=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path
