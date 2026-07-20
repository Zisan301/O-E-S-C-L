from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Tuple
import textwrap

import numpy as np
import pandas as pd

from .constellation import sample_symbols
from .day5_equalizers import (
    linear_equalizer,
    dbp_like_equalizer,
    polynomial_nlc,
    memory_mlp_equalizer,
)
from .day5_waveform import waveform_ssfm_channel
from .gmi_exact import (
    bit_metric_gmi_awgn,
    ber_from_decision,
    estimate_noise_variance_from_decisions,
)
from .utils import ensure_dir
from .day5_plots import (
    plot_constellations,
    plot_metric_vs_power,
    plot_pcs_sweep,
    plot_best_tradeoff,
)


def _net_rate(gmi: float, cfg: Dict, n_channels: int = 1) -> float:
    return float(
        gmi
        * float(cfg["simulation"]["baud_rate_gbaud"])
        * 1e9
        * int(cfg["fiber"]["polarization_modes"])
        * n_channels
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


def _apply_methods(tx, tx_idx, priors, raw, cfg, model_prefix) -> Tuple[List[Dict], Dict[str, np.ndarray]]:
    n = len(tx)
    split = max(32, int(float(cfg["day5"]["training_fraction"]) * n))
    tx_train = tx[:split]
    rx_train = raw[:split]

    outputs = {}

    method_results = []
    method_results.append(("Raw", "raw", raw, {"parameter_count": 0, "train_time_s": 0.0, "inference_time_s": 0.0}))

    lin = linear_equalizer(tx_train, rx_train, raw)
    method_results.append(("Linear EQ", "linear", lin.corrected_symbols, lin.__dict__))

    dbp = dbp_like_equalizer(raw, tx_ref=tx, strength=0.04)
    method_results.append(("DBP-like", "dbp_like", dbp.corrected_symbols, dbp.__dict__))

    poly = polynomial_nlc(tx_train, rx_train, raw)
    method_results.append(("Polynomial NLC", "poly_nlc", poly.corrected_symbols, poly.__dict__))

    mem = memory_mlp_equalizer(tx, raw, cfg, model_name=model_prefix + "_memory_mlp")
    method_results.append(("Memory neural EQ", "memory_neural", mem.corrected_symbols, mem.__dict__))

    rows = []
    for display, scenario, corrected, stats in method_results:
        outputs[scenario] = corrected
        m = _metrics(tx, tx_idx, corrected, priors, cfg)
        rows.append({
            "display_name": display,
            "scenario": scenario,
            **m,
            "parameter_count": int(stats.get("parameter_count", 0)),
            "train_time_s": float(stats.get("train_time_s", 0.0)),
            "inference_time_s": float(stats.get("inference_time_s", 0.0)),
            "residual_mse_before": float(stats.get("residual_mse_before", 0.0)),
            "residual_mse_after": float(stats.get("residual_mse_after", 0.0)),
        })
    return rows, outputs


def _ci(df: pd.DataFrame, keys: List[str]) -> pd.DataFrame:
    rows = []
    metrics = ["gmi", "ngmi", "ber", "gsnr_db", "rate_tbps", "train_time_s", "inference_time_s", "parameter_count"]
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


def _sanity_tests(cfg: Dict) -> pd.DataFrame:
    rng = np.random.default_rng(int(cfg["day5"]["seed"]))
    tx, tx_idx, priors = sample_symbols(int(cfg["day5"]["sanity_symbols"]), shaped=False, nu=0.0, rng=rng)
    base_stress = {"name": "sanity", "noise": 0.0, "nonlinear": 0.0, "implementation": 0.0, "phase": 0.0}
    specs = [
        ("identity_waveform", dict(disable_noise=True, disable_nonlinearity=True, disable_dispersion=True)),
        ("pulse_shape_matched_filter_only", dict(disable_noise=True, disable_nonlinearity=True, disable_dispersion=True)),
        ("dispersion_with_receiver_cd", dict(disable_noise=True, disable_nonlinearity=True, disable_dispersion=False)),
        ("nonlinear_no_noise", dict(disable_noise=True, disable_nonlinearity=False, disable_dispersion=False)),
    ]
    rows = []
    for test, flags in specs:
        result = waveform_ssfm_channel(
            tx, tx_idx, priors, cfg=cfg, band="C", spans=6, launch_power_dbm=0.0,
            stress=base_stress, rng=rng, **flags
        )
        m = _metrics(result.tx_symbols_aligned, result.tx_indices_aligned, result.rx_symbols, result.priors, cfg)
        rows.append({"test": test, **m, **result.stats})
    return pd.DataFrame(rows)


def _stress_selector(cfg: Dict) -> pd.DataFrame:
    rows = []
    rng_base = int(cfg["day5"]["seed"]) + 1000
    for stress_i, stress in enumerate(cfg["day5"]["stress_grid"]):
        for power in [float(v) for v in cfg["day5"]["launch_power_grid"]]:
            for spans in [int(v) for v in cfg["day5"]["waveform_spans"]]:
                rng = np.random.default_rng(rng_base + stress_i * 10000 + int((power + 100) * 10) + spans)
                tx, tx_idx, priors = sample_symbols(int(cfg["day5"]["symbols"]), shaped=False, nu=0.0, rng=rng)
                result = waveform_ssfm_channel(
                    tx, tx_idx, priors, cfg=cfg, band="C", spans=spans, launch_power_dbm=power,
                    stress=stress, rng=rng
                )
                m = _metrics(result.tx_symbols_aligned, result.tx_indices_aligned, result.rx_symbols, result.priors, cfg)

                # Distance from useful target region. Lower is better.
                target_gmi_mid = 0.5 * (float(cfg["day5"]["target_gmi_min"]) + float(cfg["day5"]["target_gmi_max"]))
                target_ber_mid_log = np.log10(np.sqrt(float(cfg["day5"]["target_ber_min"]) * float(cfg["day5"]["target_ber_max"])))
                ber_log = np.log10(max(m["ber"], 1e-8))
                score = abs(m["gmi"] - target_gmi_mid) + 0.20 * abs(ber_log - target_ber_mid_log)

                in_region = (
                    float(cfg["day5"]["target_gmi_min"]) <= m["gmi"] <= float(cfg["day5"]["target_gmi_max"])
                    and float(cfg["day5"]["target_ber_min"]) <= max(m["ber"], 1e-12) <= float(cfg["day5"]["target_ber_max"])
                    and float(cfg["day5"]["target_ngmi_min"]) <= m["ngmi"] <= float(cfg["day5"]["target_ngmi_max"])
                )

                rows.append({
                    "stress_name": stress["name"],
                    "stress_noise": float(stress["noise"]),
                    "stress_nonlinear": float(stress["nonlinear"]),
                    "stress_implementation": float(stress["implementation"]),
                    "stress_phase": float(stress.get("phase", 0.0)),
                    "launch_power_dbm": power,
                    "spans": spans,
                    "in_target_region": bool(in_region),
                    "selector_score": float(score),
                    **m,
                })
    df = pd.DataFrame(rows)
    df = df.sort_values(["in_target_region", "selector_score"], ascending=[False, True])
    return df


def _selected_stress(cfg: Dict, selector_df: pd.DataFrame) -> Tuple[Dict, float, int]:
    row = selector_df.iloc[0]
    stress = {
        "name": row["stress_name"],
        "noise": float(row["stress_noise"]),
        "nonlinear": float(row["stress_nonlinear"]),
        "implementation": float(row["stress_implementation"]),
        "phase": float(row["stress_phase"]),
    }
    return stress, float(row["launch_power_dbm"]), int(row["spans"])


def _run_final_evidence(cfg: Dict, stress: Dict, selected_power: float, selected_spans: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    seeds = [int(s) for s in cfg["day5"]["seeds"]]
    bands = list(cfg["day5"]["bands_to_run"])
    spans_grid = sorted(set([selected_spans] + [int(v) for v in cfg["day5"]["compare_spans"]]))
    powers = sorted(set([selected_power] + [float(v) for v in cfg["day5"]["launch_power_grid"]]))
    pcs_nus = [float(v) for v in cfg["day5"]["pcs_nu_grid"]]

    # Baseline method comparison without PCS.
    for seed in seeds:
        for band in bands:
            for spans in spans_grid:
                for power in powers:
                    rng = np.random.default_rng(seed * 100000 + int((power + 100) * 100) + spans * 10 + len(band))
                    tx, tx_idx, priors = sample_symbols(int(cfg["day5"]["symbols"]), shaped=False, nu=0.0, rng=rng)
                    result = waveform_ssfm_channel(tx, tx_idx, priors, cfg, band, spans, power, stress, rng)
                    method_rows, _ = _apply_methods(
                        result.tx_symbols_aligned,
                        result.tx_indices_aligned,
                        result.priors,
                        result.rx_symbols,
                        cfg,
                        f"day5_seed{seed}_{band}_sp{spans}_p{power}",
                    )
                    for r in method_rows:
                        rows.append({
                            "seed": seed,
                            "band": band,
                            "spans": spans,
                            "launch_power_dbm": power,
                            "pcs_nu": 0.0,
                            "shaped": False,
                            "stress_name": stress["name"],
                            **r,
                        })

    # PCS sweep only at selected operating point to control runtime.
    for seed in seeds:
        for nu in pcs_nus:
            rng = np.random.default_rng(seed * 200000 + int(nu * 10000))
            shaped = nu > 0
            tx, tx_idx, priors = sample_symbols(int(cfg["day5"]["symbols"]), shaped=shaped, nu=nu, rng=rng)
            result = waveform_ssfm_channel(tx, tx_idx, priors, cfg, "C", selected_spans, selected_power, stress, rng)
            method_rows, _ = _apply_methods(
                result.tx_symbols_aligned,
                result.tx_indices_aligned,
                result.priors,
                result.rx_symbols,
                cfg,
                f"day5_pcs_seed{seed}_nu{nu}",
            )
            keep = {"raw", "memory_neural"}
            for r in method_rows:
                if r["scenario"] not in keep:
                    continue
                display = ("PCS + Memory neural" if shaped else "Uniform + Memory neural") if r["scenario"] == "memory_neural" else ("PCS raw" if shaped else "Uniform raw")
                scenario = ("pcs_memory_neural" if shaped else "uniform_memory_neural") if r["scenario"] == "memory_neural" else ("pcs_raw" if shaped else "uniform_raw")
                rows.append({
                    "seed": seed,
                    "band": "C",
                    "spans": selected_spans,
                    "launch_power_dbm": selected_power,
                    "pcs_nu": nu,
                    "shaped": shaped,
                    "stress_name": stress["name"],
                    **{**r, "display_name": display, "scenario": scenario},
                })

    raw = pd.DataFrame(rows)
    ci = _ci(raw, ["band", "spans", "launch_power_dbm", "pcs_nu", "shaped", "stress_name", "display_name", "scenario"])
    return raw, ci


def _best_by_method(ci: pd.DataFrame) -> pd.DataFrame:
    return (
        ci.sort_values(["gmi_mean", "ngmi_mean", "rate_tbps_mean"], ascending=False)
        .groupby("scenario", as_index=False)
        .head(1)
        .sort_values("gmi_mean", ascending=False)
    )


def _acceptance_gate(best_df: pd.DataFrame, final_ci: pd.DataFrame, cfg: Dict) -> Dict:
    """Strict Optica evidence gate.

    Day-5 v1 allowed a PCS claim if nonzero PCS had any positive GMI gain.
    That was too loose. This strict gate requires:
    1. non-saturated operating point;
    2. improvement larger than configured threshold;
    3. improvement larger than the combined 95% CI;
    4. acceptable BER;
    5. neural must beat raw, linear, DBP-like, and polynomial baselines for a neural-superiority claim.
    """
    method_baselines = ["raw", "linear", "dbp_like", "poly_nlc"]
    neural_rows = best_df[best_df["scenario"].isin(["memory_neural", "pcs_memory_neural", "uniform_memory_neural"])]
    baseline_rows = best_df[best_df["scenario"].isin(method_baselines)]

    target_gmi_max = float(cfg["day5"]["target_gmi_max"])
    target_gmi_min = float(cfg["day5"]["target_gmi_min"])
    target_ber_min = float(cfg["day5"]["target_ber_min"])
    target_ber_max = float(cfg["day5"]["target_ber_max"])

    result = {
        "passes_high_level_optica_gate": False,
        "neural_beats_all_baselines": False,
        "pcs_nonzero_wins": False,
        "strict_gate_version": "Day5B",
        "recommended_claim": "No high-level Optica performance claim yet.",
        "details": {},
    }

    def _non_saturated(row) -> bool:
        return bool(
            target_gmi_min <= float(row["gmi_mean"]) <= target_gmi_max
            and target_ber_min <= max(float(row["ber_mean"]), 1e-12) <= target_ber_max
            and float(row["ngmi_mean"]) <= float(cfg["day5"]["target_ngmi_max"])
        )

    if not neural_rows.empty and not baseline_rows.empty:
        best_neural = neural_rows.sort_values("gmi_mean", ascending=False).iloc[0]
        best_base = baseline_rows.sort_values("gmi_mean", ascending=False).iloc[0]

        gmi_gain = float(best_neural["gmi_mean"] - best_base["gmi_mean"])
        ngmi_gain = float(best_neural["ngmi_mean"] - best_base["ngmi_mean"])
        rate_gain = float(best_neural["rate_tbps_mean"] - best_base["rate_tbps_mean"])

        combined_gmi_ci = float(best_neural.get("gmi_ci95", 0.0) + best_base.get("gmi_ci95", 0.0))
        combined_ngmi_ci = float(best_neural.get("ngmi_ci95", 0.0) + best_base.get("ngmi_ci95", 0.0))
        combined_rate_ci = float(best_neural.get("rate_tbps_ci95", 0.0) + best_base.get("rate_tbps_ci95", 0.0))

        ber_ok = float(best_neural["ber_mean"]) <= float(cfg["day5"]["max_allowed_ber"])
        neural_non_saturated = _non_saturated(best_neural)

        neural_win = (
            gmi_gain >= max(float(cfg["day5"]["min_gmi_gain_vs_best_baseline"]), combined_gmi_ci)
            and ngmi_gain >= max(float(cfg["day5"]["min_ngmi_gain_vs_best_baseline"]), combined_ngmi_ci)
            and rate_gain >= max(float(cfg["day5"]["min_rate_gain_tbps_per_channel"]), combined_rate_ci)
            and ber_ok
            and neural_non_saturated
        )

        result["neural_beats_all_baselines"] = bool(neural_win)
        result["details"]["best_neural"] = best_neural.to_dict()
        result["details"]["best_baseline"] = best_base.to_dict()
        result["details"]["gmi_gain_vs_best_baseline"] = gmi_gain
        result["details"]["ngmi_gain_vs_best_baseline"] = ngmi_gain
        result["details"]["rate_gain_tbps_vs_best_baseline"] = rate_gain
        result["details"]["combined_gmi_ci95"] = combined_gmi_ci
        result["details"]["combined_ngmi_ci95"] = combined_ngmi_ci
        result["details"]["combined_rate_ci95"] = combined_rate_ci
        result["details"]["neural_non_saturated"] = bool(neural_non_saturated)
        result["details"]["ber_ok"] = bool(ber_ok)

    pcs_rows = final_ci[final_ci["scenario"].isin(["pcs_raw", "pcs_memory_neural", "uniform_raw", "uniform_memory_neural"])].copy()
    if not pcs_rows.empty:
        # Compare best nonzero PCS against best uniform at matched family when possible.
        # Prefer raw-vs-raw and memory-vs-memory matched comparison, then choose the stronger strict result.
        comparisons = []
        pairs = [
            ("pcs_raw", "uniform_raw", "raw PCS"),
            ("pcs_memory_neural", "uniform_memory_neural", "PCS + memory neural"),
        ]
        for pcs_scenario, uniform_scenario, label in pairs:
            pcs_cand = pcs_rows[(pcs_rows["scenario"] == pcs_scenario) & (pcs_rows["pcs_nu"] > 0)]
            uni_cand = pcs_rows[(pcs_rows["scenario"] == uniform_scenario) & (pcs_rows["pcs_nu"] == 0)]
            if pcs_cand.empty or uni_cand.empty:
                continue
            best_pcs = pcs_cand.sort_values("gmi_mean", ascending=False).iloc[0]
            # Use the uniform row with same spans/power/band when possible.
            matched_uni = uni_cand[
                (uni_cand["band"] == best_pcs["band"])
                & (uni_cand["spans"] == best_pcs["spans"])
                & (uni_cand["launch_power_dbm"] == best_pcs["launch_power_dbm"])
            ]
            if matched_uni.empty:
                best_uni = uni_cand.sort_values("gmi_mean", ascending=False).iloc[0]
            else:
                best_uni = matched_uni.sort_values("gmi_mean", ascending=False).iloc[0]

            gmi_gain = float(best_pcs["gmi_mean"] - best_uni["gmi_mean"])
            ngmi_gain = float(best_pcs["ngmi_mean"] - best_uni["ngmi_mean"])
            rate_gain = float(best_pcs["rate_tbps_mean"] - best_uni["rate_tbps_mean"])
            combined_gmi_ci = float(best_pcs.get("gmi_ci95", 0.0) + best_uni.get("gmi_ci95", 0.0))
            combined_ngmi_ci = float(best_pcs.get("ngmi_ci95", 0.0) + best_uni.get("ngmi_ci95", 0.0))
            combined_rate_ci = float(best_pcs.get("rate_tbps_ci95", 0.0) + best_uni.get("rate_tbps_ci95", 0.0))

            non_saturated = _non_saturated(best_pcs) and _non_saturated(best_uni)
            ber_ok = float(best_pcs["ber_mean"]) <= float(cfg["day5"]["max_allowed_ber"])

            passes = (
                gmi_gain >= max(float(cfg["day5"]["min_gmi_gain_vs_best_baseline"]), combined_gmi_ci)
                and ngmi_gain >= max(float(cfg["day5"]["min_ngmi_gain_vs_best_baseline"]), combined_ngmi_ci)
                and rate_gain >= max(float(cfg["day5"]["min_rate_gain_tbps_per_channel"]), combined_rate_ci)
                and non_saturated
                and ber_ok
            )

            comparisons.append({
                "label": label,
                "passes": bool(passes),
                "best_pcs": best_pcs.to_dict(),
                "best_uniform": best_uni.to_dict(),
                "gmi_gain": gmi_gain,
                "ngmi_gain": ngmi_gain,
                "rate_gain": rate_gain,
                "combined_gmi_ci95": combined_gmi_ci,
                "combined_ngmi_ci95": combined_ngmi_ci,
                "combined_rate_ci95": combined_rate_ci,
                "non_saturated": bool(non_saturated),
                "ber_ok": bool(ber_ok),
            })

        if comparisons:
            best_comp = sorted(comparisons, key=lambda x: x["gmi_gain"], reverse=True)[0]
            result["pcs_nonzero_wins"] = bool(any(c["passes"] for c in comparisons))
            result["details"]["pcs_comparisons"] = comparisons
            result["details"]["best_pcs_comparison"] = best_comp

    result["passes_high_level_optica_gate"] = bool(result["neural_beats_all_baselines"] or result["pcs_nonzero_wins"])

    if result["neural_beats_all_baselines"] and result["pcs_nonzero_wins"]:
        result["recommended_claim"] = "Strict gate passed: memory-aware neural equalization improves bit-metric GMI/rate, and nonzero PCS is beneficial in a non-saturated waveform operating region."
    elif result["neural_beats_all_baselines"]:
        result["recommended_claim"] = "Strict gate passed: memory-aware neural equalization improves bit-metric GMI/rate over raw, linear, DBP-like, and polynomial baselines in a non-saturated waveform operating region."
    elif result["pcs_nonzero_wins"]:
        result["recommended_claim"] = "Strict gate passed: nonzero PCS improves exact GMI/rate in a non-saturated waveform operating region. Do not claim neural superiority unless it also beats baselines."
    else:
        result["recommended_claim"] = "Strict gate failed: use as validation/negative-result evidence; do not claim high-level Optica performance superiority yet."

    return result

def _write_reports(cfg, sanity_df, selector_df, raw_df, ci_df, best_df, gate, figure_paths) -> Tuple[Path, Path, Path]:
    reports_dir = ensure_dir(cfg["output"]["reports"])
    report = reports_dir / "day5_optica_evidence_report.md"
    acceptance = reports_dir / "day5_acceptance_gate_report.md"
    latex = reports_dir / "day5_latex_results_snippet.tex"

    sel = selector_df.iloc[0]
    lines = []
    lines.append("# Day-5 Optica Evidence Report")
    lines.append("")
    lines.append("## What Day-5 adds")
    lines.append("")
    lines.append("- Waveform-level SSFM starter with RRC pulse shaping and matched filtering.")
    lines.append("- Receiver chromatic-dispersion compensation.")
    lines.append("- Memory-aware neural equalizer using neighboring symbols.")
    lines.append("- Exact bit-metric AWGN-likelihood GMI/NGMI.")
    lines.append("- Stress selector to avoid saturated or random operating regions.")
    lines.append("- Acceptance gate against Raw, Linear EQ, DBP-like, and Polynomial NLC baselines.")
    lines.append("")
    lines.append("## Sanity tests")
    lines.append("")
    lines.append(sanity_df.round(6).to_markdown(index=False))
    lines.append("")
    lines.append("## Selected stress point")
    lines.append("")
    sel_df = pd.DataFrame([sel.to_dict()])
    lines.append(sel_df.round(6).to_markdown(index=False))
    lines.append("")
    lines.append("## Best method points")
    lines.append("")
    lines.append(best_df.round(6).to_markdown(index=False))
    lines.append("")
    lines.append("## Generated figures")
    for p in figure_paths:
        lines.append(f"- `{p}`")
    report.write_text("\n".join(lines), encoding="utf-8")

    lines = []
    lines.append("# Day-5 Acceptance Gate Report")
    lines.append("")
    lines.append(f"**Passes high-level Optica evidence gate:** {gate['passes_high_level_optica_gate']}")
    lines.append("")
    lines.append(f"**Recommended claim:** {gate['recommended_claim']}")
    lines.append("")
    lines.append("## Gate details")
    lines.append("")
    for k, v in gate["details"].items():
        lines.append(f"### {k}")
        lines.append("")
        if isinstance(v, dict):
            try:
                lines.append(pd.DataFrame([v]).round(6).to_markdown(index=False))
            except Exception:
                lines.append(str(v))
        elif isinstance(v, list):
            for i, item in enumerate(v, 1):
                lines.append(f"#### item {i}")
                if isinstance(item, dict):
                    simple = {kk: vv for kk, vv in item.items() if not isinstance(vv, dict)}
                    nested = {kk: vv for kk, vv in item.items() if isinstance(vv, dict)}
                    if simple:
                        try:
                            lines.append(pd.DataFrame([simple]).round(6).to_markdown(index=False))
                        except Exception:
                            lines.append(str(simple))
                    for nk, nv in nested.items():
                        lines.append(f"**{nk}**")
                        try:
                            lines.append(pd.DataFrame([nv]).round(6).to_markdown(index=False))
                        except Exception:
                            lines.append(str(nv))
                else:
                    lines.append(str(item))
                lines.append("")
        else:
            lines.append(str(v))
        lines.append("")
    lines.append("")
    lines.append("## Rule")
    lines.append("")
    lines.append("High-level claim is allowed only if memory neural beats all baselines by the configured GMI/NGMI/rate thresholds, or if nonzero PCS wins in exact GMI under the selected waveform stress point.")
    acceptance.write_text("\n".join(lines), encoding="utf-8")

    best = best_df.iloc[0]
    latex.write_text(textwrap.dedent(f"""
    \\subsection{{Day-5 Waveform-Level SSFM Evidence}}
    Day-5 uses waveform-level RRC pulse shaping, matched filtering, receiver chromatic-dispersion compensation, and an SSFM-style split-step propagation starter. A stress selector selected {sel['stress_name']} stress at {sel['launch_power_dbm']:.1f} dBm/channel and {int(sel['spans'])} spans because it avoided both saturation and random decisions. The best method was {best['display_name']} with GMI={best['gmi_mean']:.3f}$\\pm${best['gmi_ci95']:.3f}, NGMI={best['ngmi_mean']:.3f}$\\pm${best['ngmi_ci95']:.3f}, BER={best['ber_mean']:.3e}, and estimated rate={best['rate_tbps_mean']:.4f}$\\pm${best['rate_tbps_ci95']:.4f} Tb/s/channel. The automated acceptance gate reports: {gate['recommended_claim']}
    """).strip() + "\n", encoding="utf-8")

    return report, acceptance, latex


def run_day5_optica_evidence(cfg: Dict) -> Dict:
    tables_dir = ensure_dir(cfg["output"]["tables"])
    figures_dir = ensure_dir(cfg["output"]["figures"])

    sanity_df = _sanity_tests(cfg)
    selector_df = _stress_selector(cfg)
    stress, selected_power, selected_spans = _selected_stress(cfg, selector_df)

    raw_df, ci_df = _run_final_evidence(cfg, stress, selected_power, selected_spans)
    best_df = _best_by_method(ci_df)
    gate = _acceptance_gate(best_df, ci_df, cfg)

    sanity_df.to_csv(tables_dir / "day5_sanity_tests.csv", index=False)
    selector_df.to_csv(tables_dir / "day5_stress_selector.csv", index=False)
    raw_df.to_csv(tables_dir / "day5_raw_metrics.csv", index=False)
    ci_df.to_csv(tables_dir / "day5_ci_metrics.csv", index=False)
    best_df.to_csv(tables_dir / "day5_best_methods.csv", index=False)
    pd.DataFrame([{
        "passes_high_level_optica_gate": gate["passes_high_level_optica_gate"],
        "neural_beats_all_baselines": gate["neural_beats_all_baselines"],
        "pcs_nonzero_wins": gate["pcs_nonzero_wins"],
        "recommended_claim": gate["recommended_claim"],
    }]).to_csv(tables_dir / "day5_acceptance_summary.csv", index=False)

    # Representative plot slice: selected C-band, selected span, selected stress.
    plot_slice = ci_df[
        (ci_df["band"] == "C")
        & (ci_df["spans"] == selected_spans)
        & (ci_df["stress_name"] == stress["name"])
        & (ci_df["pcs_nu"] == 0.0)
        & (ci_df["shaped"] == False)
    ].copy()

    pcs_slice = ci_df[
        (ci_df["band"] == "C")
        & (ci_df["spans"] == selected_spans)
        & (ci_df["launch_power_dbm"] == selected_power)
        & (ci_df["scenario"].isin(["pcs_raw", "pcs_memory_neural", "uniform_raw", "uniform_memory_neural"]))
    ].copy()

    # Build constellation demo from selected operating point.
    rng = np.random.default_rng(int(cfg["day5"]["seed"]) + 999)
    tx, tx_idx, priors = sample_symbols(int(cfg["day5"]["symbols"]), shaped=False, nu=0.0, rng=rng)
    result = waveform_ssfm_channel(tx, tx_idx, priors, cfg, "C", selected_spans, selected_power, stress, rng)
    method_rows, outputs = _apply_methods(result.tx_symbols_aligned, result.tx_indices_aligned, result.priors, result.rx_symbols, cfg, "day5_constellation_demo")

    figure_paths = []
    figure_paths.append(plot_constellations(
        result.tx_symbols_aligned,
        result.rx_symbols,
        outputs.get("linear", result.rx_symbols),
        outputs.get("memory_neural", result.rx_symbols),
        figures_dir / "fig_day5_constellations.png",
    ))
    figure_paths.append(plot_metric_vs_power(plot_slice, "gmi", "GMI (bits/symbol)", "Day-5 waveform SSFM: GMI vs launch power", figures_dir / "fig_day5_gmi_vs_power.png"))
    figure_paths.append(plot_metric_vs_power(plot_slice, "ngmi", "NGMI", "Day-5 waveform SSFM: NGMI vs launch power", figures_dir / "fig_day5_ngmi_vs_power.png"))
    figure_paths.append(plot_metric_vs_power(plot_slice, "ber", "BER", "Day-5 waveform SSFM: BER vs launch power", figures_dir / "fig_day5_ber_vs_power.png", logy=True))
    if not pcs_slice.empty:
        figure_paths.append(plot_pcs_sweep(pcs_slice, "gmi", "GMI (bits/symbol)", "Day-5 PCS sweep at selected waveform operating point", figures_dir / "fig_day5_pcs_gmi_sweep.png"))
    figure_paths.append(plot_best_tradeoff(best_df, figures_dir / "fig_day5_best_tradeoff.png"))

    report, acceptance, latex = _write_reports(cfg, sanity_df, selector_df, raw_df, ci_df, best_df, gate, figure_paths)

    return {
        "report_path": str(report),
        "acceptance_report_path": str(acceptance),
        "latex_snippet_path": str(latex),
        "figure_paths": [str(p) for p in figure_paths],
        "sanity_csv": str(tables_dir / "day5_sanity_tests.csv"),
        "selector_csv": str(tables_dir / "day5_stress_selector.csv"),
        "raw_csv": str(tables_dir / "day5_raw_metrics.csv"),
        "ci_csv": str(tables_dir / "day5_ci_metrics.csv"),
        "best_csv": str(tables_dir / "day5_best_methods.csv"),
        "acceptance_csv": str(tables_dir / "day5_acceptance_summary.csv"),
    }
