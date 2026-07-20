from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from typing import Dict, List
import textwrap
import numpy as np
import pandas as pd
from .channel import make_channel_plan, estimate_noise_variances, apply_optical_channel, ChannelSpec
from .constellation import sample_symbols
from .metrics import compute_channel_metrics
from .neural_nli import apply_neural_nli_mitigation
from .utils import ensure_dir
from .day1_plots import plot_system_architecture, plot_launch_power_metric, plot_launch_power_ber, plot_complexity_clean, plot_band_heatmap


def _scenario_grid() -> List[Dict]:
    return [
        {"scenario": "uniform_baseline", "display_name": "Uniform baseline", "shaped": False, "neural": False},
        {"scenario": "pcs_only", "display_name": "PCS only", "shaped": True, "neural": False},
        {"scenario": "neural_only", "display_name": "Neural NLI only", "shaped": False, "neural": True},
        {"scenario": "proposed_pcs_neural", "display_name": "PCS + Neural NLI", "shaped": True, "neural": True},
    ]


def _temporary_channel_with_power(channel: ChannelSpec, launch_power_dbm: float) -> ChannelSpec:
    return ChannelSpec(channel.band, channel.channel_id, channel.frequency_offset_ghz, channel.wavelength_nm, float(launch_power_dbm))


def _stress_noise(noise_stats: Dict[str, float], cfg: Dict) -> Dict[str, float]:
    day1 = cfg.get("day1", {})
    noise_scale = float(day1.get("stress_noise_scale", 1.0))
    nli_scale = float(day1.get("stress_nli_scale", 1.0))
    imp_scale = float(day1.get("stress_implementation_scale", 1.0))
    stressed = dict(noise_stats)
    stressed["ase_var"] = float(stressed["ase_var"] * noise_scale)
    stressed["nli_var"] = float(stressed["nli_var"] * nli_scale)
    stressed["implementation_var"] = float(stressed["implementation_var"] * imp_scale)
    stressed["total_noise_var"] = stressed["ase_var"] + stressed["nli_var"] + stressed["implementation_var"]
    stressed["gsnr_db"] = float(10.0 * np.log10(1.0 / max(stressed["total_noise_var"], 1e-15)))
    return stressed


def _day1_channel_plan(cfg: Dict) -> List[ChannelSpec]:
    local_cfg = deepcopy(cfg)
    channels_per_band = int(cfg.get("day1", {}).get("channels_per_band", cfg["simulation"]["n_channels_per_band_full"]))
    local_cfg["simulation"]["n_channels_per_band_full"] = channels_per_band
    return make_channel_plan(local_cfg, mode="full")


def _run_single_day1_condition(cfg: Dict, seed: int, launch_power_dbm: float, channel_plan: List[ChannelSpec]) -> List[Dict]:
    rng = np.random.default_rng(int(seed))
    rows = []
    n_symbols = int(cfg.get("day1", {}).get("symbols_per_channel", cfg["simulation"]["symbols_per_channel_full"]))
    for scenario in _scenario_grid():
        for base_channel in channel_plan:
            channel = _temporary_channel_with_power(base_channel, launch_power_dbm)
            tx_symbols, tx_indices, probs = sample_symbols(n_symbols=n_symbols, shaped=bool(scenario["shaped"]), nu=float(cfg["pcs"]["shaping_nu"]), rng=rng)
            noise_stats = estimate_noise_variances(channel=channel, cfg=cfg, shaped=bool(scenario["shaped"]), neural_mitigation=False)
            noise_stats = _stress_noise(noise_stats, cfg)
            rx_symbols, _ = apply_optical_channel(tx_symbols=tx_symbols, noise_stats=noise_stats, rng=rng)
            if bool(scenario["neural"]):
                local_cfg = deepcopy(cfg)
                if "max_iter_day1" in local_cfg["neural_nli"]:
                    local_cfg["neural_nli"]["max_iter_full"] = int(local_cfg["neural_nli"]["max_iter_day1"])
                neural_result = apply_neural_nli_mitigation(tx_symbols=tx_symbols, rx_symbols=rx_symbols, cfg=local_cfg, mode="full", model_name=f"day1_seed{seed}_pwr{launch_power_dbm}_{scenario['scenario']}_{channel.band}_{channel.channel_id}")
                rx_for_metrics = neural_result.corrected_symbols
                parameter_count = neural_result.parameter_count
                train_time_s = neural_result.train_time_s
                inference_time_s = neural_result.inference_time_s
                mse_before = neural_result.residual_mse_before
                mse_after = neural_result.residual_mse_after
            else:
                rx_for_metrics = rx_symbols
                parameter_count = 0
                train_time_s = 0.0
                inference_time_s = 0.0
                mse_before = float(np.mean(np.abs(rx_symbols - tx_symbols) ** 2))
                mse_after = mse_before
            metrics = compute_channel_metrics(tx_symbols=tx_symbols, tx_indices=tx_indices, rx_symbols=rx_for_metrics, probs=probs, cfg=cfg)
            rows.append({
                "seed": int(seed), "launch_power_dbm": float(launch_power_dbm),
                "scenario": scenario["scenario"], "display_name": scenario["display_name"],
                "band": channel.band, "channel_id": channel.channel_id,
                "shaped": bool(scenario["shaped"]), "neural_nli": bool(scenario["neural"]),
                **noise_stats, **metrics,
                "parameter_count": int(parameter_count), "train_time_s": float(train_time_s),
                "inference_time_s": float(inference_time_s), "residual_mse_before": float(mse_before),
                "residual_mse_after": float(mse_after),
                "residual_mse_improvement_percent": float(100.0 * (1.0 - mse_after / max(mse_before, 1e-15))),
            })
    return rows


def _aggregate_seed_level(channel_df: pd.DataFrame) -> pd.DataFrame:
    return channel_df.groupby(["seed", "launch_power_dbm", "scenario", "display_name"], as_index=False).agg(
        total_net_rate_tbps=("net_rate_tbps", "sum"),
        mean_gsnr_db=("gsnr_db", "mean"),
        mean_ber=("ber", "mean"),
        mean_ngmi=("ngmi", "mean"),
        mean_parameter_count=("parameter_count", "mean"),
        total_train_time_s=("train_time_s", "sum"),
        mean_inference_time_ms_per_channel=("inference_time_s", lambda s: float(np.mean(s) * 1000.0)),
        mean_residual_mse_improvement_percent=("residual_mse_improvement_percent", "mean"),
        n_channels=("channel_id", "count"),
    )


def _aggregate_ci(seed_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    metrics = ["total_net_rate_tbps", "mean_gsnr_db", "mean_ber", "mean_ngmi", "mean_inference_time_ms_per_channel", "mean_residual_mse_improvement_percent"]
    for keys, group in seed_df.groupby(["launch_power_dbm", "scenario", "display_name"]):
        launch_power_dbm, scenario, display_name = keys
        row = {"launch_power_dbm": launch_power_dbm, "scenario": scenario, "display_name": display_name, "n_seeds": int(group["seed"].nunique()), "n_channels_per_seed": int(group["n_channels"].iloc[0])}
        for metric in metrics:
            vals = group[metric].astype(float).to_numpy()
            mean = float(np.mean(vals))
            std = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
            ci95 = float(1.96 * std / np.sqrt(max(len(vals), 1)))
            row[f"{metric}_mean"] = mean
            row[f"{metric}_std"] = std
            row[f"{metric}_ci95"] = ci95
        rows.append(row)
    return pd.DataFrame(rows)


def _write_day1_report(cfg: Dict, ci_df: pd.DataFrame, figure_paths: List[Path]) -> Path:
    path = ensure_dir(cfg["output"]["reports"]) / "day1_ieee_optica_upgrade_report.md"
    proposed = ci_df[ci_df["scenario"] == "proposed_pcs_neural"].copy()
    baseline = ci_df[ci_df["scenario"] == "uniform_baseline"].copy()
    best_prop_gsnr = proposed.sort_values("mean_gsnr_db_mean", ascending=False).iloc[0]
    best_prop_rate = proposed.sort_values("total_net_rate_tbps_mean", ascending=False).iloc[0]
    merged = proposed.merge(baseline[["launch_power_dbm", "total_net_rate_tbps_mean", "mean_gsnr_db_mean"]], on="launch_power_dbm", suffixes=("_proposed", "_baseline"))
    merged["rate_delta_tbps"] = merged["total_net_rate_tbps_mean_proposed"] - merged["total_net_rate_tbps_mean_baseline"]
    merged["gsnr_delta_db"] = merged["mean_gsnr_db_mean_proposed"] - merged["mean_gsnr_db_mean_baseline"]
    best_delta_gsnr = merged.sort_values("gsnr_delta_db", ascending=False).iloc[0]
    lines = [
        "# Day-1 IEEE/Optica Upgrade Report", "",
        "## What was added", "",
        "- Real system-architecture diagram for Fig. 1.",
        "- Launch-power sweep across multiple powers.",
        "- Five-seed repeated simulation.",
        "- Mean, standard deviation, and 95% confidence intervals.",
        "- BER log-scale figure.",
        "- Cleaner complexity/performance plot.",
        "- Band-wise GSNR heatmap.", "",
        "## Key Day-1 findings", "",
        f"- Best proposed mean GSNR: **{best_prop_gsnr['mean_gsnr_db_mean']:.3f} ± {best_prop_gsnr['mean_gsnr_db_ci95']:.3f} dB** at **{best_prop_gsnr['launch_power_dbm']} dBm**.",
        f"- Best proposed mean estimated rate: **{best_prop_rate['total_net_rate_tbps_mean']:.3f} ± {best_prop_rate['total_net_rate_tbps_ci95']:.3f} Tb/s** at **{best_prop_rate['launch_power_dbm']} dBm**.",
        f"- Largest GSNR advantage over uniform baseline: **{best_delta_gsnr['gsnr_delta_db']:.3f} dB** at **{best_delta_gsnr['launch_power_dbm']} dBm**.",
        f"- Rate delta at that point: **{best_delta_gsnr['rate_delta_tbps']:.4f} Tb/s**.", "",
        "## Submission-safe interpretation", "",
        "The Day-1 results should be framed as a sweep-based validation upgrade. The strongest claim is not universal capacity improvement; it is that the framework identifies operating regions where neural residual compensation improves GSNR and residual distortion, while PCS must be tuned carefully.", "",
        "## Generated figures", ""
    ]
    for p in figure_paths:
        lines.append(f"- `{p}`")
    lines += ["", "## CI table preview", ""]
    preview_cols = ["launch_power_dbm", "display_name", "total_net_rate_tbps_mean", "total_net_rate_tbps_ci95", "mean_gsnr_db_mean", "mean_gsnr_db_ci95", "mean_ber_mean", "mean_ngmi_mean"]
    lines.append(ci_df[preview_cols].round(6).to_markdown(index=False))
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_latex_snippet(cfg: Dict, ci_df: pd.DataFrame) -> Path:
    path = ensure_dir(cfg["output"]["reports"]) / "day1_latex_results_snippet.tex"
    proposed = ci_df[ci_df["scenario"] == "proposed_pcs_neural"].copy()
    best_prop = proposed.sort_values("mean_gsnr_db_mean", ascending=False).iloc[0]
    text = rf'''
% Paste this into the improved IEEE/Optica Results section after running Day-1 mode.
\subsection{{Launch-Power Sweep With Multi-Seed Confidence Intervals}}
To avoid the saturation observed in the initial single-run experiment, the Day-1 upgrade evaluates the four ablation scenarios across a launch-power grid using five independent random seeds. For each launch-power point, the reported value is the mean over seeds, and the error bar denotes the 95\% confidence interval.

Fig.~\ref{{fig:day1_gsnr_sweep}} shows the resulting GSNR trend. The proposed PCS + neural residual-compensation configuration reaches its highest mean GSNR of {best_prop['mean_gsnr_db_mean']:.2f}$\pm${best_prop['mean_gsnr_db_ci95']:.2f} dB at {best_prop['launch_power_dbm']:.1f} dBm. Unlike the initial single-run result, this sweep is more suitable for conference review because it exposes operating-region dependence rather than reporting one saturated point.

\begin{{figure}}[!t]
\centering
\includegraphics[width=\columnwidth]{{fig_day1_launch_power_gsnr.png}}
\caption{{Launch-power sweep of mean GSNR with 95\% confidence intervals over five random seeds.}}
\label{{fig:day1_gsnr_sweep}}
\end{{figure}}

\begin{{figure}}[!t]
\centering
\includegraphics[width=\columnwidth]{{fig_day1_launch_power_ber_log.png}}
\caption{{Launch-power sweep of estimated pre-FEC BER on a logarithmic scale.}}
\label{{fig:day1_ber_sweep}}
\end{{figure}}

\begin{{figure}}[!t]
\centering
\includegraphics[width=\columnwidth]{{fig_day1_launch_power_rate.png}}
\caption{{Launch-power sweep of estimated total net achievable rate with 95\% confidence intervals.}}
\label{{fig:day1_rate_sweep}}
\end{{figure}}
'''
    path.write_text(textwrap.dedent(text).strip()+"\n", encoding="utf-8")
    return path


def run_day1_ieee_optica_upgrade(cfg: Dict) -> Dict:
    tables_dir = ensure_dir(cfg["output"]["tables"])
    figures_dir = ensure_dir(cfg["output"]["figures"])
    seeds = [int(s) for s in cfg.get("day1", {}).get("seeds", [1,2,3,4,5])]
    powers = [float(p) for p in cfg.get("day1", {}).get("launch_power_dbm_grid", cfg["simulation"]["launch_power_dbm_grid"])]
    channel_plan = _day1_channel_plan(cfg)
    all_rows = []
    for seed in seeds:
        for power in powers:
            all_rows.extend(_run_single_day1_condition(cfg=cfg, seed=seed, launch_power_dbm=power, channel_plan=channel_plan))
    channel_df = pd.DataFrame(all_rows)
    seed_df = _aggregate_seed_level(channel_df)
    ci_df = _aggregate_ci(seed_df)
    channel_csv = tables_dir / "day1_channel_metrics.csv"
    seed_csv = tables_dir / "day1_seed_level_summary.csv"
    ci_csv = tables_dir / "day1_launch_power_ci.csv"
    channel_df.to_csv(channel_csv, index=False)
    seed_df.to_csv(seed_csv, index=False)
    ci_df.to_csv(ci_csv, index=False)
    figure_paths = []
    if bool(cfg.get("day1", {}).get("generate_system_diagram", True)):
        figure_paths.append(plot_system_architecture(figures_dir / "fig_day1_system_architecture.png"))
    figure_paths.append(plot_launch_power_metric(ci_df, "mean_gsnr_db_mean", "mean_gsnr_db_ci95", "Mean GSNR (dB)", "Launch-power sweep: GSNR with 95% CI", figures_dir / "fig_day1_launch_power_gsnr.png"))
    figure_paths.append(plot_launch_power_metric(ci_df, "mean_ngmi_mean", "mean_ngmi_ci95", "Mean NGMI", "Launch-power sweep: NGMI with 95% CI", figures_dir / "fig_day1_launch_power_ngmi.png"))
    figure_paths.append(plot_launch_power_metric(ci_df, "total_net_rate_tbps_mean", "total_net_rate_tbps_ci95", "Estimated total net rate (Tb/s)", "Launch-power sweep: estimated net rate with 95% CI", figures_dir / "fig_day1_launch_power_rate.png"))
    figure_paths.append(plot_launch_power_ber(ci_df, figures_dir / "fig_day1_launch_power_ber_log.png"))
    figure_paths.append(plot_complexity_clean(ci_df, figures_dir / "fig_day1_complexity_clean.png"))
    figure_paths.append(plot_band_heatmap(channel_df, figures_dir / "fig_day1_bandwise_gsnr_heatmap.png"))
    report_path = _write_day1_report(cfg, ci_df, figure_paths)
    latex_snippet_path = _write_latex_snippet(cfg, ci_df)
    return {"channel_csv": str(channel_csv), "seed_csv": str(seed_csv), "ci_csv": str(ci_csv), "report_path": str(report_path), "latex_snippet_path": str(latex_snippet_path), "figure_paths": [str(p) for p in figure_paths]}
