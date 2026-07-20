from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import textwrap
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .channel import make_channel_plan, estimate_noise_variances, apply_optical_channel, ChannelSpec
from .constellation import sample_symbols
from .metrics import compute_channel_metrics
from .neural_nli import apply_neural_nli_mitigation
from .utils import ensure_dir
from .day2_plots import (
    plot_best_nu_heatmap,
    plot_pcs_nu_rate,
    plot_pcs_nu_ber,
    plot_span_power_rate_surface,
    plot_neural_candidate_comparison,
    plot_day2_final_tradeoff,
)


def _channel_plan(cfg: Dict) -> List[ChannelSpec]:
    local_cfg = deepcopy(cfg)
    local_cfg["simulation"]["n_channels_per_band_full"] = int(cfg["day2"]["channels_per_band"])
    return make_channel_plan(local_cfg, mode="full")


def _channel_with_power(channel: ChannelSpec, power_dbm: float) -> ChannelSpec:
    return ChannelSpec(
        band=channel.band,
        channel_id=channel.channel_id,
        frequency_offset_ghz=channel.frequency_offset_ghz,
        wavelength_nm=channel.wavelength_nm,
        launch_power_dbm=float(power_dbm),
    )


def _cfg_with_span_and_nu(cfg: Dict, spans: int, nu: float) -> Dict:
    local_cfg = deepcopy(cfg)
    local_cfg["simulation"]["spans"] = int(spans)
    local_cfg["pcs"]["shaping_nu"] = float(nu)
    return local_cfg


def _stress_noise(noise_stats: Dict[str, float], cfg: Dict, launch_power_dbm: float, spans: int) -> Dict[str, float]:
    day2 = cfg["day2"]
    p_factor = 1.0 + max(float(launch_power_dbm), 0.0) / 5.0
    span_factor = float(spans) / 6.0

    stressed = dict(noise_stats)
    stressed["ase_var"] = float(stressed["ase_var"] * float(day2["stress_noise_scale"]) * span_factor)
    stressed["nli_var"] = float(stressed["nli_var"] * float(day2["stress_nli_scale"]) * p_factor * span_factor)
    stressed["implementation_var"] = float(stressed["implementation_var"] * float(day2["stress_implementation_scale"]))
    stressed["total_noise_var"] = (
        stressed["ase_var"] + stressed["nli_var"] + stressed["implementation_var"]
    )
    stressed["gsnr_db"] = float(10.0 * np.log10(1.0 / max(stressed["total_noise_var"], 1e-15)))
    return stressed


def _run_channel_set(
    cfg: Dict,
    seed: int,
    spans: int,
    power_dbm: float,
    nu: float,
    shaped: bool,
    neural: bool,
    scenario: str,
    display_name: str,
    channel_plan: List[ChannelSpec],
) -> List[Dict]:
    rng = np.random.default_rng(int(seed))
    rows = []
    n_symbols = int(cfg["day2"]["symbols_per_channel"])
    local_cfg = _cfg_with_span_and_nu(cfg, spans=spans, nu=nu)

    for base_ch in channel_plan:
        ch = _channel_with_power(base_ch, power_dbm)
        tx_symbols, tx_indices, probs = sample_symbols(
            n_symbols=n_symbols,
            shaped=bool(shaped),
            nu=float(nu),
            rng=rng,
        )
        noise_stats = estimate_noise_variances(
            channel=ch,
            cfg=local_cfg,
            shaped=bool(shaped),
            neural_mitigation=False,
        )
        noise_stats = _stress_noise(noise_stats, cfg=local_cfg, launch_power_dbm=power_dbm, spans=spans)

        rx_symbols, _ = apply_optical_channel(tx_symbols=tx_symbols, noise_stats=noise_stats, rng=rng)

        if neural:
            neural_cfg = deepcopy(local_cfg)
            neural_cfg["neural_nli"]["max_iter_full"] = int(cfg["neural_nli"].get("max_iter_day2", 100))
            neural_cfg["neural_nli"]["random_state"] = int(seed)
            neural_result = apply_neural_nli_mitigation(
                tx_symbols=tx_symbols,
                rx_symbols=rx_symbols,
                cfg=neural_cfg,
                mode="full",
                model_name=f"day2_seed{seed}_sp{spans}_p{power_dbm}_nu{nu}_{scenario}_{ch.band}_{ch.channel_id}",
            )
            rx_for_metrics = neural_result.corrected_symbols
            param_count = neural_result.parameter_count
            train_time_s = neural_result.train_time_s
            inference_time_s = neural_result.inference_time_s
            mse_before = neural_result.residual_mse_before
            mse_after = neural_result.residual_mse_after
        else:
            rx_for_metrics = rx_symbols
            param_count = 0
            train_time_s = 0.0
            inference_time_s = 0.0
            mse_before = float(np.mean(np.abs(rx_symbols - tx_symbols) ** 2))
            mse_after = mse_before

        metrics = compute_channel_metrics(
            tx_symbols=tx_symbols,
            tx_indices=tx_indices,
            rx_symbols=rx_for_metrics,
            probs=probs,
            cfg=local_cfg,
        )

        # Create a review-useful score: rate + GSNR bonus - BER penalty.
        score = (
            float(cfg["day2"]["score_rate_weight"]) * metrics["net_rate_tbps"]
            + float(cfg["day2"]["score_gsnr_weight"]) * metrics["gsnr_db"]
            - float(cfg["day2"]["score_ber_penalty"]) * metrics["ber"]
        )

        rows.append(
            {
                "seed": int(seed),
                "spans": int(spans),
                "launch_power_dbm": float(power_dbm),
                "pcs_nu": float(nu),
                "scenario": scenario,
                "display_name": display_name,
                "band": ch.band,
                "channel_id": int(ch.channel_id),
                "shaped": bool(shaped),
                "neural_nli": bool(neural),
                **noise_stats,
                **metrics,
                "parameter_count": int(param_count),
                "train_time_s": float(train_time_s),
                "inference_time_s": float(inference_time_s),
                "residual_mse_before": float(mse_before),
                "residual_mse_after": float(mse_after),
                "residual_mse_improvement_percent": float(100.0 * (1.0 - mse_after / max(mse_before, 1e-15))),
                "score": float(score),
            }
        )

    return rows


def _seed_level(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(
            ["seed", "spans", "launch_power_dbm", "pcs_nu", "scenario", "display_name"],
            as_index=False,
        )
        .agg(
            total_net_rate_tbps=("net_rate_tbps", "sum"),
            mean_gsnr_db=("gsnr_db", "mean"),
            mean_ber=("ber", "mean"),
            mean_ngmi=("ngmi", "mean"),
            mean_score=("score", "mean"),
            mean_parameter_count=("parameter_count", "mean"),
            total_train_time_s=("train_time_s", "sum"),
            mean_inference_time_ms_per_channel=("inference_time_s", lambda s: float(np.mean(s) * 1000.0)),
            mean_residual_mse_improvement_percent=("residual_mse_improvement_percent", "mean"),
            n_channels=("channel_id", "count"),
        )
    )


def _ci(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    keys = ["spans", "launch_power_dbm", "pcs_nu", "scenario", "display_name"]
    metrics = [
        "total_net_rate_tbps",
        "mean_gsnr_db",
        "mean_ber",
        "mean_ngmi",
        "mean_score",
        "mean_inference_time_ms_per_channel",
        "mean_residual_mse_improvement_percent",
    ]
    for key_vals, group in df.groupby(keys):
        row = dict(zip(keys, key_vals))
        row["n_seeds"] = int(group["seed"].nunique())
        row["n_channels_per_seed"] = int(group["n_channels"].iloc[0])
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


def _run_pcs_sweep(cfg: Dict, channel_plan: List[ChannelSpec]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    seeds = [int(s) for s in cfg["day2"]["seeds"]]
    spans_grid = [int(v) for v in cfg["day2"]["span_grid"]]
    powers = [float(v) for v in cfg["day2"]["launch_power_dbm_grid"]]
    nus = [float(v) for v in cfg["day2"]["pcs_nu_grid"]]

    for seed in seeds:
        for spans in spans_grid:
            for power in powers:
                # Uniform baseline uses nu=0 only.
                rows.extend(
                    _run_channel_set(
                        cfg, seed, spans, power, 0.0,
                        shaped=False, neural=False,
                        scenario="uniform_baseline",
                        display_name="Uniform baseline",
                        channel_plan=channel_plan,
                    )
                )

                for nu in nus:
                    rows.extend(
                        _run_channel_set(
                            cfg, seed, spans, power, nu,
                            shaped=True, neural=False,
                            scenario="pcs_only",
                            display_name="PCS only",
                            channel_plan=channel_plan,
                        )
                    )

    channel_df = pd.DataFrame(rows)
    seed_df = _seed_level(channel_df)
    ci_df = _ci(seed_df)
    return channel_df, seed_df, ci_df


def _select_neural_candidates(pcs_ci: pd.DataFrame, cfg: Dict) -> pd.DataFrame:
    pcs = pcs_ci[pcs_ci["scenario"] == "pcs_only"].copy()
    base = pcs_ci[pcs_ci["scenario"] == "uniform_baseline"].copy()

    # Keep best nu for each span/power by score, then pick top-K challenging points.
    best = (
        pcs.sort_values("mean_score_mean", ascending=False)
        .groupby(["spans", "launch_power_dbm"], as_index=False)
        .head(1)
        .copy()
    )

    # Prefer points where BER is not completely saturated and power/span are meaningful.
    best["challenge_score"] = (
        best["mean_score_mean"]
        + 0.10 * best["spans"].astype(float)
        + 0.05 * best["launch_power_dbm"].astype(float)
        - 2.0 * (best["mean_ber_mean"] <= 1e-8).astype(float)
    )

    top_k = int(cfg["day2"]["neural_candidate_top_k"])
    candidates = best.sort_values("challenge_score", ascending=False).head(top_k)
    return candidates[["spans", "launch_power_dbm", "pcs_nu"]].drop_duplicates()


def _run_neural_candidates(cfg: Dict, channel_plan: List[ChannelSpec], candidates: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    seeds = [int(s) for s in cfg["day2"]["seeds"]]

    for _, cand in candidates.iterrows():
        spans = int(cand["spans"])
        power = float(cand["launch_power_dbm"])
        nu = float(cand["pcs_nu"])

        for seed in seeds:
            rows.extend(
                _run_channel_set(
                    cfg, seed, spans, power, 0.0,
                    shaped=False, neural=True,
                    scenario="neural_only",
                    display_name="Neural NLI only",
                    channel_plan=channel_plan,
                )
            )
            rows.extend(
                _run_channel_set(
                    cfg, seed, spans, power, nu,
                    shaped=True, neural=True,
                    scenario="proposed_pcs_neural",
                    display_name="PCS + Neural NLI",
                    channel_plan=channel_plan,
                )
            )

    channel_df = pd.DataFrame(rows)
    seed_df = _seed_level(channel_df)
    ci_df = _ci(seed_df)
    return channel_df, seed_df, ci_df


def _best_operating_points(all_ci: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scenario, group in all_ci.groupby("scenario"):
        best_rate = group.sort_values("total_net_rate_tbps_mean", ascending=False).iloc[0]
        best_gsnr = group.sort_values("mean_gsnr_db_mean", ascending=False).iloc[0]
        best_score = group.sort_values("mean_score_mean", ascending=False).iloc[0]
        for label, row in [("best_rate", best_rate), ("best_gsnr", best_gsnr), ("best_score", best_score)]:
            rows.append(
                {
                    "scenario": scenario,
                    "display_name": row["display_name"],
                    "selection": label,
                    "spans": int(row["spans"]),
                    "launch_power_dbm": float(row["launch_power_dbm"]),
                    "pcs_nu": float(row["pcs_nu"]),
                    "rate_mean_tbps": float(row["total_net_rate_tbps_mean"]),
                    "rate_ci95_tbps": float(row["total_net_rate_tbps_ci95"]),
                    "gsnr_mean_db": float(row["mean_gsnr_db_mean"]),
                    "gsnr_ci95_db": float(row["mean_gsnr_db_ci95"]),
                    "ber_mean": float(row["mean_ber_mean"]),
                    "ngmi_mean": float(row["mean_ngmi_mean"]),
                    "score_mean": float(row["mean_score_mean"]),
                }
            )
    return pd.DataFrame(rows)


def _write_report(cfg: Dict, all_ci: pd.DataFrame, best_df: pd.DataFrame, figure_paths: List[Path]) -> Path:
    reports_dir = ensure_dir(cfg["output"]["reports"])
    path = reports_dir / "day2_ieee_optica_upgrade_report.md"

    proposed_rows = all_ci[all_ci["scenario"] == "proposed_pcs_neural"].copy()
    if not proposed_rows.empty:
        best_prop_score = proposed_rows.sort_values("mean_score_mean", ascending=False).iloc[0]
        best_prop_rate = proposed_rows.sort_values("total_net_rate_tbps_mean", ascending=False).iloc[0]
    else:
        best_prop_score = None
        best_prop_rate = None

    lines = []
    lines.append("# Day-2 IEEE/Optica Upgrade Report")
    lines.append("")
    lines.append("## What Day-2 adds")
    lines.append("")
    lines.append("- PCS shaping-coefficient sweep.")
    lines.append("- Span-count sweep.")
    lines.append("- Stronger nonlinear/low-SNR stress conditions.")
    lines.append("- Best-operating-point finder.")
    lines.append("- Candidate neural-compensation evaluation at promising operating points.")
    lines.append("- Paper-ready figures for rate, BER, span/power surface, and PCS tuning.")
    lines.append("")
    lines.append("## Key Day-2 findings")
    lines.append("")
    if best_prop_score is not None:
        lines.append(
            f"- Best proposed operating point by score: spans={int(best_prop_score['spans'])}, "
            f"launch power={best_prop_score['launch_power_dbm']:.1f} dBm, "
            f"PCS nu={best_prop_score['pcs_nu']:.2f}."
        )
        lines.append(
            f"- Proposed rate there: **{best_prop_score['total_net_rate_tbps_mean']:.4f} ± {best_prop_score['total_net_rate_tbps_ci95']:.4f} Tb/s**."
        )
        lines.append(
            f"- Proposed GSNR there: **{best_prop_score['mean_gsnr_db_mean']:.3f} ± {best_prop_score['mean_gsnr_db_ci95']:.3f} dB**."
        )
        lines.append(
            f"- Proposed BER there: **{best_prop_score['mean_ber_mean']:.3e}**."
        )
    if best_prop_rate is not None:
        lines.append(
            f"- Best proposed rate point: **{best_prop_rate['total_net_rate_tbps_mean']:.4f} ± {best_prop_rate['total_net_rate_tbps_ci95']:.4f} Tb/s**, "
            f"spans={int(best_prop_rate['spans'])}, power={best_prop_rate['launch_power_dbm']:.1f} dBm, nu={best_prop_rate['pcs_nu']:.2f}."
        )
    lines.append("")
    lines.append("## Best operating points table")
    lines.append("")
    lines.append(best_df.round(6).to_markdown(index=False))
    lines.append("")
    lines.append("## Submission-safe interpretation")
    lines.append("")
    lines.append(
        "Day-2 should be used to decide whether the paper can claim a genuine operating-region advantage. "
        "If PCS + Neural NLI still does not improve rate, the manuscript should be reframed as an ablation-driven "
        "validation study showing where PCS hurts, where neural compensation helps, and why tuning is necessary."
    )
    lines.append("")
    lines.append("## Generated figures")
    lines.append("")
    for p in figure_paths:
        lines.append(f"- `{p}`")
    lines.append("")
    lines.append("## Files to send back for paper rewrite")
    lines.append("")
    lines.append("- `results/reports/day2_ieee_optica_upgrade_report.md`")
    lines.append("- `results/tables/day2_best_operating_points.csv`")
    lines.append("- `results/tables/day2_all_ci.csv`")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_latex_snippet(cfg: Dict, best_df: pd.DataFrame) -> Path:
    path = ensure_dir(cfg["output"]["reports"]) / "day2_latex_results_snippet.tex"

    prop_best = best_df[(best_df["scenario"] == "proposed_pcs_neural") & (best_df["selection"] == "best_score")]
    if prop_best.empty:
        prop_text = "The neural candidate sweep did not produce a proposed-method entry. The results should be interpreted as incomplete."
    else:
        r = prop_best.iloc[0]
        prop_text = (
            f"The best proposed operating point by the combined validation score occurs at "
            f"{int(r['spans'])} spans, {r['launch_power_dbm']:.1f} dBm launch power, "
            f"and PCS shaping coefficient $\\nu={r['pcs_nu']:.2f}$. "
            f"At this point, the proposed method obtains an estimated rate of "
            f"{r['rate_mean_tbps']:.4f}$\\pm${r['rate_ci95_tbps']:.4f} Tb/s, "
            f"GSNR of {r['gsnr_mean_db']:.2f}$\\pm${r['gsnr_ci95_db']:.2f} dB, "
            f"and mean BER of {r['ber_mean']:.3e}."
        )

    tex = rf"""
% Paste this into the improved Results section after Day-2 completion.

\subsection{{PCS-Tuning and Span-Count Stress Evaluation}}
The Day-2 experiment extends the initial launch-power sweep by adding a PCS shaping-coefficient sweep and a span-count sweep. This experiment is designed to expose the operating region in which shaping and neural residual compensation are useful, rather than evaluating only a single high-SNR point.

{prop_text}

\begin{{figure}}[!t]
\centering
\includegraphics[width=\columnwidth]{{fig_day2_pcs_nu_rate.png}}
\caption{{Estimated net rate versus PCS shaping coefficient under the selected span and launch-power conditions.}}
\label{{fig:day2_nu_rate}}
\end{{figure}}

\begin{{figure}}[!t]
\centering
\includegraphics[width=\columnwidth]{{fig_day2_pcs_nu_ber.png}}
\caption{{Estimated BER versus PCS shaping coefficient on a logarithmic scale.}}
\label{{fig:day2_nu_ber}}
\end{{figure}}

\begin{{figure}}[!t]
\centering
\includegraphics[width=\columnwidth]{{fig_day2_best_nu_heatmap.png}}
\caption{{Best PCS shaping coefficient selected over span count and launch power.}}
\label{{fig:day2_best_nu}}
\end{{figure}}
"""
    path.write_text(textwrap.dedent(tex).strip() + "\n", encoding="utf-8")
    return path


def run_day2_ieee_optica_upgrade(cfg: Dict) -> Dict:
    tables_dir = ensure_dir(cfg["output"]["tables"])
    figures_dir = ensure_dir(cfg["output"]["figures"])

    channel_plan = _channel_plan(cfg)

    pcs_channel_df, pcs_seed_df, pcs_ci_df = _run_pcs_sweep(cfg, channel_plan)
    candidates = _select_neural_candidates(pcs_ci_df, cfg)
    neural_channel_df, neural_seed_df, neural_ci_df = _run_neural_candidates(cfg, channel_plan, candidates)

    all_channel_df = pd.concat([pcs_channel_df, neural_channel_df], ignore_index=True)
    all_seed_df = pd.concat([pcs_seed_df, neural_seed_df], ignore_index=True)
    all_ci_df = pd.concat([pcs_ci_df, neural_ci_df], ignore_index=True)

    best_df = _best_operating_points(all_ci_df)

    pcs_channel_df.to_csv(tables_dir / "day2_pcs_sweep_channel_metrics.csv", index=False)
    pcs_seed_df.to_csv(tables_dir / "day2_pcs_sweep_seed_summary.csv", index=False)
    pcs_ci_df.to_csv(tables_dir / "day2_pcs_sweep_ci.csv", index=False)
    neural_channel_df.to_csv(tables_dir / "day2_neural_candidate_channel_metrics.csv", index=False)
    neural_seed_df.to_csv(tables_dir / "day2_neural_candidate_seed_summary.csv", index=False)
    neural_ci_df.to_csv(tables_dir / "day2_neural_candidate_ci.csv", index=False)
    all_channel_df.to_csv(tables_dir / "day2_all_channel_metrics.csv", index=False)
    all_seed_df.to_csv(tables_dir / "day2_all_seed_summary.csv", index=False)
    all_ci_df.to_csv(tables_dir / "day2_all_ci.csv", index=False)
    best_df.to_csv(tables_dir / "day2_best_operating_points.csv", index=False)
    candidates.to_csv(tables_dir / "day2_neural_candidates.csv", index=False)

    figure_paths = []
    figure_paths.append(plot_pcs_nu_rate(pcs_ci_df, figures_dir / "fig_day2_pcs_nu_rate.png"))
    figure_paths.append(plot_pcs_nu_ber(pcs_ci_df, figures_dir / "fig_day2_pcs_nu_ber.png"))
    figure_paths.append(plot_best_nu_heatmap(pcs_ci_df, figures_dir / "fig_day2_best_nu_heatmap.png"))
    figure_paths.append(plot_span_power_rate_surface(pcs_ci_df, figures_dir / "fig_day2_span_power_rate_surface.png"))
    figure_paths.append(plot_neural_candidate_comparison(all_ci_df, figures_dir / "fig_day2_neural_candidate_comparison.png"))
    figure_paths.append(plot_day2_final_tradeoff(all_ci_df, figures_dir / "fig_day2_final_tradeoff.png"))

    report_path = _write_report(cfg, all_ci_df, best_df, figure_paths)
    latex_snippet_path = _write_latex_snippet(cfg, best_df)

    return {
        "report_path": str(report_path),
        "latex_snippet_path": str(latex_snippet_path),
        "figure_paths": [str(p) for p in figure_paths],
        "best_operating_points_csv": str(tables_dir / "day2_best_operating_points.csv"),
        "all_ci_csv": str(tables_dir / "day2_all_ci.csv"),
    }
