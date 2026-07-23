from __future__ import annotations

import copy
import math
import textwrap
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from .day8_q3_band_comparison import _run_one, _scenario_seed, _paired
from .utils import ensure_dir


def _day9_defaults(cfg: Dict) -> Dict:
    return {
        "accepted_points": [
            {"scenario_group": "C", "spans": 10, "launch_power_dbm": 2.0, "pcs_nu": 0.36},
            {"scenario_group": "S", "spans": 12, "launch_power_dbm": -2.0, "pcs_nu": 0.36},
            {"scenario_group": "C+S", "spans": 12, "launch_power_dbm": 0.0, "pcs_nu": 0.36},
        ],
        "raw_per_seed": {"seeds": [1, 2, 3, 4, 5, 6, 7]},
        "ssfm_convergence": {
            "enabled": True,
            "scenarios": ["C", "S"],
            "seeds": [1, 2, 3],
            "steps_per_span_grid": [2, 4, 8, 12],
            "symbols": 4096,
            "reference_steps_per_span": 12,
            "pass_gmi_gain_tolerance": 0.020,
            "pass_ngmi_gain_tolerance": 0.006,
        },
        "symbol_convergence": {
            "enabled": True,
            "scenarios": ["C", "S"],
            "seeds": [1, 2, 3],
            "symbol_grid": [2048, 4096, 8192],
            "steps_per_span": 4,
            "reference_symbols": 8192,
            "pass_gmi_gain_tolerance": 0.020,
            "pass_ngmi_gain_tolerance": 0.006,
        },
        "gn_style_benchmark": {
            "enabled": True,
            "scenarios": ["C", "S"],
            "seeds": [1, 2, 3],
            "powers": [-2.0, 0.0, 2.0, 4.0],
            "symbols": 4096,
            "steps_per_span": 4,
        },
        "external_reference": {
            "enabled": True,
            "csv_path": "validation_data/gnpy_day9_reference.csv",
            "expected_columns": ["scenario_group", "band", "spans", "launch_power_dbm", "reference_gsnr_db"],
        },
    }


def _merge_defaults(base: Dict, override: Dict) -> Dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge_defaults(out[k], v)
        else:
            out[k] = v
    return out


def _day9_cfg(cfg: Dict) -> Dict:
    return _merge_defaults(_day9_defaults(cfg), cfg.get("day9_validation", {}))


def _scenario_bands(scenario: str) -> List[str]:
    return ["C", "S"] if scenario == "C+S" else [scenario]


def _cfg_variant(cfg: Dict, *, symbols: Optional[int] = None, steps_per_span: Optional[int] = None) -> Dict:
    c = copy.deepcopy(cfg)
    if symbols is not None:
        c["day8"]["symbols"] = int(symbols)
        # Keep GMI sampling bounded by available symbols so smaller convergence runs stay stable.
        c["day5"]["gmi_monte_carlo_limit"] = min(int(c["day5"].get("gmi_monte_carlo_limit", 30000)), int(symbols))
    if steps_per_span is not None:
        c["day5"]["ssfm_steps_per_span"] = int(steps_per_span)
    return c


def _simulate_operating_rows(
    cfg: Dict,
    *,
    points: Iterable[Dict],
    seeds: Iterable[int],
    include_uniform: bool = True,
    include_pcs: bool = True,
) -> pd.DataFrame:
    rows: List[Dict] = []
    for point in points:
        scenario = str(point["scenario_group"])
        spans = int(point["spans"])
        power = float(point["launch_power_dbm"])
        pcs_nu = float(point["pcs_nu"])
        nus: List[float] = []
        if include_uniform:
            nus.append(0.0)
        if include_pcs:
            nus.append(pcs_nu)
        for seed in map(int, seeds):
            for band in _scenario_bands(scenario):
                for nu in nus:
                    rows.append(_run_one(seed, scenario, band, spans, power, nu, cfg))
    return pd.DataFrame(rows)


def _paired_gain_from_raw(raw: pd.DataFrame) -> pd.DataFrame:
    seed_level = _scenario_seed(raw)
    gain = _paired(seed_level)
    return gain, seed_level


def _accepted_points(day9: Dict, scenarios: Optional[Iterable[str]] = None) -> List[Dict]:
    points = list(day9["accepted_points"])
    if scenarios is None:
        return points
    allowed = set(map(str, scenarios))
    return [p for p in points if str(p["scenario_group"]) in allowed]


def _add_reference_error(summary: pd.DataFrame, metric: str, group_cols: List[str], ref_col_name: str) -> pd.DataFrame:
    if summary.empty:
        return summary
    ref = summary.copy()
    ref = ref[ref[ref_col_name] == ref[ref_col_name].max()]
    ref = ref[group_cols + [metric]].rename(columns={metric: f"{metric}_reference"})
    out = summary.merge(ref, on=group_cols, how="left")
    out[f"{metric}_abs_error_vs_reference"] = (out[metric] - out[f"{metric}_reference"]).abs()
    return out


def _summarize_gain(gain: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "scenario_group", "spans", "launch_power_dbm", "pcs_nu", "n_pairs",
        "gmi_gain_mean", "gmi_gain_ci95", "ngmi_gain_mean", "ngmi_gain_ci95",
        "ber_delta_mean", "ber_delta_ci95", "rate_gain_mean", "rate_gain_ci95",
        "aggregate_rate_gain_mean", "aggregate_rate_gain_ci95",
    ]
    return gain[[c for c in cols if c in gain.columns]].copy()


def _run_raw_per_seed(cfg: Dict, day9: Dict, tables_dir: Path) -> Dict[str, str]:
    seeds = day9["raw_per_seed"]["seeds"]
    raw = _simulate_operating_rows(cfg, points=day9["accepted_points"], seeds=seeds)
    gain, seed_level = _paired_gain_from_raw(raw)

    raw_path = tables_dir / "day9_raw_band_metrics_selected.csv"
    seed_path = tables_dir / "day9_raw_per_seed_selected.csv"
    gain_path = tables_dir / "day9_raw_per_seed_paired_gains.csv"

    raw.to_csv(raw_path, index=False)
    seed_level.to_csv(seed_path, index=False)
    gain.to_csv(gain_path, index=False)
    return {"raw_band": str(raw_path), "seed_level": str(seed_path), "paired_gain": str(gain_path)}


def _run_ssfm_convergence(cfg: Dict, day9: Dict, tables_dir: Path) -> Dict[str, str]:
    c = day9["ssfm_convergence"]
    points = _accepted_points(day9, c.get("scenarios"))
    rows: List[pd.DataFrame] = []
    for steps in map(int, c["steps_per_span_grid"]):
        cv = _cfg_variant(cfg, symbols=int(c["symbols"]), steps_per_span=steps)
        raw = _simulate_operating_rows(cv, points=points, seeds=c["seeds"])
        gain, _ = _paired_gain_from_raw(raw)
        gain["ssfm_steps_per_span"] = int(steps)
        gain["symbols"] = int(c["symbols"])
        rows.append(gain)
    all_gain = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    summary = _summarize_gain(all_gain)
    if not summary.empty:
        summary["ssfm_steps_per_span"] = all_gain["ssfm_steps_per_span"].values
        summary["symbols"] = all_gain["symbols"].values
        summary = _add_reference_error(
            summary,
            metric="gmi_gain_mean",
            group_cols=["scenario_group", "spans", "launch_power_dbm", "pcs_nu"],
            ref_col_name="ssfm_steps_per_span",
        )
        summary = _add_reference_error(
            summary,
            metric="ngmi_gain_mean",
            group_cols=["scenario_group", "spans", "launch_power_dbm", "pcs_nu"],
            ref_col_name="ssfm_steps_per_span",
        )
        tol_g = float(c["pass_gmi_gain_tolerance"])
        tol_n = float(c["pass_ngmi_gain_tolerance"])
        summary["passes_convergence_gate"] = (
            (summary["gmi_gain_mean_abs_error_vs_reference"] <= tol_g)
            & (summary["ngmi_gain_mean_abs_error_vs_reference"] <= tol_n)
        )
    path = tables_dir / "day9_ssfm_step_convergence.csv"
    summary.to_csv(path, index=False)
    return {"ssfm_convergence": str(path)}


def _run_symbol_convergence(cfg: Dict, day9: Dict, tables_dir: Path) -> Dict[str, str]:
    c = day9["symbol_convergence"]
    points = _accepted_points(day9, c.get("scenarios"))
    rows: List[pd.DataFrame] = []
    for symbols in map(int, c["symbol_grid"]):
        cv = _cfg_variant(cfg, symbols=symbols, steps_per_span=int(c["steps_per_span"]))
        raw = _simulate_operating_rows(cv, points=points, seeds=c["seeds"])
        gain, _ = _paired_gain_from_raw(raw)
        gain["symbols"] = int(symbols)
        gain["ssfm_steps_per_span"] = int(c["steps_per_span"])
        rows.append(gain)
    all_gain = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    summary = _summarize_gain(all_gain)
    if not summary.empty:
        summary["symbols"] = all_gain["symbols"].values
        summary["ssfm_steps_per_span"] = all_gain["ssfm_steps_per_span"].values
        summary = _add_reference_error(
            summary,
            metric="gmi_gain_mean",
            group_cols=["scenario_group", "spans", "launch_power_dbm", "pcs_nu"],
            ref_col_name="symbols",
        )
        summary = _add_reference_error(
            summary,
            metric="ngmi_gain_mean",
            group_cols=["scenario_group", "spans", "launch_power_dbm", "pcs_nu"],
            ref_col_name="symbols",
        )
        tol_g = float(c["pass_gmi_gain_tolerance"])
        tol_n = float(c["pass_ngmi_gain_tolerance"])
        summary["passes_convergence_gate"] = (
            (summary["gmi_gain_mean_abs_error_vs_reference"] <= tol_g)
            & (summary["ngmi_gain_mean_abs_error_vs_reference"] <= tol_n)
        )
    path = tables_dir / "day9_symbol_count_convergence.csv"
    summary.to_csv(path, index=False)
    return {"symbol_convergence": str(path)}


def _gn_style_estimate(row: pd.Series, cfg: Dict, calibration: Dict[str, float]) -> float:
    band_cfg = cfg["bands"][str(row["band"])]
    spans = max(float(row["spans"]), 1.0)
    p_lin = 10.0 ** (float(row["launch_power_dbm"]) / 10.0)
    nf_scale = float(band_cfg["noise_figure_db"]) / 5.0
    loss_scale = float(band_cfg["attenuation_db_per_km"]) / 0.20
    disp_scale = max(abs(float(band_cfg["dispersion_ps_nm_km"])) / 16.7, 0.1)
    ase = calibration["ase"] * spans * nf_scale * loss_scale / max(p_lin, 1e-12)
    nli = calibration["nli"] * (p_lin ** 2) * spans * disp_scale
    impl = calibration["implementation"]
    snr = 1.0 / max(ase + nli + impl, 1e-12)
    return float(10.0 * math.log10(snr) + calibration["offset_db"])


def _fit_gn_offset(sim: pd.DataFrame, cfg: Dict) -> Dict[str, float]:
    # Simple internal GN-style sanity model. This is not GNPy.
    base = {"ase": 0.006, "nli": 0.00055, "implementation": 0.0025, "offset_db": 0.0}
    tmp = sim.copy()
    tmp["gn_no_offset"] = tmp.apply(lambda r: _gn_style_estimate(r, cfg, base), axis=1)
    base["offset_db"] = float((tmp["gsnr_db"] - tmp["gn_no_offset"]).mean()) if not tmp.empty else 0.0
    return base


def _run_gn_style_benchmark(cfg: Dict, day9: Dict, tables_dir: Path) -> Dict[str, str]:
    c = day9["gn_style_benchmark"]
    rows: List[Dict] = []
    cv = _cfg_variant(cfg, symbols=int(c["symbols"]), steps_per_span=int(c["steps_per_span"]))
    points = _accepted_points(day9, c.get("scenarios"))
    bench_points = []
    for p in points:
        for power in c["powers"]:
            q = dict(p)
            q["launch_power_dbm"] = float(power)
            bench_points.append(q)
    raw = _simulate_operating_rows(cv, points=bench_points, seeds=c["seeds"], include_uniform=True, include_pcs=False)
    calibration = _fit_gn_offset(raw, cv)
    raw["gn_style_gsnr_db"] = raw.apply(lambda r: _gn_style_estimate(r, cv, calibration), axis=1)
    raw["gsnr_error_db"] = raw["gsnr_db"] - raw["gn_style_gsnr_db"]
    summary = raw.groupby(["scenario_group", "band", "spans", "launch_power_dbm"], as_index=False).agg(
        ssfm_gsnr_db_mean=("gsnr_db", "mean"),
        gn_style_gsnr_db_mean=("gn_style_gsnr_db", "mean"),
        gsnr_error_db_mean=("gsnr_error_db", "mean"),
        gsnr_error_db_std=("gsnr_error_db", "std"),
        n_seeds=("seed", "nunique"),
    )
    rmse = float(np.sqrt(np.mean(np.square(summary["gsnr_error_db_mean"])))) if not summary.empty else float("nan")
    summary["benchmark_rmse_db_over_grid"] = rmse
    summary["benchmark_type"] = "internal_gn_style_sanity_not_gnpy"
    path = tables_dir / "day9_gn_style_gsnr_benchmark.csv"
    summary.to_csv(path, index=False)
    raw_path = tables_dir / "day9_gn_style_raw_uniform_runs.csv"
    raw.to_csv(raw_path, index=False)
    return {"gn_style_benchmark": str(path), "gn_style_raw": str(raw_path)}


def _run_external_reference_check(cfg: Dict, day9: Dict, tables_dir: Path) -> Dict[str, str]:
    e = day9["external_reference"]
    template = pd.DataFrame(columns=e["expected_columns"])
    template_path = tables_dir / "day9_external_reference_template.csv"
    template.to_csv(template_path, index=False)

    ref_path = Path(str(e.get("csv_path", "")))
    if not ref_path.exists():
        report = tables_dir / "day9_external_reference_check.csv"
        pd.DataFrame([{
            "status": "reference_file_missing",
            "expected_csv_path": str(ref_path),
            "message": "Fill the template with GNPy/GN/EGN reference GSNR values and rerun this script.",
        }]).to_csv(report, index=False)
        return {"external_reference_template": str(template_path), "external_reference_check": str(report)}

    ref = pd.read_csv(ref_path)
    required = set(e["expected_columns"])
    missing = sorted(required.difference(ref.columns))
    if missing:
        report = tables_dir / "day9_external_reference_check.csv"
        pd.DataFrame([{"status": "missing_columns", "missing_columns": ";".join(missing)}]).to_csv(report, index=False)
        return {"external_reference_template": str(template_path), "external_reference_check": str(report)}

    gn_path = tables_dir / "day9_gn_style_gsnr_benchmark.csv"
    if not gn_path.exists():
        report = tables_dir / "day9_external_reference_check.csv"
        pd.DataFrame([{"status": "internal_benchmark_missing", "message": "Run GN-style benchmark first."}]).to_csv(report, index=False)
        return {"external_reference_template": str(template_path), "external_reference_check": str(report)}

    sim = pd.read_csv(gn_path)
    merged = sim.merge(ref, on=["scenario_group", "band", "spans", "launch_power_dbm"], how="inner")
    if merged.empty:
        merged = pd.DataFrame([{"status": "no_matching_rows", "message": "Reference rows did not match simulated scenario/band/span/power keys."}])
    else:
        merged["external_error_db"] = merged["ssfm_gsnr_db_mean"] - merged["reference_gsnr_db"]
        merged["external_rmse_db"] = float(np.sqrt(np.mean(np.square(merged["external_error_db"]))))
        merged["status"] = "ok"
    report = tables_dir / "day9_external_reference_check.csv"
    merged.to_csv(report, index=False)
    return {"external_reference_template": str(template_path), "external_reference_check": str(report)}


def _plot_outputs(tables_dir: Path, figures_dir: Path) -> Dict[str, str]:
    import matplotlib.pyplot as plt

    out: Dict[str, str] = {}

    def savefig(name: str) -> None:
        png = figures_dir / f"{name}.png"
        pdf = figures_dir / f"{name}.pdf"
        plt.tight_layout()
        plt.savefig(png, dpi=300)
        plt.savefig(pdf)
        plt.close()
        out[name] = str(png)
        out[f"{name}_pdf"] = str(pdf)

    ssfm_path = tables_dir / "day9_ssfm_step_convergence.csv"
    if ssfm_path.exists():
        df = pd.read_csv(ssfm_path)
        if not df.empty:
            plt.figure(figsize=(6.5, 4.2))
            for scenario, g in df.groupby("scenario_group"):
                g = g.sort_values("ssfm_steps_per_span")
                plt.plot(g["ssfm_steps_per_span"], g["gmi_gain_mean"], marker="o", label=str(scenario))
            plt.xlabel("SSFM steps per span")
            plt.ylabel("Mean GMI gain")
            plt.title("SSFM step-size convergence of PCS gain")
            plt.grid(True, alpha=0.3)
            plt.legend()
            savefig("fig_day9_ssfm_step_convergence")

    sym_path = tables_dir / "day9_symbol_count_convergence.csv"
    if sym_path.exists():
        df = pd.read_csv(sym_path)
        if not df.empty:
            plt.figure(figsize=(6.5, 4.2))
            for scenario, g in df.groupby("scenario_group"):
                g = g.sort_values("symbols")
                plt.plot(g["symbols"], g["gmi_gain_mean"], marker="o", label=str(scenario))
            plt.xlabel("Symbols per trial")
            plt.ylabel("Mean GMI gain")
            plt.title("Symbol-count convergence of PCS gain")
            plt.grid(True, alpha=0.3)
            plt.legend()
            savefig("fig_day9_symbol_count_convergence")

    gn_path = tables_dir / "day9_gn_style_gsnr_benchmark.csv"
    if gn_path.exists():
        df = pd.read_csv(gn_path)
        if not df.empty:
            plt.figure(figsize=(5.8, 5.2))
            plt.scatter(df["gn_style_gsnr_db_mean"], df["ssfm_gsnr_db_mean"])
            lo = float(min(df["gn_style_gsnr_db_mean"].min(), df["ssfm_gsnr_db_mean"].min()))
            hi = float(max(df["gn_style_gsnr_db_mean"].max(), df["ssfm_gsnr_db_mean"].max()))
            plt.plot([lo, hi], [lo, hi], linestyle="--")
            plt.xlabel("GN-style GSNR estimate (dB)")
            plt.ylabel("SSFM GSNR mean (dB)")
            plt.title("Internal GN-style sanity benchmark")
            plt.grid(True, alpha=0.3)
            savefig("fig_day9_gn_style_gsnr_comparison")

    gain_path = tables_dir / "day9_raw_per_seed_paired_gains.csv"
    if gain_path.exists():
        df = pd.read_csv(gain_path)
        if not df.empty:
            plt.figure(figsize=(6.5, 4.2))
            labels = []
            values = []
            errors = []
            for _, r in df.sort_values("scenario_group").iterrows():
                labels.append(str(r["scenario_group"]))
                values.append(float(r["gmi_gain_mean"]))
                errors.append(float(r.get("gmi_gain_ci95", 0.0)))
            plt.bar(labels, values, yerr=errors, capsize=4)
            plt.xlabel("Scenario")
            plt.ylabel("Mean GMI gain")
            plt.title("Raw per-seed paired PCS gains at accepted points")
            plt.grid(True, axis="y", alpha=0.3)
            savefig("fig_day9_seed_gain_distribution")

    return out


def _write_reports(cfg: Dict, day9: Dict, tables_dir: Path, figures_dir: Path, reports_dir: Path, outputs: Dict[str, str], figures: Dict[str, str]) -> Dict[str, str]:
    acc = pd.read_csv(outputs["paired_gain"]) if "paired_gain" in outputs else pd.DataFrame()
    ssfm = pd.read_csv(outputs["ssfm_convergence"]) if "ssfm_convergence" in outputs else pd.DataFrame()
    sym = pd.read_csv(outputs["symbol_convergence"]) if "symbol_convergence" in outputs else pd.DataFrame()
    gn = pd.read_csv(outputs["gn_style_benchmark"]) if "gn_style_benchmark" in outputs else pd.DataFrame()
    ext = pd.read_csv(outputs["external_reference_check"]) if "external_reference_check" in outputs else pd.DataFrame()

    ssfm_pass = bool(ssfm.get("passes_convergence_gate", pd.Series([False])).all()) if not ssfm.empty and "passes_convergence_gate" in ssfm else False
    sym_pass = bool(sym.get("passes_convergence_gate", pd.Series([False])).all()) if not sym.empty and "passes_convergence_gate" in sym else False
    gn_rmse = float(gn["benchmark_rmse_db_over_grid"].iloc[0]) if not gn.empty and "benchmark_rmse_db_over_grid" in gn else float("nan")

    report_path = reports_dir / "day9_validation_report.md"
    latex_path = reports_dir / "day9_latex_validation_snippet.tex"
    checklist_path = reports_dir / "day9_reviewer_evidence_checklist.md"

    report = [
        "# Day-9 Publication-Strength Validation Report",
        "",
        "This run adds the minimum reviewer-facing validation outputs requested after the first Springer PNC draft review.",
        "It does not replace a full Raman/ISRS-calibrated C+S validation. It strengthens the current manuscript by adding raw per-seed evidence, SSFM step-size convergence, symbol-count convergence, and an internal GN-style GSNR sanity benchmark.",
        "",
        "## Generated tables",
    ]
    for k, v in outputs.items():
        report.append(f"- `{k}`: `{v}`")
    report += ["", "## Generated figures"]
    for k, v in figures.items():
        if k.endswith("_pdf"):
            continue
        report.append(f"- `{v}`")
    report += [
        "",
        "## Summary gates",
        f"- SSFM step convergence gate passed: `{ssfm_pass}`",
        f"- Symbol-count convergence gate passed: `{sym_pass}`",
        f"- Internal GN-style benchmark RMSE over grid: `{gn_rmse:.4f} dB`" if not math.isnan(gn_rmse) else "- Internal GN-style benchmark RMSE over grid: `not available`",
        "",
        "## Raw accepted-point paired gains",
        acc.round(6).to_markdown(index=False) if not acc.empty else "Raw paired gain table not found.",
        "",
        "## External reference check",
        ext.to_markdown(index=False) if not ext.empty else "External reference table not evaluated.",
        "",
        "## Correct manuscript claim after Day-9",
        "The manuscript can now state that the accepted C/S PCS gains are supported by repeated-seed paired comparisons and basic numerical convergence checks. If the optional GNPy/GN/EGN reference file is supplied, the paper can additionally report an external GSNR benchmark RMSE. Until then, the GN-style table must be described only as an internal analytical sanity check, not as a formal GNPy validation.",
    ]
    report_path.write_text("\n".join(report), encoding="utf-8")

    latex = r"""
\subsection{Additional numerical validation}
To strengthen the numerical reliability of the waveform-level PCS comparison, an additional Day-9 validation run was performed. The run exported raw per-seed accepted-point metrics, paired PCS-minus-uniform gains, SSFM step-size convergence data, symbol-count convergence data, and an internal GN-style GSNR sanity benchmark. The convergence tests vary the number of SSFM steps per span and the number of simulated symbols while keeping the accepted C and S operating points fixed. The paired-gain calculation compares PCS and uniform signaling at the same scenario, span count, launch power, and seed, which reduces random-seed bias in the reported gains.

The Day-9 validation is not claimed as a full Raman/ISRS-calibrated C+S WDM validation. Its purpose is to demonstrate that the principal single-band PCS conclusions are not produced by a single random seed or by one arbitrary numerical resolution. A formal external benchmark can be added by filling the generated \texttt{day9\_external\_reference\_template.csv} file with GNPy, GN, or EGN reference GSNR values and rerunning the validation script.
""".strip() + "\n"
    latex_path.write_text(latex, encoding="utf-8")

    checklist = textwrap.dedent(
        """
        # Day-9 Reviewer Evidence Checklist

        Use these outputs to upgrade the paper before resubmission:

        1. Add the raw per-seed paired-gain table as supplementary data.
        2. Add the SSFM step-size convergence figure to the validation section.
        3. Add the symbol-count convergence figure to the validation section.
        4. Add the GN-style GSNR plot only as an internal sanity benchmark unless an external GNPy/GN/EGN CSV is provided.
        5. Keep the C+S limitation. Do not rewrite the simplified C+S stress result as full Raman/ISRS validation.
        6. Archive the exact GitHub commit used for Day-8 + Day-9 output before final Springer upload.
        """
    ).strip() + "\n"
    checklist_path.write_text(checklist, encoding="utf-8")
    return {"validation_report": str(report_path), "latex_snippet": str(latex_path), "reviewer_checklist": str(checklist_path)}


def run_day9_publication_validation(cfg: Dict) -> Dict:
    day9 = _day9_cfg(cfg)
    tables_dir = ensure_dir(Path(cfg["output"]["tables"]))
    figures_dir = ensure_dir(Path(cfg["output"]["figures"]))
    reports_dir = ensure_dir(Path(cfg["output"]["reports"]))

    outputs: Dict[str, str] = {}
    outputs.update(_run_raw_per_seed(cfg, day9, tables_dir))

    if bool(day9["ssfm_convergence"].get("enabled", True)):
        outputs.update(_run_ssfm_convergence(cfg, day9, tables_dir))
    if bool(day9["symbol_convergence"].get("enabled", True)):
        outputs.update(_run_symbol_convergence(cfg, day9, tables_dir))
    if bool(day9["gn_style_benchmark"].get("enabled", True)):
        outputs.update(_run_gn_style_benchmark(cfg, day9, tables_dir))
    if bool(day9["external_reference"].get("enabled", True)):
        outputs.update(_run_external_reference_check(cfg, day9, tables_dir))

    figures = _plot_outputs(tables_dir, figures_dir)
    reports = _write_reports(cfg, day9, tables_dir, figures_dir, reports_dir, outputs, figures)

    return {"tables": outputs, "figures": figures, "reports": reports}
