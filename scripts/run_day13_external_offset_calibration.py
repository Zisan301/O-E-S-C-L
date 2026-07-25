from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    in_csv = PROJECT_ROOT / "results/tables/day12_external_alignment_sweep.csv"
    out_csv = PROJECT_ROOT / "results/tables/day13_external_offset_calibration.csv"
    report_path = PROJECT_ROOT / "results/reports/day13_external_offset_calibration_report.md"
    latex_path = PROJECT_ROOT / "results/reports/day13_external_offset_calibration_latex_snippet.tex"

    if not in_csv.exists():
        raise FileNotFoundError("Missing Day-12 sweep CSV. Run Day-12 first.")

    df = pd.read_csv(in_csv)

    required = {
        "spans",
        "gnpy_reference_gsnr_db",
        "oescl_uniform_gsnr_mean_db",
        "gsnr_error_db",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise RuntimeError("Missing columns in Day-12 CSV: " + ", ".join(missing))

    df = df.sort_values("spans").copy()

    # Error convention from Day-12:
    # gsnr_error_db = OESCL - GNPy
    raw_errors = df["gsnr_error_db"].astype(float).to_numpy()

    # Constant offset needed to map OESCL absolute GSNR to GNPy scale:
    # corrected_oescl = oescl + offset
    offset_db = float(-np.mean(raw_errors))

    df["constant_offset_db"] = offset_db
    df["oescl_offset_calibrated_gsnr_db"] = (
        df["oescl_uniform_gsnr_mean_db"].astype(float) + offset_db
    )
    df["calibrated_error_db"] = (
        df["oescl_offset_calibrated_gsnr_db"].astype(float)
        - df["gnpy_reference_gsnr_db"].astype(float)
    )
    df["abs_calibrated_error_db"] = df["calibrated_error_db"].abs()

    raw_rmse = float(np.sqrt(np.mean(raw_errors ** 2)))
    raw_mean_error = float(np.mean(raw_errors))
    raw_std = float(np.std(raw_errors, ddof=1)) if len(raw_errors) > 1 else 0.0

    calibrated_errors = df["calibrated_error_db"].astype(float).to_numpy()
    calibrated_rmse = float(np.sqrt(np.mean(calibrated_errors ** 2)))
    calibrated_mae = float(np.mean(np.abs(calibrated_errors)))
    calibrated_max_abs = float(np.max(np.abs(calibrated_errors)))

    # Leave-one-out offset calibration:
    # For each span, estimate offset using all other spans, then test on held-out span.
    loo_rows = []
    for idx, row in df.iterrows():
        train = df.drop(index=idx)
        train_raw_errors = train["gsnr_error_db"].astype(float).to_numpy()
        loo_offset = float(-np.mean(train_raw_errors))

        pred = float(row["oescl_uniform_gsnr_mean_db"]) + loo_offset
        ref = float(row["gnpy_reference_gsnr_db"])
        err = pred - ref

        loo_rows.append({
            "spans": int(row["spans"]),
            "loo_offset_db": loo_offset,
            "loo_predicted_gsnr_db": pred,
            "gnpy_reference_gsnr_db": ref,
            "loo_error_db": err,
            "abs_loo_error_db": abs(err),
        })

    loo_df = pd.DataFrame(loo_rows)
    loo_rmse = float(np.sqrt(np.mean(loo_df["loo_error_db"].astype(float) ** 2)))
    loo_mae = float(np.mean(loo_df["abs_loo_error_db"].astype(float)))
    loo_max_abs = float(np.max(loo_df["abs_loo_error_db"].astype(float)))

    # Simple pass criteria for diagnostic alignment, not formal raw validation.
    diagnostic_pass = bool(
        calibrated_rmse <= 0.50
        and loo_rmse <= 0.75
        and raw_std <= 1.00
    )

    df.to_csv(out_csv, index=False)

    loo_csv = PROJECT_ROOT / "results/tables/day13_external_offset_calibration_loo.csv"
    loo_df.to_csv(loo_csv, index=False)

    report = []
    report.append("# Day-13 External Offset-Calibration Diagnostic")
    report.append("")
    report.append("Day-13 evaluates whether the Day-12 O-E-S-C-L vs GNPy mismatch can be explained by one constant conservative GSNR offset.")
    report.append("")
    report.append("This is not reported as raw absolute GNPy validation. It is a calibration diagnostic for the absolute GSNR scale.")
    report.append("")
    report.append("## Raw Day-12 alignment")
    report.append(f"- Raw RMSE: `{raw_rmse:.6f} dB`")
    report.append(f"- Raw mean error, O-E-S-C-L minus GNPy: `{raw_mean_error:.6f} dB`")
    report.append(f"- Raw offset standard deviation: `{raw_std:.6f} dB`")
    report.append("")
    report.append("## Constant offset")
    report.append(f"- Offset applied to O-E-S-C-L GSNR: `+{offset_db:.6f} dB`")
    report.append("")
    report.append("## Offset-calibrated alignment")
    report.append(f"- Calibrated RMSE: `{calibrated_rmse:.6f} dB`")
    report.append(f"- Calibrated MAE: `{calibrated_mae:.6f} dB`")
    report.append(f"- Calibrated max absolute error: `{calibrated_max_abs:.6f} dB`")
    report.append("")
    report.append("## Leave-one-out offset diagnostic")
    report.append(f"- LOO RMSE: `{loo_rmse:.6f} dB`")
    report.append(f"- LOO MAE: `{loo_mae:.6f} dB`")
    report.append(f"- LOO max absolute error: `{loo_max_abs:.6f} dB`")
    report.append("")
    report.append("## Calibrated sweep table")
    report.append(df.round(6).to_markdown(index=False))
    report.append("")
    report.append("## Leave-one-out table")
    report.append(loo_df.round(6).to_markdown(index=False))
    report.append("")
    report.append("## Decision")
    report.append(f"- Diagnostic offset calibration passed: `{diagnostic_pass}`")
    report.append("")
    report.append("## Correct interpretation")
    if diagnostic_pass:
        report.append(
            "The raw absolute GSNR scale of O-E-S-C-L is conservatively shifted relative to GNPy, but the mismatch is well explained by a nearly constant offset across span count. The manuscript may use this as an external calibration diagnostic while keeping the main validated claim focused on PCS gain trends and repeated-seed convergence."
        )
    else:
        report.append(
            "The constant-offset correction is not sufficient. Further physical tuning of noise, nonlinear, or implementation-penalty scaling is required before using GNPy as an external diagnostic."
        )

    report_path.write_text("\n".join(report), encoding="utf-8")

    latex = rf"""\subsection{{External GSNR alignment diagnostic}}
An independent GNPy sweep was performed for the C-band reference case across multiple span counts. The raw O-E-S-C-L GSNR values were conservatively lower than the GNPy center-channel GSNR values, with a mean offset of {raw_mean_error:.3f} dB and an offset standard deviation of {raw_std:.3f} dB. Applying a single constant offset of +{offset_db:.3f} dB reduced the calibrated RMSE to {calibrated_rmse:.3f} dB, with leave-one-out RMSE of {loo_rmse:.3f} dB. This result is interpreted as an external calibration diagnostic rather than raw absolute GNPy validation; the main claim remains the repeated-seed, larger-symbol stability of PCS gain trends.
"""
    latex_path.write_text(latex, encoding="utf-8")

    print("Day-13 external offset-calibration diagnostic completed.")
    print(f"Offset applied: +{offset_db:.6f} dB")
    print(f"Raw RMSE: {raw_rmse:.6f} dB")
    print(f"Calibrated RMSE: {calibrated_rmse:.6f} dB")
    print(f"LOO RMSE: {loo_rmse:.6f} dB")
    print(f"Diagnostic pass: {diagnostic_pass}")
    print(f"Report: {report_path}")
    print(f"CSV: {out_csv}")
    print(f"LOO CSV: {loo_csv}")
    print(f"LaTeX: {latex_path}")


if __name__ == "__main__":
    main()
