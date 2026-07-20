from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Dict, List
import textwrap

import numpy as np
import pandas as pd

from .baselines import linear_equalize, polynomial_nlc, dbp_inspired_compensation
from .constellation import sample_symbols, entropy_bits
from .gmi_exact import bit_metric_gmi_awgn, ber_from_decision, estimate_noise_variance_from_decisions
from .neural_nli import apply_neural_nli_mitigation
from .ssfm_lite import ssfm_lite_propagate
from .utils import ensure_dir
from .day4_plots import (
    plot_day4_gmi,
    plot_day4_ngmi,
    plot_day4_ber,
    plot_day4_gsnr,
    plot_day4_rate,
    plot_best_tradeoff,
)


def _net_rate_tbps(gmi: float, cfg: Dict, n_channels: int) -> float:
    baud = float(cfg["simulation"]["baud_rate_gbaud"]) * 1e9
    pol = int(cfg["fiber"]["polarization_modes"])
    fec_overhead = 0.20
    return float(gmi * baud * pol * n_channels / (1.0 + fec_overhead) / 1e12)


def _scenario_grid() -> List[Dict]:
    return [
        {"scenario": "uniform_raw", "display_name": "Uniform raw", "shaped": False, "nu": 0.0, "method": "raw"},
        {"scenario": "linear_eq", "display_name": "Linear EQ", "shaped": False, "nu": 0.0, "method": "linear"},
        {"scenario": "poly_nlc", "display_name": "Polynomial NLC", "shaped": False, "nu": 0.0, "method": "poly"},
        {"scenario": "dbp_like", "display_name": "DBP-like", "shaped": False, "nu": 0.0, "method": "dbp"},
        {"scenario": "neural_residual", "display_name": "Neural residual", "shaped": False, "nu": 0.0, "method": "neural"},
        {"scenario": "pcs_raw", "display_name": "PCS raw", "shaped": True, "nu": None, "method": "raw"},
        {"scenario": "pcs_neural", "display_name": "PCS + Neural", "shaped": True, "nu": None, "method": "neural"},
    ]


def _apply_method(
    method: str,
    tx_symbols: np.ndarray,
    rx_symbols: np.ndarray,
    cfg: Dict,
    mode_name: str,
) -> tuple[np.ndarray, Dict[str, float]]:
    n = len(tx_symbols)
    split = max(20, int(0.55 * n))
    tx_train = tx_symbols[:split]
    rx_train = rx_symbols[:split]

    if method == "raw":
        return rx_symbols, {"parameter_count": 0, "train_time_s": 0.0, "inference_time_s": 0.0}

    if method == "linear":
        y = linear_equalize(tx_train, rx_train, rx_symbols)
        return y, {"parameter_count": 2, "train_time_s": 0.0, "inference_time_s": 0.0}

    if method == "poly":
        import time
        t0 = time.perf_counter()
        y = polynomial_nlc(tx_train, rx_train, rx_symbols, degree=3)
        t1 = time.perf_counter()
        return y, {"parameter_count": 60, "train_time_s": t1 - t0, "inference_time_s": 0.0}

    if method == "dbp":
        y = dbp_inspired_compensation(rx_symbols)
        return y, {"parameter_count": 1, "train_time_s": 0.0, "inference_time_s": 0.0}

    if method == "neural":
        local_cfg = deepcopy(cfg)
        local_cfg["neural_nli"]["max_iter_full"] = int(cfg["day4"]["max_iter_neural"])
        res = apply_neural_nli_mitigation(
            tx_symbols=tx_symbols,
            rx_symbols=rx_symbols,
            cfg=local_cfg,
            mode="full",
            model_name=mode_name,
        )
        return res.corrected_symbols, {
            "parameter_count": res.parameter_count,
            "train_time_s": res.train_time_s,
            "inference_time_s": res.inference_time_s,
            "residual_mse_improvement_percent": 100.0 * (1.0 - res.residual_mse_after / max(res.residual_mse_before, 1e-15)),
        }

    raise ValueError(f"Unknown method: {method}")


def _run_one(
    cfg: Dict,
    seed: int,
    spans: int,
    power: float,
    band: str,
    nu: float,
    scenario: Dict,
) -> Dict:
    rng = np.random.default_rng(seed)
    n_sym = int(cfg["day4"]["symbols_per_channel"])
    shaped = bool(scenario["shaped"])
    effective_nu = float(nu if scenario["nu"] is None else scenario["nu"])

    tx, tx_idx, priors = sample_symbols(
        n_symbols=n_sym,
        shaped=shaped,
        nu=effective_nu,
        rng=rng,
    )

    local_cfg = deepcopy(cfg)
    local_cfg["simulation"]["spans"] = int(spans)
    local_cfg["pcs"]["shaping_nu"] = effective_nu

    rx, ssfm_stats = ssfm_lite_propagate(
        tx_symbols=tx,
        launch_power_dbm=power,
        spans=spans,
        band_cfg=cfg["bands"][band],
        cfg=local_cfg,
        rng=rng,
    )

    corrected, method_stats = _apply_method(
        scenario["method"],
        tx_symbols=tx,
        rx_symbols=rx,
        cfg=local_cfg,
        mode_name=f"day4_seed{seed}_sp{spans}_p{power}_b{band}_nu{effective_nu}_{scenario['scenario']}",
    )

    noise_var = estimate_noise_variance_from_decisions(corrected, tx)
    gmi, ngmi = bit_metric_gmi_awgn(
        tx_indices=tx_idx,
        rx_symbols=corrected,
        noise_var=max(noise_var, float(cfg["day4"]["llr_noise_floor"])),
        priors=priors,
        max_samples=int(cfg["day4"]["gmi_monte_carlo_limit"]),
    )
    ber = ber_from_decision(tx_idx, corrected)
    gsnr_db = 10.0 * np.log10(float(np.mean(np.abs(tx) ** 2)) / max(float(np.mean(np.abs(corrected - tx) ** 2)), 1e-15))
    rate = _net_rate_tbps(gmi, local_cfg, n_channels=1)

    score = (
        float(cfg["day4"]["score_rate_weight"]) * rate
        + float(cfg["day4"]["score_gsnr_weight"]) * gsnr_db
        - float(cfg["day4"]["score_ber_penalty"]) * ber
    )

    return {
        "seed": seed,
        "spans": int(spans),
        "launch_power_dbm": float(power),
        "band": band,
        "pcs_nu": effective_nu,
        "scenario": scenario["scenario"],
        "display_name": scenario["display_name"],
        "method": scenario["method"],
        "shaped": shaped,
        "gmi": float(gmi),
        "ngmi": float(ngmi),
        "ber": float(ber),
        "gsnr_db": float(gsnr_db),
        "rate_tbps": float(rate),
        "entropy_bits_per_symbol": float(entropy_bits(priors)),
        "score": float(score),
        **ssfm_stats,
        **method_stats,
    }


def _ci(seed_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    keys = ["spans", "launch_power_dbm", "band", "pcs_nu", "scenario", "display_name"]
    metrics = ["gmi", "ngmi", "ber", "gsnr_db", "rate_tbps", "score"]
    for key_vals, group in seed_df.groupby(keys):
        row = dict(zip(keys, key_vals))
        row["n_seeds"] = int(group["seed"].nunique())
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


def _best_points(ci_df: pd.DataFrame) -> pd.DataFrame:
    return (
        ci_df.sort_values("score_mean", ascending=False)
        .groupby("scenario", as_index=False)
        .head(1)
        .sort_values("score_mean", ascending=False)
    )


def _write_report(cfg: Dict, ci_df: pd.DataFrame, best_df: pd.DataFrame, figure_paths: List[Path]) -> Path:
    path = ensure_dir(cfg["output"]["reports"]) / "day4_optica_scientific_upgrade_report.md"
    best_overall = best_df.iloc[0]
    lines = []
    lines.append("# Day-4 Optica Scientific Upgrade Report")
    lines.append("")
    lines.append("## What Day-4 adds")
    lines.append("")
    lines.append("- SSFM-lite split-step propagation instead of only analytical noise screening.")
    lines.append("- Bit-metric AWGN-likelihood GMI/NGMI estimate instead of Shannon-like proxy.")
    lines.append("- Stronger baselines: Linear EQ, Polynomial NLC, DBP-like compensation, Neural residual compensation.")
    lines.append("- Multi-seed confidence intervals.")
    lines.append("")
    lines.append("## Best overall operating point")
    lines.append("")
    lines.append(f"- Scenario: **{best_overall['display_name']}**")
    lines.append(f"- Spans: **{int(best_overall['spans'])}**")
    lines.append(f"- Launch power: **{best_overall['launch_power_dbm']:.1f} dBm/channel**")
    lines.append(f"- Band: **{best_overall['band']}**")
    lines.append(f"- PCS nu: **{best_overall['pcs_nu']:.2f}**")
    lines.append(f"- GMI: **{best_overall['gmi_mean']:.3f} ± {best_overall['gmi_ci95']:.3f} bits/symbol**")
    lines.append(f"- NGMI: **{best_overall['ngmi_mean']:.3f} ± {best_overall['ngmi_ci95']:.3f}**")
    lines.append(f"- BER: **{best_overall['ber_mean']:.3e}**")
    lines.append(f"- GSNR: **{best_overall['gsnr_db_mean']:.3f} ± {best_overall['gsnr_db_ci95']:.3f} dB**")
    lines.append(f"- Estimated rate: **{best_overall['rate_tbps_mean']:.4f} ± {best_overall['rate_tbps_ci95']:.4f} Tb/s per evaluated channel**")
    lines.append("")
    lines.append("## Best point by scenario")
    lines.append("")
    lines.append(best_df.round(6).to_markdown(index=False))
    lines.append("")
    lines.append("## Generated figures")
    lines.append("")
    for p in figure_paths:
        lines.append(f"- `{p}`")
    lines.append("")
    lines.append("## Honest Optica-readiness interpretation")
    lines.append("")
    lines.append(
        "If Neural residual or DBP-like compensation improves exact bit-metric GMI or NGMI over raw/linear baselines, the paper can be reframed around nonlinear-residual compensation. "
        "If PCS still selects nu=0 or loses rate, do not claim PCS gain. "
        "A high-level Optica regular submission still benefits from a fuller SSFM implementation with pulse shaping, WDM coupling, more seeds, and larger symbol counts."
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_latex(cfg: Dict, best_df: pd.DataFrame) -> Path:
    path = ensure_dir(cfg["output"]["reports"]) / "day4_latex_results_snippet.tex"
    best_overall = best_df.iloc[0]
    tex = f"""
\\subsection{{SSFM-Lite Validation and Bit-Metric GMI}}
Day-4 replaces the earlier analytical screening-only model with an SSFM-lite propagation model and evaluates bit-metric AWGN-likelihood GMI/NGMI. The best operating point is obtained by {best_overall['display_name']} at {int(best_overall['spans'])} spans, {best_overall['launch_power_dbm']:.1f} dBm/channel, band {best_overall['band']}, and $\\nu={best_overall['pcs_nu']:.2f}$. The method obtains GMI={best_overall['gmi_mean']:.3f}$\\pm${best_overall['gmi_ci95']:.3f} bits/symbol, NGMI={best_overall['ngmi_mean']:.3f}$\\pm${best_overall['ngmi_ci95']:.3f}, BER={best_overall['ber_mean']:.3e}, and GSNR={best_overall['gsnr_db_mean']:.2f}$\\pm${best_overall['gsnr_db_ci95']:.2f} dB.
"""
    path.write_text(textwrap.dedent(tex).strip() + "\n", encoding="utf-8")
    return path


def run_day4_optica_scientific_upgrade(cfg: Dict) -> Dict:
    tables_dir = ensure_dir(cfg["output"]["tables"])
    figures_dir = ensure_dir(cfg["output"]["figures"])

    seeds = [int(s) for s in cfg["day4"]["seeds"]]
    spans_grid = [int(v) for v in cfg["day4"]["span_grid"]]
    powers = [float(v) for v in cfg["day4"]["launch_power_dbm_grid"]]
    nus = [float(v) for v in cfg["day4"]["pcs_nu_grid"]]
    bands = list(cfg["day4"]["bands_to_run"])

    rows = []
    scenarios = _scenario_grid()

    for seed in seeds:
        for spans in spans_grid:
            for power in powers:
                for band in bands:
                    for scenario in scenarios:
                        if scenario["nu"] is None:
                            for nu in nus:
                                rows.append(_run_one(cfg, seed, spans, power, band, nu, scenario))
                        else:
                            rows.append(_run_one(cfg, seed, spans, power, band, float(scenario["nu"]), scenario))

    raw_df = pd.DataFrame(rows)
    ci_df = _ci(raw_df)
    best_df = _best_points(ci_df)

    raw_csv = tables_dir / "day4_raw_metrics.csv"
    ci_csv = tables_dir / "day4_ci_metrics.csv"
    best_csv = tables_dir / "day4_best_points.csv"

    raw_df.to_csv(raw_csv, index=False)
    ci_df.to_csv(ci_csv, index=False)
    best_df.to_csv(best_csv, index=False)

    # Plot one representative span/band/nu slice to keep figures readable.
    best_overall = best_df.iloc[0]
    plot_df = ci_df[
        (ci_df["spans"] == best_overall["spans"])
        & (ci_df["band"] == best_overall["band"])
        & (ci_df["pcs_nu"] == best_overall["pcs_nu"])
    ].copy()

    figure_paths = [
        plot_day4_gmi(plot_df, figures_dir / "fig_day4_gmi_vs_power.png"),
        plot_day4_ngmi(plot_df, figures_dir / "fig_day4_ngmi_vs_power.png"),
        plot_day4_ber(plot_df, figures_dir / "fig_day4_ber_vs_power.png"),
        plot_day4_gsnr(plot_df, figures_dir / "fig_day4_gsnr_vs_power.png"),
        plot_day4_rate(plot_df, figures_dir / "fig_day4_rate_vs_power.png"),
        plot_best_tradeoff(best_df, figures_dir / "fig_day4_best_tradeoff.png"),
    ]

    report_path = _write_report(cfg, ci_df, best_df, figure_paths)
    latex_path = _write_latex(cfg, best_df)

    return {
        "raw_csv": str(raw_csv),
        "ci_csv": str(ci_csv),
        "best_csv": str(best_csv),
        "report_path": str(report_path),
        "latex_snippet_path": str(latex_path),
        "figure_paths": [str(p) for p in figure_paths],
    }
