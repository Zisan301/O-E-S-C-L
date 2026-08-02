"""Generate repository-facing final claim-boundary documentation."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "results" / "final" / "tables" / "confirmation_statistical_summary.csv"
DOC = ROOT / "docs" / "reproducibility" / "FINAL_CONFIRMATION_CLAIM_BOUNDARY.md"
README = ROOT / "README.md"

START = "<!-- OESCL_FINAL_CONFIRMATION_START -->"
END = "<!-- OESCL_FINAL_CONFIRMATION_END -->"


def main() -> None:
    if not SUMMARY.exists():
        raise FileNotFoundError(f"Missing statistical summary: {SUMMARY}")

    with SUMMARY.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    lines = []
    lines.append("# Final Confirmation Claim Boundary")
    lines.append("")
    lines.append("This document freezes the final independent confirmation result for the O-E-S-C-L project.")
    lines.append("")
    lines.append("## Final protocol")
    lines.append("")
    lines.append("- Stage: final_confirmation")
    lines.append("- Seeds: 21-50")
    lines.append("- Total jobs: 90")
    lines.append("- Jobs per scenario: 30")
    lines.append("- Symbols per job: 131072")
    lines.append("- Frozen shaping parameter: nu = 0.36")
    lines.append("")
    lines.append("## Acceptance rule")
    lines.append("")
    lines.append("A scenario is called `confirmed_positive` only when the lower 95% confidence bound of the entropy-corrected BMD gain is greater than zero.")
    lines.append("")
    lines.append("## Final result")
    lines.append("")
    lines.append("| Scenario | n | Mean gain | 95% CI lower | 95% CI upper | Status |")
    lines.append("|---|---:|---:|---:|---:|---|")

    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['n']} | "
            f"{row['mean_delta_corrected_bmd_gain_bit_per_symbol']} | "
            f"{row['ci95_lower_bit_per_symbol']} | "
            f"{row['ci95_upper_bit_per_symbol']} | "
            f"{row['confirmation_status']} |"
        )

    lines.append("")
    lines.append("## Claim boundary")
    lines.append("")
    lines.append("No scenario is confirmed positive under the final independent confirmation rule.")
    lines.append("")
    lines.append("The manuscript must not claim confirmed PCS throughput improvement or robust positive PCS gain.")
    lines.append("")
    lines.append("The correct project framing is:")
    lines.append("")
    lines.append("> A validation-aware framework that shows discovery-stage entropy-corrected PCS gains did not survive stricter independent final confirmation.")
    lines.append("")
    lines.append("## Scenario interpretation")
    lines.append("")
    lines.append("- C: not positive under independent final confirmation.")
    lines.append("- S: borderline/inconclusive.")
    lines.append("- C+S: borderline/exploratory under the existing Day-8 two-band surrogate.")

    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text("\n".join(lines), encoding="utf-8")

    readme_block = []
    readme_block.append(START)
    readme_block.append("## Final confirmation claim boundary")
    readme_block.append("")
    readme_block.append("The final independent confirmation run used 90 jobs: 30 seeds per scenario for C, S, and C+S.")
    readme_block.append("")
    readme_block.append("Final status:")
    readme_block.append("")
    for row in rows:
        readme_block.append(
            f"- {row['scenario']}: {row['confirmation_status']} "
            f"(mean gain {row['mean_delta_corrected_bmd_gain_bit_per_symbol']}, "
            f"95% CI [{row['ci95_lower_bit_per_symbol']}, {row['ci95_upper_bit_per_symbol']}])"
        )
    readme_block.append("")
    readme_block.append("No scenario is confirmed positive under the final 95% confidence-bound rule. The project should be cited as a validation-aware framework for detecting non-robust discovery-stage PCS gains, not as a confirmed PCS-gain result.")
    readme_block.append("")
    readme_block.append("See: `docs/reproducibility/FINAL_CONFIRMATION_CLAIM_BOUNDARY.md`")
    readme_block.append(END)

    block_text = "\n".join(readme_block)

    if README.exists():
        text = README.read_text(encoding="utf-8", errors="replace")
    else:
        text = "# O-E-S-C-L\n"

    if START in text and END in text:
        before = text.split(START)[0].rstrip()
        after = text.split(END, 1)[1].lstrip()
        new_text = before + "\n\n" + block_text + "\n\n" + after
    else:
        new_text = text.rstrip() + "\n\n" + block_text + "\n"

    README.write_text(new_text, encoding="utf-8")

    print(f"Wrote {DOC}")
    print(f"Updated {README}")


if __name__ == "__main__":
    main()