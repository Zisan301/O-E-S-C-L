"""Analyze independent confirmation results for entropy-corrected PCS gains.

This script expects real per-seed results in:
results/final/tables/confirmation_raw_results.csv

It does not generate or fake simulation results.
"""

from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / "results" / "final" / "tables" / "confirmation_raw_results.csv"
SUMMARY_PATH = ROOT / "results" / "final" / "tables" / "confirmation_statistical_summary.csv"
REPORT_PATH = ROOT / "results" / "final" / "reports" / "confirmation_statistical_summary_report.md"


T_CRITICAL_95 = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    21: 2.080,
    22: 2.074,
    23: 2.069,
    24: 2.064,
    25: 2.060,
    26: 2.056,
    27: 2.052,
    28: 2.048,
    29: 2.045,
    30: 2.042,
}


def t_critical_95(df: int) -> float:
    if df <= 0:
        raise ValueError("Degrees of freedom must be positive.")
    if df in T_CRITICAL_95:
        return T_CRITICAL_95[df]
    return 1.960


def read_rows() -> list[dict[str, str]]:
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"Missing raw confirmation file: {RAW_PATH}\n"
            "Create this file from actual simulation outputs before running the analyzer."
        )

    with RAW_PATH.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError("confirmation_raw_results.csv exists but contains no data rows.")

    return rows


def classify(lower_ci: float, upper_ci: float) -> str:
    if lower_ci > 0:
        return "confirmed_positive"
    if lower_ci <= 0 <= upper_ci:
        return "borderline_inconclusive"
    return "not_positive"


def main() -> None:
    rows = read_rows()

    final_rows = [r for r in rows if r["stage"] == "final_confirmation"]
    if not final_rows:
        raise ValueError("No final_confirmation rows found in raw results.")

    scenarios = sorted({r["scenario"] for r in final_rows})

    summary_rows = []
    for scenario in scenarios:
        srows = [r for r in final_rows if r["scenario"] == scenario]
        gains = [float(r["delta_corrected_bmd_gain_bit_per_symbol"]) for r in srows]

        n = len(gains)
        if n < 2:
            raise ValueError(f"Need at least 2 final-confirmation rows for {scenario}.")

        mean_gain = statistics.mean(gains)
        std_gain = statistics.stdev(gains)
        se_gain = std_gain / math.sqrt(n)
        tcrit = t_critical_95(n - 1)
        ci_half = tcrit * se_gain
        lower = mean_gain - ci_half
        upper = mean_gain + ci_half
        status = classify(lower, upper)

        summary_rows.append({
            "scenario": scenario,
            "n": n,
            "mean_delta_corrected_bmd_gain_bit_per_symbol": f"{mean_gain:.6f}",
            "std_bit_per_symbol": f"{std_gain:.6f}",
            "se_bit_per_symbol": f"{se_gain:.6f}",
            "t_critical_95": f"{tcrit:.3f}",
            "ci95_half_width_bit_per_symbol": f"{ci_half:.6f}",
            "ci95_lower_bit_per_symbol": f"{lower:.6f}",
            "ci95_upper_bit_per_symbol": f"{upper:.6f}",
            "confirmation_status": status,
        })

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with SUMMARY_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    lines = []
    lines.append("# Confirmation Statistical Summary")
    lines.append("")
    lines.append("This report analyzes real final-confirmation rows only.")
    lines.append("")
    lines.append("Claim rule: confirmed positive only if the lower 95% confidence bound is greater than zero.")
    lines.append("")
    lines.append("| Scenario | n | Mean gain | 95% CI lower | 95% CI upper | Status |")
    lines.append("|---|---:|---:|---:|---:|---|")

    for row in summary_rows:
        lines.append(
            "| {} | {} | {} | {} | {} | {} |".format(
                row["scenario"],
                row["n"],
                row["mean_delta_corrected_bmd_gain_bit_per_symbol"],
                row["ci95_lower_bit_per_symbol"],
                row["ci95_upper_bit_per_symbol"],
                row["confirmation_status"],
            )
        )

    lines.append("")
    lines.append("No scenario should be called confirmed positive unless its status is confirmed_positive.")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {SUMMARY_PATH}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()