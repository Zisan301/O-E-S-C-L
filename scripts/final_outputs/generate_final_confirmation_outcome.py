"""Generate final confirmation outcome and manuscript claim boundary report."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUMMARY_CSV = ROOT / "results" / "final" / "tables" / "confirmation_statistical_summary.csv"
RAW_CSV = ROOT / "results" / "final" / "tables" / "confirmation_raw_results.csv"

OUT_CSV = ROOT / "results" / "final" / "tables" / "final_confirmation_claim_boundary.csv"
OUT_REPORT = ROOT / "results" / "final" / "reports" / "final_confirmation_outcome_report.md"


def manuscript_action(scenario: str, status: str) -> str:
    if status == "confirmed_positive":
        return "May report as confirmed positive under final-confirmation rule."
    if scenario == "C" and status == "not_positive":
        return "Report as not positive under independent final confirmation; remove confirmed gain claim."
    if scenario == "S":
        return "Report as borderline/inconclusive; do not claim confirmed positive gain."
    if scenario == "C+S":
        return "Report as borderline/exploratory; do not claim confirmed positive gain."
    return "Do not claim confirmed positive gain."


def main() -> None:
    if not SUMMARY_CSV.exists():
        raise FileNotFoundError(f"Missing summary CSV: {SUMMARY_CSV}")
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"Missing raw combined CSV: {RAW_CSV}")

    with SUMMARY_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        summary_rows = list(csv.DictReader(f))

    with RAW_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        raw_rows = list(csv.DictReader(f))

    if len(raw_rows) != 90:
        raise AssertionError(f"Expected 90 raw confirmation rows, found {len(raw_rows)}")

    claim_rows = []

    for row in summary_rows:
        scenario = row["scenario"]
        n = row["n"]
        mean_gain = row["mean_delta_corrected_bmd_gain_bit_per_symbol"]
        ci_lower = row["ci95_lower_bit_per_symbol"]
        ci_upper = row["ci95_upper_bit_per_symbol"]
        status = row["confirmation_status"]

        allowed = "yes_confirmed_positive_gain" if status == "confirmed_positive" else "no_confirmed_positive_gain"

        claim_rows.append({
            "scenario": scenario,
            "n": n,
            "mean_gain_bit_per_symbol": mean_gain,
            "ci95_lower_bit_per_symbol": ci_lower,
            "ci95_upper_bit_per_symbol": ci_upper,
            "status": status,
            "claim_allowed": allowed,
            "manuscript_action": manuscript_action(scenario, status),
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(claim_rows[0].keys()))
        writer.writeheader()
        writer.writerows(claim_rows)

    lines = []
    lines.append("# Final Confirmation Outcome Report")
    lines.append("")
    lines.append("This report freezes the final independent confirmation result for the O-E-S-C-L project.")
    lines.append("")
    lines.append("## Protocol")
    lines.append("")
    lines.append("- Stage: final_confirmation")
    lines.append("- Seeds: 21-50")
    lines.append("- Rows: 90 total")
    lines.append("- Scenarios: C, S, C+S")
    lines.append("- Rows per scenario: 30")
    lines.append("- Symbols per job: 131072")
    lines.append("- Frozen shaping parameter: nu = 0.36")
    lines.append("")
    lines.append("## Claim rule")
    lines.append("")
    lines.append("A scenario is called confirmed positive only if the lower 95% confidence bound is greater than zero.")
    lines.append("")
    lines.append("## Final claim boundary")
    lines.append("")
    lines.append("| Scenario | n | Mean gain | 95% CI lower | 95% CI upper | Status | Manuscript action |")
    lines.append("|---|---:|---:|---:|---:|---|---|")

    for row in claim_rows:
        lines.append(
            f"| {row['scenario']} | {row['n']} | {row['mean_gain_bit_per_symbol']} | "
            f"{row['ci95_lower_bit_per_symbol']} | {row['ci95_upper_bit_per_symbol']} | "
            f"{row['status']} | {row['manuscript_action']} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("No scenario should be described as having a confirmed positive entropy-corrected BMD gain under the final independent confirmation protocol.")
    lines.append("")
    lines.append("The correct manuscript interpretation is:")
    lines.append("")
    lines.append("- Earlier discovery-stage gains were not confirmed by the stricter 30-seed final-confirmation run.")
    lines.append("- C-band becomes not positive under final confirmation.")
    lines.append("- S-band remains borderline/inconclusive.")
    lines.append("- C+S remains borderline/exploratory under the existing Day-8 two-band surrogate.")
    lines.append("- The project contribution should be framed as a validation-aware framework that exposes non-robust discovery claims, not as a confirmed PCS gain result.")
    lines.append("")
    lines.append("## Manuscript warning")
    lines.append("")
    lines.append("Do not claim confirmed throughput improvement, confirmed PCS advantage, or robust C/S/C+S positive gain from the final-confirmation experiment.")

    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()