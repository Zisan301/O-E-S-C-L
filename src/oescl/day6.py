from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple
import textwrap

import numpy as np
import pandas as pd

from .constellation import sample_symbols
from .day5_waveform import waveform_ssfm_channel
from .day5_equalizers import memory_mlp_equalizer
from .gmi_exact import (
    bit_metric_gmi_awgn,
    ber_from_decision,
    estimate_noise_variance_from_decisions,
)
from .utils import ensure_dir
from .day6_plots import plot_day6_pcs_metric, plot_day6_gain, plot_day6_constellation


def _net_rate(gmi: float, cfg: Dict) -> float:
    return float(
        gmi
        * float(cfg["simulation"]["baud_rate_gbaud"])
        * 1e9
        * int(cfg["fiber"]["polarization_modes"])
        / 1.20
        / 1e12
    )


def _metrics(tx: np.ndarray, tx_idx: np.ndarray, rx: np.ndarray, priors: np.ndarray, cfg: Dict) -> Dict[str, float]:
    noise_var = max(
        estimate_noise_variance_from_decisions(rx, tx),
        float(cfg["day5"]["llr_noise_floor"]),
    )
    gmi, ngmi = bit_metric_gmi_awgn(
        tx_indices=tx_idx,
        rx_symbols=rx,
        noise_var=noise_var,
        priors=priors,
        max_samples=int(cfg["day5"]["gmi_monte_carlo_limit"]),
    )
    ber = ber_from_decision(tx_idx, rx)
    gsnr = 10.0 * np.log10(float(np.mean(np.abs(tx) ** 2)) / max(float(np.mean(np.abs(rx - tx) ** 2)), 1e-15))
    return {
        "gmi": float(gmi),
        "ngmi": float(ngmi),
        "ber": float(ber),
        "gsnr_db": float(gsnr),
        "rate_tbps": _net_rate(gmi, cfg),
    }


def _ci(df: pd.DataFrame, keys: List[str]) -> pd.DataFrame:
    rows = []
    metrics = [
        "gmi", "ngmi", "ber", "gsnr_db", "rate_tbps",
        "train_time_s", "inference_time_s", "parameter_count",
    ]
    for key_vals, group in df.groupby(keys):
        if not isinstance(key_vals, tuple):
            key_vals = (key_vals,)
        row = dict(zip(keys, key_vals))
        row["n_seeds"] = int(group["seed"].nunique()) if "seed" in group else len(group)
        for metric in metrics:
            if metric not in group:
                continue
            vals = group[metric].astype(float).to_numpy()
            mean = float(np.mean(vals))
            std = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
            ci95 = float(1.96 * std / np.sqrt(max(len(vals), 1)))
            row[f"{metric}_mean"] = mean
            row[f"{metric}_std"] = std
            row[f"{metric}_ci95"] = ci95
        rows.append(row)
    return pd.DataFrame(rows)


def _run_one(seed: int, nu: float, cfg: Dict, shaped: bool, memory_check: bool) -> List[Dict]:
    day6 = cfg["day6"]
    band = str(day6["band"])
    spans = int(day6["spans"])
    power = float(day6["launch_power_dbm"])
    stress = dict(day6["stress"])

    rng = np.random.default_rng(int(day6["seed"]) + seed * 100000 + int((nu + 10.0) * 10000))
    tx, tx_idx, priors = sample_symbols(int(day6["symbols"]), shaped=shaped, nu=float(nu), rng=rng)

    result = waveform_ssfm_channel(
        tx_symbols=tx,
        tx_indices=tx_idx,
        priors=priors,
        cfg=cfg,
        band=band,
        spans=spans,
        launch_power_dbm=power,
        stress=stress,
        rng=rng,
    )

    txa = result.tx_symbols_aligned
    idxa = result.tx_indices_aligned
    rx = result.rx_symbols

    rows = []
    display = "PCS raw" if shaped else "Uniform raw"
    scenario = "pcs_raw" if shaped else "uniform_raw"
    m = _metrics(txa, idxa, rx, result.priors, cfg)
    rows.append({
        "seed": seed,
        "pcs_nu": float(nu),
        "shaped": bool(shaped),
        "display_name": display,
        "scenario": scenario,
        "band": band,
        "spans": spans,
        "launch_power_dbm": power,
        "stress_name": stress["name"],
        **m,
        "train_time_s": 0.0,
        "inference_time_s": 0.0,
        "parameter_count": 0,
    })

    if memory_check:
        mem = memory_mlp_equalizer(txa, rx, cfg, model_name=f"day6_seed{seed}_nu{nu}_memory")
        m2 = _metrics(txa, idxa, mem.corrected_symbols, result.priors, cfg)
        rows.append({
            "seed": seed,
            "pcs_nu": float(nu),
            "shaped": bool(shaped),
            "display_name": "PCS + Memory neural" if shaped else "Uniform + Memory neural",
            "scenario": "pcs_memory_neural" if shaped else "uniform_memory_neural",
            "band": band,
            "spans": spans,
            "launch_power_dbm": power,
            "stress_name": stress["name"],
            **m2,
            "train_time_s": float(mem.train_time_s),
            "inference_time_s": float(mem.inference_time_s),
            "parameter_count": int(mem.parameter_count),
        })

    return rows


def _compute_paired_gains(raw_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    uniform = raw_df[(raw_df["scenario"] == "uniform_raw") & (raw_df["pcs_nu"] == 0.0)]
    for nu in sorted(v for v in raw_df["pcs_nu"].unique() if float(v) > 0):
        pcs = raw_df[(raw_df["scenario"] == "pcs_raw") & (raw_df["pcs_nu"] == float(nu))]
        merged = pcs.merge(
            uniform[["seed", "gmi", "ngmi", "ber", "rate_tbps", "gsnr_db"]],
            on="seed",
            suffixes=("_pcs", "_uniform"),
        )
        if merged.empty:
            continue
        gmi_gain = merged["gmi_pcs"] - merged["gmi_uniform"]
        ngmi_gain = merged["ngmi_pcs"] - merged["ngmi_uniform"]
        rate_gain = merged["rate_tbps_pcs"] - merged["rate_tbps_uniform"]
        ber_delta = merged["ber_pcs"] - merged["ber_uniform"]
        gsnr_delta = merged["gsnr_db_pcs"] - merged["gsnr_db_uniform"]

        def ci95(x):
            x = np.asarray(x, dtype=float)
            return float(1.96 * np.std(x, ddof=1) / np.sqrt(max(len(x), 1))) if len(x) > 1 else 0.0

        rows.append({
            "pcs_nu": float(nu),
            "n_pairs": int(len(merged)),
            "gmi_gain_mean": float(np.mean(gmi_gain)),
            "gmi_gain_std": float(np.std(gmi_gain, ddof=1)) if len(gmi_gain) > 1 else 0.0,
            "gmi_gain_ci95": ci95(gmi_gain),
            "ngmi_gain_mean": float(np.mean(ngmi_gain)),
            "ngmi_gain_std": float(np.std(ngmi_gain, ddof=1)) if len(ngmi_gain) > 1 else 0.0,
            "ngmi_gain_ci95": ci95(ngmi_gain),
            "rate_gain_mean": float(np.mean(rate_gain)),
            "rate_gain_std": float(np.std(rate_gain, ddof=1)) if len(rate_gain) > 1 else 0.0,
            "rate_gain_ci95": ci95(rate_gain),
            "ber_delta_mean": float(np.mean(ber_delta)),
            "ber_delta_ci95": ci95(ber_delta),
            "gsnr_delta_mean": float(np.mean(gsnr_delta)),
            "gsnr_delta_ci95": ci95(gsnr_delta),
        })
    return pd.DataFrame(rows)


def _non_saturated(row: pd.Series, cfg: Dict) -> bool:
    d6 = cfg["day6"]
    return bool(
        float(d6["target_gmi_min"]) <= float(row["gmi_mean"]) <= float(d6["target_gmi_max"])
        and float(d6["target_ngmi_min"]) <= float(row["ngmi_mean"]) <= float(d6["target_ngmi_max"])
        and float(d6["target_ber_min"]) <= max(float(row["ber_mean"]), 1e-12) <= float(d6["target_ber_max"])
    )


def _acceptance(ci_df: pd.DataFrame, gain_df: pd.DataFrame, cfg: Dict) -> Dict:
    d6 = cfg["day6"]
    result = {
        "passes_day6_pcs_confirmation": False,
        "recommended_claim": "Day-6 PCS confirmation failed. Do not use the Day-5B PCS claim as a high-level Optica claim yet.",
        "best_pcs_nu": None,
        "details": {},
    }

    if gain_df.empty:
        result["details"]["error"] = "No paired PCS gains were computed."
        return result

    best_gain = gain_df.sort_values("gmi_gain_mean", ascending=False).iloc[0]
    best_nu = float(best_gain["pcs_nu"])
    best_pcs = ci_df[(ci_df["scenario"] == "pcs_raw") & (ci_df["pcs_nu"] == best_nu)].iloc[0]
    uniform = ci_df[(ci_df["scenario"] == "uniform_raw") & (ci_df["pcs_nu"] == 0.0)].iloc[0]

    passes = (
        float(best_gain["gmi_gain_mean"]) >= float(d6["min_gmi_gain"])
        and float(best_gain["ngmi_gain_mean"]) >= float(d6["min_ngmi_gain"])
        and float(best_gain["rate_gain_mean"]) >= float(d6["min_rate_gain_tbps_per_channel"])
        and float(best_gain["gmi_gain_mean"]) > float(best_gain["gmi_gain_ci95"])
        and float(best_gain["ngmi_gain_mean"]) > float(best_gain["ngmi_gain_ci95"])
        and float(best_gain["rate_gain_mean"]) > float(best_gain["rate_gain_ci95"])
        and float(best_pcs["ber_mean"]) <= float(d6["max_ber"])
        and (not bool(d6["require_non_saturated"]) or (_non_saturated(best_pcs, cfg) and _non_saturated(uniform, cfg)))
    )

    result["passes_day6_pcs_confirmation"] = bool(passes)
    result["best_pcs_nu"] = best_nu
    result["details"]["best_gain"] = best_gain.to_dict()
    result["details"]["best_pcs"] = best_pcs.to_dict()
    result["details"]["uniform_reference"] = uniform.to_dict()
    result["details"]["non_saturated"] = bool(_non_saturated(best_pcs, cfg) and _non_saturated(uniform, cfg))

    if passes:
        result["recommended_claim"] = (
            "Day-6 confirmed nonzero PCS gain at the focused waveform operating point. "
            "Claim PCS-centered operating-region improvement, not neural superiority."
        )

    return result


def _write_reports(cfg, raw_df, ci_df, gain_df, acceptance, figure_paths) -> Tuple[Path, Path, Path]:
    reports_dir = ensure_dir(cfg["output"]["reports"])

    report = reports_dir / "day6_pcs_confirmation_report.md"
    gate = reports_dir / "day6_pcs_acceptance_gate_report.md"
    latex = reports_dir / "day6_latex_results_snippet.tex"

    d6 = cfg["day6"]
    lines = []
    lines.append("# Day-6 PCS Confirmation Report")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append("Day-6 confirms the Day-5B strict-gate PCS finding using a focused matched comparison with more seeds and more symbols.")
    lines.append("")
    lines.append("## Locked operating point")
    lines.append("")
    lines.append(pd.DataFrame([{
        "band": d6["band"],
        "spans": d6["spans"],
        "launch_power_dbm": d6["launch_power_dbm"],
        "stress_name": d6["stress"]["name"],
        "symbols": d6["symbols"],
        "n_seeds": len(d6["seeds"]),
    }]).to_markdown(index=False))
    lines.append("")
    lines.append("## Raw PCS vs uniform CI")
    lines.append("")
    lines.append(ci_df[ci_df["scenario"].isin(["uniform_raw", "pcs_raw"])].round(6).to_markdown(index=False))
    lines.append("")
    lines.append("## Paired PCS gains")
    lines.append("")
    lines.append(gain_df.round(6).to_markdown(index=False))
    lines.append("")
    lines.append("## Generated figures")
    for p in figure_paths:
        lines.append(f"- `{p}`")
    report.write_text("\n".join(lines), encoding="utf-8")

    lines = []
    lines.append("# Day-6 PCS Acceptance Gate Report")
    lines.append("")
    lines.append(f"**Passes Day-6 PCS confirmation:** {acceptance['passes_day6_pcs_confirmation']}")
    lines.append("")
    lines.append(f"**Recommended claim:** {acceptance['recommended_claim']}")
    lines.append("")
    lines.append(f"**Best PCS nu:** {acceptance['best_pcs_nu']}")
    lines.append("")
    lines.append("## Details")
    lines.append("")
    for k, v in acceptance["details"].items():
        lines.append(f"### {k}")
        lines.append("")
        if isinstance(v, dict):
            try:
                lines.append(pd.DataFrame([v]).round(6).to_markdown(index=False))
            except Exception:
                lines.append(str(v))
        else:
            lines.append(str(v))
        lines.append("")
    gate.write_text("\n".join(lines), encoding="utf-8")

    if acceptance["passes_day6_pcs_confirmation"]:
        bg = acceptance["details"]["best_gain"]
        bp = acceptance["details"]["best_pcs"]
        uni = acceptance["details"]["uniform_reference"]
        latex_body = f"""
        \\subsection{{Day-6 Focused PCS Confirmation}}
        A focused Day-6 confirmation was performed at the Day-5B operating region: C band, {int(d6['spans'])} spans, {float(d6['launch_power_dbm']):.1f} dBm/channel, and evidence stress. Using {len(d6['seeds'])} seeds and {int(d6['symbols'])} symbols/seed, the best nonzero PCS coefficient was $\\nu={float(acceptance['best_pcs_nu']):.2f}$. Compared with uniform signaling, PCS improved bit-metric GMI by {float(bg['gmi_gain_mean']):.4f}$\\pm${float(bg['gmi_gain_ci95']):.4f} bits/symbol and estimated rate by {float(bg['rate_gain_mean']):.4f}$\\pm${float(bg['rate_gain_ci95']):.4f} Tb/s/channel. The corresponding PCS operating point achieved GMI={float(bp['gmi_mean']):.4f}, NGMI={float(bp['ngmi_mean']):.4f}, and BER={float(bp['ber_mean']):.3e}; the uniform reference achieved GMI={float(uni['gmi_mean']):.4f}, NGMI={float(uni['ngmi_mean']):.4f}, and BER={float(uni['ber_mean']):.3e}. This supports a PCS-centered operating-region claim; neural superiority is not claimed.
        """
    else:
        latex_body = """
        \\subsection{Day-6 Focused PCS Confirmation}
        The focused Day-6 confirmation did not pass the strict PCS acceptance gate. Therefore, the paper must not claim high-level PCS performance superiority. The result should be framed as validation evidence and used to motivate further waveform-level investigation.
        """
    latex.write_text(textwrap.dedent(latex_body).strip() + "\n", encoding="utf-8")

    return report, gate, latex


def run_day6_pcs_confirmation(cfg: Dict) -> Dict:
    tables_dir = ensure_dir(cfg["output"]["tables"])
    figures_dir = ensure_dir(cfg["output"]["figures"])

    d6 = cfg["day6"]
    rows = []
    for seed in [int(s) for s in d6["seeds"]]:
        for nu in [float(v) for v in d6["pcs_nu_grid"]]:
            shaped = nu > 0
            memory_check = bool(d6["run_memory_neural_check"]) and (nu in [float(v) for v in d6["memory_neural_nu_subset"]])
            rows.extend(_run_one(seed=seed, nu=nu, cfg=cfg, shaped=shaped, memory_check=memory_check))

    raw_df = pd.DataFrame(rows)
    ci_df = _ci(raw_df, ["pcs_nu", "shaped", "display_name", "scenario", "band", "spans", "launch_power_dbm", "stress_name"])
    gain_df = _compute_paired_gains(raw_df)
    acceptance = _acceptance(ci_df, gain_df, cfg)

    raw_df.to_csv(tables_dir / "day6_raw_metrics.csv", index=False)
    ci_df.to_csv(tables_dir / "day6_ci_metrics.csv", index=False)
    gain_df.to_csv(tables_dir / "day6_paired_pcs_gains.csv", index=False)
    pd.DataFrame([{
        "passes_day6_pcs_confirmation": acceptance["passes_day6_pcs_confirmation"],
        "best_pcs_nu": acceptance["best_pcs_nu"],
        "recommended_claim": acceptance["recommended_claim"],
    }]).to_csv(tables_dir / "day6_acceptance_summary.csv", index=False)

    figure_paths = []
    raw_ci = ci_df[ci_df["scenario"].isin(["uniform_raw", "pcs_raw"])].copy()
    figure_paths.append(plot_day6_pcs_metric(raw_ci, "gmi", "GMI (bits/symbol)", "Day-6 focused PCS confirmation: GMI", figures_dir / "fig_day6_pcs_gmi.png"))
    figure_paths.append(plot_day6_pcs_metric(raw_ci, "ngmi", "NGMI", "Day-6 focused PCS confirmation: NGMI", figures_dir / "fig_day6_pcs_ngmi.png"))
    figure_paths.append(plot_day6_pcs_metric(raw_ci, "ber", "BER", "Day-6 focused PCS confirmation: BER", figures_dir / "fig_day6_pcs_ber.png", logy=True))
    figure_paths.append(plot_day6_gain(gain_df, figures_dir / "fig_day6_pcs_gmi_gain.png"))

    # Constellation demo using seed 1 and best nu if available.
    best_nu = acceptance["best_pcs_nu"] if acceptance["best_pcs_nu"] is not None else 0.24
    demo_seed = int(d6["seeds"][0])
    rng_u = np.random.default_rng(int(d6["seed"]) + demo_seed * 100000)
    tx_u, idx_u, pri_u = sample_symbols(int(d6["symbols"]), shaped=False, nu=0.0, rng=rng_u)
    res_u = waveform_ssfm_channel(tx_u, idx_u, pri_u, cfg, d6["band"], int(d6["spans"]), float(d6["launch_power_dbm"]), dict(d6["stress"]), rng_u)

    rng_p = np.random.default_rng(int(d6["seed"]) + demo_seed * 100000 + int((float(best_nu) + 10.0) * 10000))
    tx_p, idx_p, pri_p = sample_symbols(int(d6["symbols"]), shaped=True, nu=float(best_nu), rng=rng_p)
    res_p = waveform_ssfm_channel(tx_p, idx_p, pri_p, cfg, d6["band"], int(d6["spans"]), float(d6["launch_power_dbm"]), dict(d6["stress"]), rng_p)

    figure_paths.append(plot_day6_constellation(
        res_u.tx_symbols_aligned,
        res_u.rx_symbols,
        res_p.rx_symbols,
        figures_dir / "fig_day6_constellation_uniform_vs_pcs.png",
    ))

    report, gate, latex = _write_reports(cfg, raw_df, ci_df, gain_df, acceptance, figure_paths)

    return {
        "report_path": str(report),
        "acceptance_report_path": str(gate),
        "latex_snippet_path": str(latex),
        "figure_paths": [str(p) for p in figure_paths],
        "raw_csv": str(tables_dir / "day6_raw_metrics.csv"),
        "ci_csv": str(tables_dir / "day6_ci_metrics.csv"),
        "gain_csv": str(tables_dir / "day6_paired_pcs_gains.csv"),
        "acceptance_csv": str(tables_dir / "day6_acceptance_summary.csv"),
    }
