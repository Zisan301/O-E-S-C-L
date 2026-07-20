from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd

from .utils import ensure_dir


def _save_bar(df: pd.DataFrame, x: str, y: str, title: str, ylabel: str, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(df[x], df[y])
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def generate_all_plots(
    channel_df: pd.DataFrame,
    scenario_df: pd.DataFrame,
    complexity_df: pd.DataFrame,
    cfg: Dict,
    mode: str,
) -> List[Path]:
    figures_dir = ensure_dir(cfg["output"]["figures"])
    paths: List[Path] = []

    scenario_order = [
        "Uniform baseline",
        "PCS only",
        "Neural NLI only",
        "Proposed PCS + Neural NLI",
    ]
    scenario_df = scenario_df.copy()
    scenario_df["display_name"] = pd.Categorical(
        scenario_df["display_name"],
        categories=scenario_order,
        ordered=True,
    )
    scenario_df = scenario_df.sort_values("display_name")

    paths.append(
        _save_bar(
            scenario_df,
            x="display_name",
            y="total_net_rate_tbps",
            title="Estimated total net achievable rate",
            ylabel="Net rate (Tb/s)",
            path=figures_dir / f"fig_total_net_rate_{mode}.png",
        )
    )

    paths.append(
        _save_bar(
            scenario_df,
            x="display_name",
            y="mean_ngmi",
            title="Mean NGMI by scenario",
            ylabel="Mean NGMI",
            path=figures_dir / f"fig_mean_ngmi_{mode}.png",
        )
    )

    paths.append(
        _save_bar(
            scenario_df,
            x="display_name",
            y="mean_ber",
            title="Mean estimated pre-FEC BER by scenario",
            ylabel="Mean BER",
            path=figures_dir / f"fig_mean_ber_{mode}.png",
        )
    )

    paths.append(
        _save_bar(
            scenario_df,
            x="display_name",
            y="mean_gsnr_db",
            title="Mean GSNR by scenario",
            ylabel="Mean GSNR (dB)",
            path=figures_dir / f"fig_mean_gsnr_{mode}.png",
        )
    )

    band_df = (
        channel_df.groupby(["display_name", "band"], as_index=False)
        .agg(mean_gsnr_db=("gsnr_db", "mean"), mean_ngmi=("ngmi", "mean"))
    )
    proposed = band_df[band_df["display_name"] == "Proposed PCS + Neural NLI"].copy()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(proposed["band"], proposed["mean_gsnr_db"], marker="o")
    ax.set_title("Proposed method: band-wise GSNR")
    ax.set_xlabel("Band")
    ax.set_ylabel("Mean GSNR (dB)")
    fig.tight_layout()
    p = figures_dir / f"fig_bandwise_gsnr_proposed_{mode}.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    paths.append(p)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(
        complexity_df["mean_inference_time_ms_per_channel"],
        complexity_df["mean_residual_mse_improvement_percent"],
    )
    for _, row in complexity_df.iterrows():
        ax.annotate(
            str(row["display_name"]),
            (
                row["mean_inference_time_ms_per_channel"],
                row["mean_residual_mse_improvement_percent"],
            ),
            fontsize=8,
        )
    ax.set_title("Complexity/performance trade-off")
    ax.set_xlabel("Mean inference time per channel (ms)")
    ax.set_ylabel("Residual MSE improvement (%)")
    fig.tight_layout()
    p = figures_dir / f"fig_complexity_tradeoff_{mode}.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    paths.append(p)

    return paths
