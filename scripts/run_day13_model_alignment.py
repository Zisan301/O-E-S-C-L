#!/usr/bin/env python
"""
Day-13 model alignment and calibrated validation for O-E-S-C-L.

This script is intentionally conservative. It does not replace or fabricate
external GNPy values. It reads the Day-11 error table generated after the
Day-12 matched-GNPy run, diagnoses the mismatch, and evaluates whether a
simple band-dependent launch-power correction can be validated on held-out
launch powers.

Run from project root:
    python scripts/run_day13_model_alignment.py --config config/day13_model_alignment_config.yaml
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None


REQUIRED_COLUMNS = [
    "scenario_group",
    "band",
    "spans",
    "launch_power_dbm",
    "oesc_uniform_gsnr_mean_db",
    "reference_gsnr_db",
]


def read_config(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required. Install with: pip install pyyaml")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def metrics(errors: Iterable[float]) -> Dict[str, float]:
    arr = np.asarray(list(errors), dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {"n": 0, "rmse_db": math.nan, "mae_db": math.nan, "max_abs_db": math.nan, "bias_db": math.nan}
    return {
        "n": int(arr.size),
        "rmse_db": float(np.sqrt(np.mean(arr ** 2))),
        "mae_db": float(np.mean(np.abs(arr))),
        "max_abs_db": float(np.max(np.abs(arr))),
        "bias_db": float(np.mean(arr)),
    }


def load_errors(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Day-11 error table not found: {path}. Run Day-11 after Day-12 first."
        )
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise RuntimeError(f"Input file is missing required columns: {missing}")
    for col in ["spans", "launch_power_dbm", "oesc_uniform_gsnr_mean_db", "reference_gsnr_db"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["launch_power_dbm", "oesc_uniform_gsnr_mean_db", "reference_gsnr_db"]).copy()
    if df.empty:
        raise RuntimeError("No valid numeric O-E-S-C-L/reference GSNR rows found.")
    if "case_id" not in df.columns:
        df["case_id"] = df.apply(
            lambda r: f"{r['scenario_group']}-{r['band']}-{int(r['spans'])}sp-{r['launch_power_dbm']:+.1f}dBm",
            axis=1,
        )
    df["uncalibrated_error_db"] = df["oesc_uniform_gsnr_mean_db"] - df["reference_gsnr_db"]
    df["abs_uncalibrated_error_db"] = df["uncalibrated_error_db"].abs()
    # Correction needed to map O-E-S-C-L to reference.
    df["needed_correction_db"] = df["reference_gsnr_db"] - df["oesc_uniform_gsnr_mean_db"]
    df = df.sort_values(["band", "spans", "launch_power_dbm"]).reset_index(drop=True)
    return df


def fit_band_linear_correction(train: pd.DataFrame) -> Tuple[float, float]:
    """Fit needed_correction_db = intercept + slope * launch_power_dbm."""
    x = train["launch_power_dbm"].to_numpy(dtype=float)
    y = train["needed_correction_db"].to_numpy(dtype=float)
    if len(train) == 1:
        return float(y[0]), 0.0
    X = np.column_stack([np.ones_like(x), x])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    return float(beta[0]), float(beta[1])


def apply_correction(df: pd.DataFrame, intercept: float, slope: float) -> pd.DataFrame:
    out = df.copy()
    out["calibration_intercept_db"] = intercept
    out["calibration_slope_db_per_dbm"] = slope
    out["applied_correction_db"] = intercept + slope * out["launch_power_dbm"]
    out["calibrated_oesc_gsnr_db"] = out["oesc_uniform_gsnr_mean_db"] + out["applied_correction_db"]
    out["calibrated_error_db"] = out["calibrated_oesc_gsnr_db"] - out["reference_gsnr_db"]
    out["abs_calibrated_error_db"] = out["calibrated_error_db"].abs()
    return out


def primary_holdout_protocol(df: pd.DataFrame, cal_powers: List[float], val_powers: List[float]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    rows: List[pd.DataFrame] = []
    coeffs: List[Dict[str, Any]] = []
    for band, g in df.groupby("band", sort=True):
        train = g[g["launch_power_dbm"].isin(cal_powers)].copy()
        test = g[g["launch_power_dbm"].isin(val_powers)].copy()
        if train.empty or test.empty:
            raise RuntimeError(f"Band {band}: missing calibration or validation rows for primary protocol.")
        intercept, slope = fit_band_linear_correction(train)
        train_pred = apply_correction(train, intercept, slope)
        train_pred["set"] = "calibration"
        test_pred = apply_correction(test, intercept, slope)
        test_pred["set"] = "heldout_validation"
        combined = pd.concat([train_pred, test_pred], ignore_index=True)
        combined["protocol"] = "low_power_to_high_power_holdout"
        rows.append(combined)
        coeffs.append({
            "protocol": "low_power_to_high_power_holdout",
            "band": band,
            "calibration_powers_dbm": ",".join(str(int(p)) if float(p).is_integer() else str(p) for p in cal_powers),
            "validation_powers_dbm": ",".join(str(int(p)) if float(p).is_integer() else str(p) for p in val_powers),
            "intercept_db": intercept,
            "slope_db_per_dbm": slope,
            "n_calibration_cases": int(len(train)),
            "n_validation_cases": int(len(test)),
        })
    return pd.concat(rows, ignore_index=True), pd.DataFrame(coeffs)


def lopo_protocol(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    rows: List[pd.DataFrame] = []
    coeffs: List[Dict[str, Any]] = []
    for band, g in df.groupby("band", sort=True):
        powers = sorted(g["launch_power_dbm"].unique())
        if len(powers) < 3:
            raise RuntimeError(f"Band {band}: leave-one-power-out needs at least 3 powers.")
        for holdout_power in powers:
            train = g[g["launch_power_dbm"] != holdout_power].copy()
            test = g[g["launch_power_dbm"] == holdout_power].copy()
            intercept, slope = fit_band_linear_correction(train)
            pred = apply_correction(test, intercept, slope)
            pred["protocol"] = "leave_one_power_out"
            pred["set"] = "heldout_validation"
            pred["holdout_power_dbm"] = holdout_power
            pred["training_powers_dbm"] = ",".join(str(int(p)) if float(p).is_integer() else str(p) for p in sorted(train["launch_power_dbm"].unique()))
            rows.append(pred)
            coeffs.append({
                "protocol": "leave_one_power_out",
                "band": band,
                "holdout_power_dbm": holdout_power,
                "training_powers_dbm": pred["training_powers_dbm"].iloc[0],
                "intercept_db": intercept,
                "slope_db_per_dbm": slope,
                "n_training_cases": int(len(train)),
                "n_validation_cases": int(len(test)),
            })
    return pd.concat(rows, ignore_index=True), pd.DataFrame(coeffs)


def all_case_insample_protocol(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    rows: List[pd.DataFrame] = []
    coeffs: List[Dict[str, Any]] = []
    for band, g in df.groupby("band", sort=True):
        intercept, slope = fit_band_linear_correction(g)
        pred = apply_correction(g, intercept, slope)
        pred["protocol"] = "all_case_band_linear_insample"
        pred["set"] = "in_sample_diagnostic_only"
        rows.append(pred)
        coeffs.append({
            "protocol": "all_case_band_linear_insample",
            "band": band,
            "intercept_db": intercept,
            "slope_db_per_dbm": slope,
            "n_cases": int(len(g)),
        })
    return pd.concat(rows, ignore_index=True), pd.DataFrame(coeffs)


def summarize_protocols(
    uncalibrated: pd.DataFrame,
    primary: pd.DataFrame,
    lopo: pd.DataFrame,
    insample: pd.DataFrame,
    cfg: Dict[str, Any],
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    m = metrics(uncalibrated["uncalibrated_error_db"])
    rows.append({
        "protocol": "uncalibrated_direct_gnpy_reference",
        "set": "all_cases",
        **m,
        "rmse_gate_db": cfg["thresholds"]["primary_holdout_rmse_pass_db"],
        "max_abs_gate_db": cfg["thresholds"]["primary_holdout_max_abs_pass_db"],
        "passed": False,
        "interpretation": "Direct uncalibrated reference comparison; expected to remain failed after Day-12.",
    })

    for set_name, group in primary.groupby("set"):
        m = metrics(group["calibrated_error_db"])
        is_holdout = set_name == "heldout_validation"
        passed = False
        if is_holdout:
            passed = (
                m["rmse_db"] <= float(cfg["thresholds"]["primary_holdout_rmse_pass_db"])
                and m["max_abs_db"] <= float(cfg["thresholds"]["primary_holdout_max_abs_pass_db"])
            )
        rows.append({
            "protocol": "low_power_to_high_power_holdout",
            "set": set_name,
            **m,
            "rmse_gate_db": cfg["thresholds"]["primary_holdout_rmse_pass_db"] if is_holdout else math.nan,
            "max_abs_gate_db": cfg["thresholds"]["primary_holdout_max_abs_pass_db"] if is_holdout else math.nan,
            "passed": passed if is_holdout else "diagnostic",
            "interpretation": "Primary held-out calibrated validation." if is_holdout else "Calibration fit quality only; not validation.",
        })

    m = metrics(lopo["calibrated_error_db"])
    rows.append({
        "protocol": "leave_one_power_out",
        "set": "heldout_validation_all_folds",
        **m,
        "rmse_gate_db": cfg["thresholds"]["lopo_rmse_pass_db"],
        "max_abs_gate_db": cfg["thresholds"]["lopo_max_abs_pass_db"],
        "passed": (
            m["rmse_db"] <= float(cfg["thresholds"]["lopo_rmse_pass_db"])
            and m["max_abs_db"] <= float(cfg["thresholds"]["lopo_max_abs_pass_db"])
        ),
        "interpretation": "Cross-validation stability check using held-out launch powers.",
    })

    m = metrics(insample["calibrated_error_db"])
    rows.append({
        "protocol": "all_case_band_linear_insample",
        "set": "in_sample_diagnostic_only",
        **m,
        "rmse_gate_db": math.nan,
        "max_abs_gate_db": math.nan,
        "passed": "diagnostic",
        "interpretation": "All-case in-sample diagnostic; do not present as validation.",
    })

    return pd.DataFrame(rows)


def write_report(
    path: Path,
    df: pd.DataFrame,
    primary: pd.DataFrame,
    lopo: pd.DataFrame,
    coeffs: pd.DataFrame,
    summary: pd.DataFrame,
    cfg: Dict[str, Any],
) -> None:
    ensure_dir(path.parent)
    uncal = metrics(df["uncalibrated_error_db"])
    primary_holdout = summary[(summary["protocol"] == "low_power_to_high_power_holdout") & (summary["set"] == "heldout_validation")].iloc[0]
    lopo_row = summary[(summary["protocol"] == "leave_one_power_out")].iloc[0]
    primary_pass = bool(primary_holdout["passed"])
    lopo_pass = bool(lopo_row["passed"])
    final_status = primary_pass and lopo_pass

    lines: List[str] = []
    lines.append("# Day-13 Model Alignment and Calibrated Validation Report")
    lines.append("")
    lines.append("Day-13 evaluates whether the Day-12 GNPy mismatch can be handled with a transparent band-dependent launch-power correction. It does not replace or fabricate GNPy values.")
    lines.append("")
    lines.append("## Summary gate")
    lines.append("")
    lines.append(f"- Direct uncalibrated GNPy gate passed: `False`")
    lines.append(f"- Direct uncalibrated RMSE: `{uncal['rmse_db']:.4f} dB`")
    lines.append(f"- Primary calibrated held-out gate passed: `{primary_pass}`")
    lines.append(f"- Primary held-out RMSE: `{float(primary_holdout['rmse_db']):.4f} dB`")
    lines.append(f"- Primary held-out MAE: `{float(primary_holdout['mae_db']):.4f} dB`")
    lines.append(f"- Primary held-out max absolute error: `{float(primary_holdout['max_abs_db']):.4f} dB`")
    lines.append(f"- Leave-one-power-out gate passed: `{lopo_pass}`")
    lines.append(f"- Leave-one-power-out RMSE: `{float(lopo_row['rmse_db']):.4f} dB`")
    lines.append(f"- Leave-one-power-out max absolute error: `{float(lopo_row['max_abs_db']):.4f} dB`")
    lines.append(f"- Overall calibrated validation status: `{'passed' if final_status else 'not_passed'}`")
    lines.append("")
    lines.append("## Calibration model")
    lines.append("")
    lines.append("The correction is fitted separately for each band:")
    lines.append("")
    lines.append("```text")
    lines.append("G_calibrated(P, band) = G_OESC(P, band) + a_band + b_band * P")
    lines.append("```")
    lines.append("")
    lines.append("where `P` is launch power in dBm. The primary protocol fits `a_band` and `b_band` using -2 and 0 dBm, then validates on held-out +2 and +4 dBm cases.")
    lines.append("")
    lines.append("## Primary calibration coefficients")
    lines.append("")
    primary_coeffs = coeffs[coeffs["protocol"] == "low_power_to_high_power_holdout"].copy()
    primary_cols = [
        "protocol", "band", "calibration_powers_dbm", "validation_powers_dbm",
        "intercept_db", "slope_db_per_dbm", "n_calibration_cases", "n_validation_cases"
    ]
    lines.append(primary_coeffs[primary_cols].to_markdown(index=False))
    lines.append("")
    lines.append("## Protocol summary")
    lines.append("")
    lines.append(summary.to_markdown(index=False))
    lines.append("")
    lines.append("## Primary held-out validation predictions")
    lines.append("")
    cols = [
        "band", "spans", "launch_power_dbm", "set", "oesc_uniform_gsnr_mean_db",
        "reference_gsnr_db", "applied_correction_db", "calibrated_oesc_gsnr_db",
        "calibrated_error_db", "abs_calibrated_error_db"
    ]
    lines.append(primary[cols].sort_values(["band", "launch_power_dbm"]).to_markdown(index=False))
    lines.append("")
    lines.append("## Diagnostic interpretation")
    lines.append("")
    lines.append("- The raw Day-12 GNPy comparison should not be described as direct agreement because the uncalibrated RMSE remains high.")
    lines.append("- The errors are power-dependent, so a constant offset alone is not a sufficient physical explanation.")
    lines.append("- The calibrated result can be used only as a calibrated-alignment claim, not as a claim that the raw simulator directly reproduces GNPy.")
    lines.append("- The C+S scenario remains a simplified stress case unless separately validated with Raman/ISRS-aware reference data.")
    lines.append("")
    lines.append("## Correct manuscript claim")
    lines.append("")
    if final_status:
        lines.append("> A band-dependent launch-power correction was fitted using low-power calibration cases and evaluated on held-out high-power cases. The calibrated O-E-S-C-L predictions agreed with the matched GNPy reference within the reported held-out error bounds.")
    else:
        lines.append("> The calibrated alignment did not pass the selected gate. The manuscript should report the mismatch as a limitation and avoid claiming GNPy-validated agreement.")
    lines.append("")
    lines.append("## Generated outputs")
    lines.append("")
    lines.append("- `results/tables/day13_uncalibrated_errors.csv`")
    lines.append("- `results/tables/day13_calibration_coefficients.csv`")
    lines.append("- `results/tables/day13_primary_holdout_predictions.csv`")
    lines.append("- `results/tables/day13_lopo_predictions.csv`")
    lines.append("- `results/tables/day13_protocol_summary.csv`")
    lines.append("- `results/figures/fig_day13_uncalibrated_vs_calibrated_errors.png`")
    lines.append("- `results/figures/fig_day13_correction_vs_power.png`")
    lines.append("- `results/figures/fig_day13_lopo_errors.png`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex_snippet(path: Path, summary: pd.DataFrame, coeffs: pd.DataFrame) -> None:
    ensure_dir(path.parent)
    primary = summary[(summary["protocol"] == "low_power_to_high_power_holdout") & (summary["set"] == "heldout_validation")].iloc[0]
    lopo = summary[(summary["protocol"] == "leave_one_power_out")].iloc[0]
    text = rf"""
\subsection{{GNPy-Calibrated Model Alignment}}
Direct uncalibrated comparison with the matched GNPy reference showed a remaining power-dependent GSNR deviation. Therefore, a band-dependent launch-power correction was evaluated rather than claiming direct raw agreement. The calibrated GSNR was computed as
\begin{{equation}}
G_{{\mathrm{{cal}}}}(P,b)=G_{{\mathrm{{OESC}}}}(P,b)+a_b+b_bP,
\end{{equation}}
where $P$ is the launch power in dBm and $a_b,b_b$ are fitted separately for each band. The primary calibration used the low-power cases ($-2$ and $0$ dBm) and evaluated the fitted correction on held-out high-power cases ($+2$ and $+4$ dBm). The held-out calibrated RMSE was {float(primary['rmse_db']):.3f} dB, with MAE {float(primary['mae_db']):.3f} dB and maximum absolute error {float(primary['max_abs_db']):.3f} dB. Leave-one-power-out validation gave RMSE {float(lopo['rmse_db']):.3f} dB and maximum absolute error {float(lopo['max_abs_db']):.3f} dB. This supports a calibrated-alignment claim, while the uncalibrated mismatch is retained as a limitation.
""".strip()
    path.write_text(text + "\n", encoding="utf-8")


def make_figures(
    figures_dir: Path,
    df: pd.DataFrame,
    primary: pd.DataFrame,
    lopo: pd.DataFrame,
) -> None:
    ensure_dir(figures_dir)
    if plt is None:
        return

    # 1) Uncalibrated vs calibrated errors for the primary protocol.
    fig_path = figures_dir / "fig_day13_uncalibrated_vs_calibrated_errors.png"
    p = primary.sort_values(["band", "launch_power_dbm"]).copy()
    labels = [f"{r.band} {int(r.spans)}sp {r.launch_power_dbm:+.0f} dBm" for r in p.itertuples()]
    x = np.arange(len(p))
    width = 0.38
    plt.figure(figsize=(10, 4.8))
    plt.bar(x - width / 2, p["uncalibrated_error_db"], width, label="Uncalibrated")
    plt.bar(x + width / 2, p["calibrated_error_db"], width, label="Calibrated")
    plt.axhline(0, linewidth=1)
    plt.xticks(x, labels, rotation=25, ha="right")
    plt.ylabel("GSNR error (dB)")
    plt.xlabel("Validation case")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=220)
    plt.close()

    # 2) Needed correction vs power with fitted primary lines.
    fig_path = figures_dir / "fig_day13_correction_vs_power.png"
    plt.figure(figsize=(7.5, 4.8))
    for band, g in p.groupby("band"):
        plt.scatter(g["launch_power_dbm"], g["needed_correction_db"], label=f"{band} needed correction")
        # Use the primary fit stored on rows.
        intercept = float(g["calibration_intercept_db"].iloc[0])
        slope = float(g["calibration_slope_db_per_dbm"].iloc[0])
        xs = np.linspace(float(g["launch_power_dbm"].min()), float(g["launch_power_dbm"].max()), 50)
        ys = intercept + slope * xs
        plt.plot(xs, ys, label=f"{band} fitted correction")
    plt.axhline(0, linewidth=1)
    plt.xlabel("Launch power (dBm)")
    plt.ylabel("Reference - O-E-S-C-L GSNR (dB)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=220)
    plt.close()

    # 3) LOPO errors.
    fig_path = figures_dir / "fig_day13_lopo_errors.png"
    l = lopo.sort_values(["band", "launch_power_dbm"]).copy()
    labels = [f"{r.band} {r.launch_power_dbm:+.0f} dBm" for r in l.itertuples()]
    x = np.arange(len(l))
    plt.figure(figsize=(9.5, 4.6))
    plt.bar(x, l["calibrated_error_db"], label="LOPO calibrated error")
    plt.axhline(0, linewidth=1)
    plt.xticks(x, labels, rotation=25, ha="right")
    plt.ylabel("GSNR error (dB)")
    plt.xlabel("Held-out power case")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=220)
    plt.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to Day-13 YAML config")
    args = parser.parse_args()

    cfg_path = Path(args.config)
    cfg = read_config(cfg_path)
    root = Path(cfg.get("project", {}).get("root", ".")).resolve()

    tables_dir = root / cfg["output"]["tables_dir"]
    reports_dir = root / cfg["output"]["reports_dir"]
    figures_dir = root / cfg["output"]["figures_dir"]
    ensure_dir(tables_dir)
    ensure_dir(reports_dir)
    ensure_dir(figures_dir)

    errors_path = root / cfg["input"]["day11_errors_csv"]
    df = load_errors(errors_path)

    cal_powers = [float(x) for x in cfg["calibration"]["calibration_powers_dbm"]]
    val_powers = [float(x) for x in cfg["calibration"]["validation_powers_dbm"]]

    primary, primary_coeffs = primary_holdout_protocol(df, cal_powers, val_powers)
    lopo, lopo_coeffs = lopo_protocol(df)
    insample, insample_coeffs = all_case_insample_protocol(df)
    coeffs = pd.concat([primary_coeffs, lopo_coeffs, insample_coeffs], ignore_index=True, sort=False)
    summary = summarize_protocols(df, primary, lopo, insample, cfg)

    df.to_csv(tables_dir / "day13_uncalibrated_errors.csv", index=False)
    coeffs.to_csv(tables_dir / "day13_calibration_coefficients.csv", index=False)
    primary.to_csv(tables_dir / "day13_primary_holdout_predictions.csv", index=False)
    lopo.to_csv(tables_dir / "day13_lopo_predictions.csv", index=False)
    insample.to_csv(tables_dir / "day13_all_case_insample_predictions.csv", index=False)
    summary.to_csv(tables_dir / "day13_protocol_summary.csv", index=False)

    report_path = root / cfg["output"]["report_md"]
    latex_path = root / cfg["output"]["latex_snippet"]
    write_report(report_path, df, primary, lopo, coeffs, summary, cfg)
    write_latex_snippet(latex_path, summary, coeffs)
    make_figures(figures_dir, df, primary, lopo)

    primary_row = summary[(summary["protocol"] == "low_power_to_high_power_holdout") & (summary["set"] == "heldout_validation")].iloc[0]
    lopo_row = summary[summary["protocol"] == "leave_one_power_out"].iloc[0]
    final_pass = bool(primary_row["passed"]) and bool(lopo_row["passed"])

    print("\nO-E-S-C-L Day-13 model alignment completed.")
    print(f"Report: {report_path}")
    print(f"LaTeX snippet: {latex_path}")
    print(f"Protocol summary: {tables_dir / 'day13_protocol_summary.csv'}")
    print(f"Primary calibrated held-out gate: {'PASSED' if bool(primary_row['passed']) else 'FAILED'}")
    print(f"LOPO calibrated gate: {'PASSED' if bool(lopo_row['passed']) else 'FAILED'}")
    print(f"Overall calibrated validation: {'PASSED' if final_pass else 'NOT PASSED'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
