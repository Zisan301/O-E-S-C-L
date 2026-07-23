from __future__ import annotations

import argparse
import copy
import math
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.oescl.config import load_config
from src.oescl.utils import ensure_dir, set_global_seed
from src.oescl.day8_q3_band_comparison import _run_one, _scenario_bands


METRICS = ["gmi", "ngmi", "ber", "gsnr_db", "rate_tbps", "rate_tbps_per_channel"]


def load_day10_config(path: str) -> Dict:
    cfg_path = Path(path)
    if not cfg_path.is_absolute():
        cfg_path = PROJECT_ROOT / cfg_path
    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def prepare_base_config(day10_cfg: Dict) -> Dict:
    base_path = Path(day10_cfg.get("base_config", "config/day8_q3_band_comparison_config.yaml"))
    if not base_path.is_absolute():
        base_path = PROJECT_ROOT / base_path
    cfg = load_config(str(base_path))
    return cfg


def point_list(day10_cfg: Dict) -> List[Dict]:
    d10 = day10_cfg["day10"]
    pts = list(d10["accepted_points"])
    if bool(d10.get("include_cs_stress_case", False)):
        pts.append(dict(d10["cs_point"]))
    return pts


def aggregate_seed_trial(cfg: Dict, seed: int, point: Dict, nu: float, symbol_count: int, steps_per_span: int) -> Dict:
    scenario = str(point["scenario_group"])
    spans = int(point["spans"])
    power = float(point["launch_power_dbm"])
    local = copy.deepcopy(cfg)
    local["day8"]["symbols"] = int(symbol_count)
    local["day5"]["ssfm_steps_per_span"] = int(steps_per_span)

    band_rows = []
    for band in _scenario_bands(scenario):
        band_rows.append(_run_one(seed, scenario, band, spans, power, float(nu), local))

    df = pd.DataFrame(band_rows)
    shaped = bool(float(nu) > 0.0)
    row = {
        "seed": int(seed),
        "scenario_group": scenario,
        "spans": spans,
        "launch_power_dbm": power,
        "pcs_nu": float(nu),
        "shaped": shaped,
        "scenario": "pcs_raw" if shaped else "uniform_raw",
        "symbol_count": int(symbol_count),
        "ssfm_steps_per_span": int(steps_per_span),
        "n_bands": int(df["band"].nunique()),
        "bands": "+".join(sorted(df["band"].astype(str).unique())),
    }

    for m in ["gmi", "ngmi", "ber", "gsnr_db"]:
        row[m] = float(df[m].mean())

    # Aggregate rate across represented bands. Per-channel rate is the mean.
    row["rate_tbps"] = float(df["rate_tbps"].sum())
    row["rate_tbps_per_channel"] = float(df["rate_tbps"].mean())

    return row


def paired_gain(seed_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    keys = ["scenario_group", "spans", "launch_power_dbm", "symbol_count", "ssfm_steps_per_span"]
    uniform = seed_df[(seed_df["scenario"] == "uniform_raw") & (seed_df["pcs_nu"] == 0.0)].copy()
    pcs_all = seed_df[seed_df["scenario"] == "pcs_raw"].copy()

    for key_values, base in uniform.groupby(keys):
        key_filter = dict(zip(keys, key_values))
        pcs = pcs_all.copy()
        for k, v in key_filter.items():
            pcs = pcs[pcs[k] == v]
        if pcs.empty:
            continue

        for nu, pcsg in pcs.groupby("pcs_nu"):
            merged = pcsg.merge(
                base[["seed"] + METRICS],
                on="seed",
                suffixes=("_pcs", "_uniform"),
            )
            if merged.empty:
                continue
            row = dict(key_filter)
            row["pcs_nu"] = float(nu)
            row["n_pairs"] = int(len(merged))
            for m in METRICS:
                diff = merged[f"{m}_pcs"].astype(float).to_numpy() - merged[f"{m}_uniform"].astype(float).to_numpy()
                sd = float(np.std(diff, ddof=1)) if len(diff) > 1 else 0.0
                row[f"{m}_delta_mean"] = float(np.mean(diff))
                row[f"{m}_delta_std"] = sd
                row[f"{m}_delta_ci95"] = float(1.96 * sd / math.sqrt(max(len(diff), 1)))
            # Aliases for paper-friendly names.
            row["gmi_gain_mean"] = row["gmi_delta_mean"]
            row["gmi_gain_ci95"] = row["gmi_delta_ci95"]
            row["ngmi_gain_mean"] = row["ngmi_delta_mean"]
            row["ngmi_gain_ci95"] = row["ngmi_delta_ci95"]
            row["ber_delta_mean"] = row["ber_delta_mean"]
            row["ber_delta_ci95"] = row["ber_delta_ci95"]
            row["rate_gain_mean"] = row["rate_tbps_per_channel_delta_mean"]
            row["rate_gain_ci95"] = row["rate_tbps_per_channel_delta_ci95"]
            row["aggregate_rate_gain_mean"] = row["rate_tbps_delta_mean"]
            row["aggregate_rate_gain_ci95"] = row["rate_tbps_delta_ci95"]
            rows.append(row)
    return pd.DataFrame(rows)


def summarize_symbol_stability(gain_df: pd.DataFrame, day10_cfg: Dict) -> pd.DataFrame:
    d10 = day10_cfg["day10"]
    gate = d10["stability_gate"]
    max_abs = float(gate["max_abs_gmi_gain_drift"])
    max_rel = float(gate["max_rel_gmi_gain_drift"])
    require_positive = bool(gate.get("require_positive_gain_at_largest_count", True))
    rows = []

    for scenario, g in gain_df.groupby("scenario_group"):
        g = g.sort_values("symbol_count")
        counts = sorted(g["symbol_count"].unique())
        if len(counts) < 2:
            rows.append({
                "scenario_group": scenario,
                "passed_symbol_stability": False,
                "reason": "fewer_than_two_symbol_counts",
            })
            continue
        low_count, high_count = counts[-2], counts[-1]
        low = g[g["symbol_count"] == low_count].iloc[0]
        high = g[g["symbol_count"] == high_count].iloc[0]
        drift = float(high["gmi_gain_mean"] - low["gmi_gain_mean"])
        abs_drift = abs(drift)
        rel_drift = abs_drift / max(abs(float(high["gmi_gain_mean"])), 1e-12)
        positive = float(high["gmi_gain_mean"]) > 0.0
        passed = bool(abs_drift <= max_abs and rel_drift <= max_rel and (positive or not require_positive))
        reason = "passed" if passed else "failed"
        rows.append({
            "scenario_group": scenario,
            "low_symbol_count": int(low_count),
            "high_symbol_count": int(high_count),
            "low_gmi_gain": float(low["gmi_gain_mean"]),
            "high_gmi_gain": float(high["gmi_gain_mean"]),
            "gmi_gain_drift": drift,
            "abs_gmi_gain_drift": abs_drift,
            "relative_gmi_gain_drift": rel_drift,
            "largest_count_positive_gain": positive,
            "passed_symbol_stability": passed,
            "reason": reason,
        })
    return pd.DataFrame(rows)


def internal_gn_reference(seed_df: pd.DataFrame, points: List[Dict], day10_cfg: Dict) -> pd.DataFrame:
    """Create a transparent internal analytical sanity reference.

    This is not GNPy. It is a simple GN-like attenuation/noise/nonlinear trend
    calculation intended to catch obviously inconsistent GSNR trends.
    """
    rows = []
    largest_symbol = int(max(day10_cfg["day10"]["symbol_counts"]))
    steps = int(day10_cfg["day10"]["ssfm_steps_per_span"])
    for point in points:
        scenario = str(point["scenario_group"])
        for band in _scenario_bands(scenario):
            # Use uniform waveform at the largest symbol count as the SSFM-side comparison.
            filt = (
                (seed_df["scenario_group"] == scenario)
                & (seed_df["symbol_count"] == largest_symbol)
                & (seed_df["ssfm_steps_per_span"] == steps)
                & (seed_df["scenario"] == "uniform_raw")
            )
            ssfm_gsnr = float(seed_df[filt]["gsnr_db"].mean()) if seed_df[filt].shape[0] else np.nan
            spans = int(point["spans"])
            power = float(point["launch_power_dbm"])

            # Conservative monotone GN-style proxy. It is calibrated only as a sanity trend,
            # not as a publication-grade external reference.
            band_penalty = 0.0 if band == "C" else 0.7
            length_penalty = 0.018 * spans * 80.0
            nonlinear_penalty = 0.06 * spans * (10 ** (power / 10.0))
            reference_gsnr = 24.0 - length_penalty - nonlinear_penalty - band_penalty
            rows.append({
                "scenario_group": scenario,
                "band": band,
                "spans": spans,
                "launch_power_dbm": power,
                "reference_model": "internal_GN_style_sanity_not_GNPy",
                "reference_gsnr_db": float(reference_gsnr),
                "oescl_uniform_gsnr_db": ssfm_gsnr,
                "gsnr_error_db": float(ssfm_gsnr - reference_gsnr) if np.isfinite(ssfm_gsnr) else np.nan,
            })
    return pd.DataFrame(rows)


def write_external_template(points: List[Dict], day10_cfg: Dict) -> Path:
    template_path = Path(day10_cfg["day10"]["external_reference"]["template_path"])
    if not template_path.is_absolute():
        template_path = PROJECT_ROOT / template_path
    template_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in points:
        scenario = str(p["scenario_group"])
        for band in _scenario_bands(scenario):
            rows.append({
                "scenario_group": scenario,
                "band": band,
                "spans": int(p["spans"]),
                "launch_power_dbm": float(p["launch_power_dbm"]),
                "reference_model": "GNPy",
                "reference_gsnr_db": "",
                "notes": "Fill with external GNPy/GN/EGN value and rerun Day-10.",
            })
    pd.DataFrame(rows).to_csv(template_path, index=False)
    return template_path


def check_external_reference(seed_df: pd.DataFrame, day10_cfg: Dict) -> pd.DataFrame:
    d10 = day10_cfg["day10"]
    expected = Path(d10["external_reference"]["expected_path"])
    if not expected.is_absolute():
        expected = PROJECT_ROOT / expected

    if not expected.exists():
        return pd.DataFrame([{
            "status": "reference_file_missing",
            "expected_csv_path": str(expected.relative_to(PROJECT_ROOT)),
            "message": "Copy validation_data/gnpy_day10_reference_template.csv to this path, fill reference_gsnr_db, and rerun Day-10.",
        }])

    ref = pd.read_csv(expected)
    needed = {"scenario_group", "band", "spans", "launch_power_dbm", "reference_model", "reference_gsnr_db"}
    missing = sorted(needed - set(ref.columns))
    if missing:
        return pd.DataFrame([{
            "status": "reference_file_invalid",
            "expected_csv_path": str(expected.relative_to(PROJECT_ROOT)),
            "message": "Missing columns: " + ", ".join(missing),
        }])

    largest_symbol = int(max(d10["symbol_counts"]))
    steps = int(d10["ssfm_steps_per_span"])
    rows = []
    for _, r in ref.iterrows():
        if pd.isna(r["reference_gsnr_db"]) or str(r["reference_gsnr_db"]).strip() == "":
            continue
        scenario = str(r["scenario_group"])
        filt = (
            (seed_df["scenario_group"] == scenario)
            & (seed_df["symbol_count"] == largest_symbol)
            & (seed_df["ssfm_steps_per_span"] == steps)
            & (seed_df["scenario"] == "uniform_raw")
        )
        if filt.sum() == 0:
            continue
        oescl = float(seed_df[filt]["gsnr_db"].mean())
        reference = float(r["reference_gsnr_db"])
        rows.append({
            "status": "reference_compared",
            "scenario_group": scenario,
            "band": str(r["band"]),
            "spans": int(r["spans"]),
            "launch_power_dbm": float(r["launch_power_dbm"]),
            "reference_model": str(r["reference_model"]),
            "reference_gsnr_db": reference,
            "oescl_uniform_gsnr_db": oescl,
            "gsnr_error_db": oescl - reference,
        })

    if not rows:
        return pd.DataFrame([{
            "status": "reference_file_present_but_empty",
            "expected_csv_path": str(expected.relative_to(PROJECT_ROOT)),
            "message": "reference_gsnr_db values were empty or no matching cases were found.",
        }])

    out = pd.DataFrame(rows)
    rmse = float(np.sqrt(np.mean(out["gsnr_error_db"].astype(float) ** 2)))
    passed = bool(rmse <= float(d10["external_reference"]["max_gsnr_rmse_db"]))
    out["external_gsnr_rmse_db"] = rmse
    out["passed_external_reference_gate"] = passed
    return out


def plot_outputs(gain_df: pd.DataFrame, stability_df: pd.DataFrame, seed_df: pd.DataFrame, internal_ref: pd.DataFrame, fig_dir: Path) -> List[Path]:
    import matplotlib.pyplot as plt

    paths = []

    # Symbol-count convergence
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for scenario, g in gain_df.groupby("scenario_group"):
        g = g.sort_values("symbol_count")
        ax.plot(g["symbol_count"], g["gmi_gain_mean"], marker="o", label=scenario)
    ax.set_xlabel("Symbols per trial")
    ax.set_ylabel("Mean paired GMI gain")
    ax.grid(True, alpha=0.35)
    ax.legend()
    p = fig_dir / "fig_day10_symbol_count_convergence.png"
    fig.tight_layout()
    fig.savefig(p, dpi=300)
    plt.close(fig)
    paths.append(p)

    # Relative error/drift
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    s = stability_df.copy()
    ax.bar(s["scenario_group"], s["relative_gmi_gain_drift"])
    ax.set_xlabel("Scenario")
    ax.set_ylabel("Relative drift between two largest symbol counts")
    ax.grid(True, axis="y", alpha=0.35)
    p = fig_dir / "fig_day10_symbol_count_relative_error.png"
    fig.tight_layout()
    fig.savefig(p, dpi=300)
    plt.close(fig)
    paths.append(p)

    # Seed gain distribution at largest symbol count
    largest_symbol = int(seed_df["symbol_count"].max())
    rows = []
    for (scenario, seed), g in seed_df[seed_df["symbol_count"] == largest_symbol].groupby(["scenario_group", "seed"]):
        uni = g[(g["scenario"] == "uniform_raw") & (g["pcs_nu"] == 0.0)]
        pcs = g[g["scenario"] == "pcs_raw"]
        if uni.empty or pcs.empty:
            continue
        rows.append({
            "scenario_group": scenario,
            "seed": int(seed),
            "gmi_gain": float(pcs.iloc[0]["gmi"] - uni.iloc[0]["gmi"]),
        })
    sg = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    if not sg.empty:
        labels = list(sg["scenario_group"].drop_duplicates())
        data = [sg[sg["scenario_group"] == lab]["gmi_gain"].to_numpy() for lab in labels]
        ax.boxplot(data, labels=labels, showmeans=True)
    ax.set_xlabel("Scenario")
    ax.set_ylabel("Per-seed paired GMI gain")
    ax.grid(True, axis="y", alpha=0.35)
    p = fig_dir / "fig_day10_seed_gain_distribution.png"
    fig.tight_layout()
    fig.savefig(p, dpi=300)
    plt.close(fig)
    paths.append(p)

    # Internal GN reference comparison
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    clean = internal_ref.dropna(subset=["reference_gsnr_db", "oescl_uniform_gsnr_db"])
    if not clean.empty:
        x = np.arange(len(clean))
        ax.plot(x, clean["oescl_uniform_gsnr_db"], marker="o", label="O-E-S-C-L uniform")
        ax.plot(x, clean["reference_gsnr_db"], marker="s", label="Internal GN-style")
        ax.set_xticks(x)
        ax.set_xticklabels(clean["scenario_group"] + "/" + clean["band"], rotation=0)
        ax.legend()
    ax.set_xlabel("Case")
    ax.set_ylabel("GSNR (dB)")
    ax.grid(True, alpha=0.35)
    p = fig_dir / "fig_day10_gn_reference_comparison.png"
    fig.tight_layout()
    fig.savefig(p, dpi=300)
    plt.close(fig)
    paths.append(p)

    return paths


def write_report(report_dir: Path, tables: Dict[str, Path], figs: List[Path], stability: pd.DataFrame, external: pd.DataFrame, internal_ref: pd.DataFrame) -> Path:
    report = report_dir / "day10_publication_validation_report.md"

    symbol_pass = bool(stability["passed_symbol_stability"].all()) if not stability.empty else False
    if "passed_external_reference_gate" in external.columns:
        external_pass = bool(external["passed_external_reference_gate"].iloc[0])
        ext_status = f"External reference gate passed: `{external_pass}`"
    else:
        ext_status = "External reference gate passed: `False`"

    internal_rmse = np.nan
    if not internal_ref.empty and "gsnr_error_db" in internal_ref:
        e = internal_ref["gsnr_error_db"].dropna().astype(float)
        if len(e):
            internal_rmse = float(np.sqrt(np.mean(e ** 2)))

    text = []
    text.append("# Day-10 Publication Validation Report\n")
    text.append("Day-10 strengthens the single-band C and S validation evidence after Day-9.\n")
    text.append("It focuses on larger symbol-count convergence, raw per-seed paired gains, and an optional external GNPy/GN/EGN reference check.\n")
    text.append("The C+S case remains a simplified stress scenario unless enabled and externally validated.\n")
    text.append("\n## Generated tables\n")
    for name, path in tables.items():
        text.append(f"- `{name}`: `{path}`")
    text.append("\n## Generated figures\n")
    for p in figs:
        text.append(f"- `{p}`")
    text.append("\n## Summary gates\n")
    text.append(f"- Symbol-count stability gate passed: `{symbol_pass}`")
    text.append(f"- {ext_status}")
    text.append(f"- Internal GN-style sanity RMSE: `{internal_rmse:.4f} dB`" if np.isfinite(internal_rmse) else "- Internal GN-style sanity RMSE: `not available`")
    text.append("\n## Symbol-count stability summary\n")
    text.append(stability.round(6).to_markdown(index=False))
    text.append("\n## External reference check\n")
    text.append(external.round(6).to_markdown(index=False))
    text.append("\n## Correct manuscript claim after Day-10\n")
    if symbol_pass and ("passed_external_reference_gate" in external.columns) and bool(external["passed_external_reference_gate"].iloc[0]):
        text.append("The manuscript can state that accepted C/S PCS gains are supported by larger-symbol repeated-seed convergence and by an external GSNR reference check. C+S should remain limited unless separately validated.")
    elif symbol_pass:
        text.append("The manuscript can state that accepted C/S PCS gains are supported by larger-symbol repeated-seed convergence. External validation is still incomplete, so the GN-style result must be described only as an internal analytical sanity check.")
    else:
        text.append("Do not submit yet. At least one C/S symbol-count stability gate failed. Increase symbol count, seed count, or investigate waveform/GMI variance before updating the manuscript.")

    report.write_text("\n".join(text), encoding="utf-8")
    return report


def write_latex_snippet(report_dir: Path, stability: pd.DataFrame, external: pd.DataFrame) -> Path:
    p = report_dir / "day10_validation_latex_snippet.tex"
    stable_cases = ", ".join(stability.loc[stability["passed_symbol_stability"] == True, "scenario_group"].astype(str).tolist()) if not stability.empty else "none"
    ext_phrase = "an external reference file was available" if "passed_external_reference_gate" in external.columns else "the external reference file was not available"
    text = rf"""\subsection{{Numerical convergence and reference checking}}
A Day-10 validation run was added for the accepted single-band operating points to reduce the risk that the PCS gain is an artifact of a short waveform simulation. The run repeated paired PCS-minus-uniform comparisons over larger symbol counts and compared the two largest symbol-count settings using an absolute and relative GMI-gain drift gate. The symbol-count stability gate passed for: {stable_cases}. In addition, {ext_phrase}. If no external GNPy/GN/EGN reference file is supplied, the analytical GSNR comparison is interpreted only as an internal sanity check and not as formal external validation.
"""
    p.write_text(text, encoding="utf-8")
    return p


def main() -> None:
    parser = argparse.ArgumentParser(description="O-E-S-C-L Day-10 publication validation.")
    parser.add_argument("--config", default="config/day10_validation_config.yaml")
    args = parser.parse_args()

    day10_cfg = load_day10_config(args.config)
    cfg = prepare_base_config(day10_cfg)
    set_global_seed(int(cfg["simulation"]["seed"]))

    d10 = day10_cfg["day10"]
    tables_dir = ensure_dir(PROJECT_ROOT / d10["output"]["tables"])
    figs_dir = ensure_dir(PROJECT_ROOT / d10["output"]["figures"])
    reports_dir = ensure_dir(PROJECT_ROOT / d10["output"]["reports"])

    points = point_list(day10_cfg)
    write_external_template(points, day10_cfg)

    rows = []
    for symbol_count in map(int, d10["symbol_counts"]):
        for point in points:
            for seed in map(int, d10["seeds"]):
                rows.append(aggregate_seed_trial(cfg, seed, point, 0.0, symbol_count, int(d10["ssfm_steps_per_span"])))
                rows.append(aggregate_seed_trial(cfg, seed, point, float(point["pcs_nu"]), symbol_count, int(d10["ssfm_steps_per_span"])))

    seed_df = pd.DataFrame(rows)
    gain_df = paired_gain(seed_df)
    stability_df = summarize_symbol_stability(gain_df, day10_cfg)

    # Optional step convergence check at fixed symbol count.
    step_rows = []
    if bool(d10.get("run_step_convergence_check", True)):
        for steps in map(int, d10["step_convergence_steps_per_span"]):
            for point in points:
                for seed in map(int, d10["seeds"]):
                    step_rows.append(aggregate_seed_trial(cfg, seed, point, 0.0, int(d10["step_convergence_symbols"]), steps))
                    step_rows.append(aggregate_seed_trial(cfg, seed, point, float(point["pcs_nu"]), int(d10["step_convergence_symbols"]), steps))
    step_df = pd.DataFrame(step_rows)
    step_gain = paired_gain(step_df) if not step_df.empty else pd.DataFrame()

    internal_ref = internal_gn_reference(seed_df, points, day10_cfg)
    external_check = check_external_reference(seed_df, day10_cfg)

    table_paths = {
        "raw_per_seed_metrics": tables_dir / "day10_raw_per_seed_metrics.csv",
        "raw_per_seed_paired_gains": tables_dir / "day10_raw_per_seed_paired_gains.csv",
        "symbol_count_convergence": tables_dir / "day10_symbol_count_convergence.csv",
        "symbol_count_stability_summary": tables_dir / "day10_symbol_count_stability_summary.csv",
        "step_convergence_metrics": tables_dir / "day10_step_convergence_metrics.csv",
        "step_convergence_paired_gains": tables_dir / "day10_step_convergence_paired_gains.csv",
        "internal_gn_reference": tables_dir / "day10_internal_gn_reference.csv",
        "external_reference_check": tables_dir / "day10_external_reference_check.csv",
    }

    seed_df.to_csv(table_paths["raw_per_seed_metrics"], index=False)
    gain_df.to_csv(table_paths["raw_per_seed_paired_gains"], index=False)
    gain_df.to_csv(table_paths["symbol_count_convergence"], index=False)
    stability_df.to_csv(table_paths["symbol_count_stability_summary"], index=False)
    step_df.to_csv(table_paths["step_convergence_metrics"], index=False)
    step_gain.to_csv(table_paths["step_convergence_paired_gains"], index=False)
    internal_ref.to_csv(table_paths["internal_gn_reference"], index=False)
    external_check.to_csv(table_paths["external_reference_check"], index=False)

    figs = plot_outputs(gain_df, stability_df, seed_df, internal_ref, figs_dir)
    report = write_report(reports_dir, table_paths, figs, stability_df, external_check, internal_ref)
    latex = write_latex_snippet(reports_dir, stability_df, external_check)

    print("\nO-E-S-C-L Day-10 publication validation completed.")
    print(f"Report: {report.resolve()}")
    print(f"LaTeX snippet: {latex.resolve()}")
    print("\nSend these files back:")
    print(report)
    print(table_paths["symbol_count_stability_summary"])
    print(table_paths["symbol_count_convergence"])
    print(table_paths["raw_per_seed_paired_gains"])
    print(table_paths["external_reference_check"])
    for fig in figs:
        print(fig)


if __name__ == "__main__":
    main()
