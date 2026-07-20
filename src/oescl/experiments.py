from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from .channel import apply_optical_channel, estimate_noise_variances, make_channel_plan
from .constellation import sample_symbols
from .metrics import compute_channel_metrics
from .neural_nli import apply_neural_nli_mitigation
from .plots import generate_all_plots
from .utils import ensure_dir


def _scenario_grid() -> List[Dict]:
    return [
        {
            "scenario": "uniform_baseline",
            "display_name": "Uniform baseline",
            "shaped": False,
            "neural": False,
        },
        {
            "scenario": "pcs_only",
            "display_name": "PCS only",
            "shaped": True,
            "neural": False,
        },
        {
            "scenario": "neural_only",
            "display_name": "Neural NLI only",
            "shaped": False,
            "neural": True,
        },
        {
            "scenario": "proposed_pcs_neural",
            "display_name": "Proposed PCS + Neural NLI",
            "shaped": True,
            "neural": True,
        },
    ]


def _symbols_per_channel(cfg: Dict, mode: str) -> int:
    return (
        int(cfg["simulation"]["symbols_per_channel_smoke"])
        if mode == "smoke"
        else int(cfg["simulation"]["symbols_per_channel_full"])
    )


def run_experiment(cfg: Dict, mode: str) -> Dict:
    seed = int(cfg["simulation"]["seed"])
    rng = np.random.default_rng(seed)
    channel_plan = make_channel_plan(cfg, mode=mode)
    n_symbols = _symbols_per_channel(cfg, mode=mode)

    rows = []
    scenario_rows = []
    complexity_rows = []

    for scenario in _scenario_grid():
        scenario_channel_rates = []
        scenario_bers = []
        scenario_ngmis = []
        scenario_gsnrs = []

        for channel in channel_plan:
            tx_symbols, tx_indices, probs = sample_symbols(
                n_symbols=n_symbols,
                shaped=bool(scenario["shaped"]),
                nu=float(cfg["pcs"]["shaping_nu"]),
                rng=rng,
            )

            noise_stats = estimate_noise_variances(
                channel=channel,
                cfg=cfg,
                shaped=bool(scenario["shaped"]),
                neural_mitigation=False,
            )
            rx_symbols, _ = apply_optical_channel(
                tx_symbols=tx_symbols,
                noise_stats=noise_stats,
                rng=rng,
            )

            neural_result = None
            if bool(scenario["neural"]):
                neural_result = apply_neural_nli_mitigation(
                    tx_symbols=tx_symbols,
                    rx_symbols=rx_symbols,
                    cfg=cfg,
                    mode=mode,
                    model_name=f"{scenario['scenario']}_{channel.band}_{channel.channel_id}",
                )
                rx_for_metrics = neural_result.corrected_symbols
            else:
                rx_for_metrics = rx_symbols

            metrics = compute_channel_metrics(
                tx_symbols=tx_symbols,
                tx_indices=tx_indices,
                rx_symbols=rx_for_metrics,
                probs=probs,
                cfg=cfg,
            )

            scenario_channel_rates.append(metrics["net_rate_tbps"])
            scenario_bers.append(metrics["ber"])
            scenario_ngmis.append(metrics["ngmi"])
            scenario_gsnrs.append(metrics["gsnr_db"])

            if neural_result is not None:
                parameter_count = neural_result.parameter_count
                train_time_s = neural_result.train_time_s
                inference_time_s = neural_result.inference_time_s
                residual_mse_before = neural_result.residual_mse_before
                residual_mse_after = neural_result.residual_mse_after
            else:
                parameter_count = 0
                train_time_s = 0.0
                inference_time_s = 0.0
                residual_mse_before = float(np.mean(np.abs(rx_symbols - tx_symbols) ** 2))
                residual_mse_after = residual_mse_before

            rows.append(
                {
                    "scenario": scenario["scenario"],
                    "display_name": scenario["display_name"],
                    "band": channel.band,
                    "channel_id": channel.channel_id,
                    "wavelength_nm": channel.wavelength_nm,
                    "frequency_offset_ghz": channel.frequency_offset_ghz,
                    "launch_power_dbm": channel.launch_power_dbm,
                    "shaped": scenario["shaped"],
                    "neural_nli": scenario["neural"],
                    **noise_stats,
                    **metrics,
                    "parameter_count": parameter_count,
                    "train_time_s": train_time_s,
                    "inference_time_s": inference_time_s,
                    "residual_mse_before": residual_mse_before,
                    "residual_mse_after": residual_mse_after,
                }
            )

        total_rate = float(np.sum(scenario_channel_rates))
        scenario_rows.append(
            {
                "scenario": scenario["scenario"],
                "display_name": scenario["display_name"],
                "total_net_rate_tbps": total_rate,
                "mean_net_rate_tbps_per_channel": float(np.mean(scenario_channel_rates)),
                "mean_ber": float(np.mean(scenario_bers)),
                "median_ber": float(np.median(scenario_bers)),
                "mean_ngmi": float(np.mean(scenario_ngmis)),
                "mean_gsnr_db": float(np.mean(scenario_gsnrs)),
                "n_channels": len(channel_plan),
            }
        )

        scenario_df_partial = pd.DataFrame([row for row in rows if row["scenario"] == scenario["scenario"]])
        if scenario["neural"]:
            complexity_rows.append(
                {
                    "scenario": scenario["scenario"],
                    "display_name": scenario["display_name"],
                    "mean_parameter_count": float(scenario_df_partial["parameter_count"].mean()),
                    "total_train_time_s": float(scenario_df_partial["train_time_s"].sum()),
                    "mean_inference_time_ms_per_channel": float(
                        scenario_df_partial["inference_time_s"].mean() * 1000.0
                    ),
                    "mean_residual_mse_improvement_percent": float(
                        100.0
                        * (
                            1.0
                            - scenario_df_partial["residual_mse_after"].mean()
                            / max(scenario_df_partial["residual_mse_before"].mean(), 1e-15)
                        )
                    ),
                }
            )
        else:
            complexity_rows.append(
                {
                    "scenario": scenario["scenario"],
                    "display_name": scenario["display_name"],
                    "mean_parameter_count": 0.0,
                    "total_train_time_s": 0.0,
                    "mean_inference_time_ms_per_channel": 0.0,
                    "mean_residual_mse_improvement_percent": 0.0,
                }
            )

    channel_df = pd.DataFrame(rows)
    scenario_df = pd.DataFrame(scenario_rows)
    complexity_df = pd.DataFrame(complexity_rows)

    tables_dir = ensure_dir(cfg["output"]["tables"])
    channel_csv = tables_dir / f"channel_metrics_{mode}.csv"
    scenario_csv = tables_dir / f"scenario_summary_{mode}.csv"
    complexity_csv = tables_dir / f"complexity_summary_{mode}.csv"

    channel_df.to_csv(channel_csv, index=False)
    scenario_df.to_csv(scenario_csv, index=False)
    complexity_df.to_csv(complexity_csv, index=False)

    figure_paths = generate_all_plots(
        channel_df=channel_df,
        scenario_df=scenario_df,
        complexity_df=complexity_df,
        cfg=cfg,
        mode=mode,
    )

    return {
        "mode": mode,
        "channel_metrics": channel_df,
        "scenario_summary": scenario_df,
        "complexity_summary": complexity_df,
        "channel_csv": channel_csv,
        "scenario_csv": scenario_csv,
        "complexity_csv": complexity_csv,
        "figure_paths": figure_paths,
        "channel_plan_size": len(channel_plan),
    }
