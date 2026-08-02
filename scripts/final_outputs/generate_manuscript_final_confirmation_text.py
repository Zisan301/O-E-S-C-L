"""Generate manuscript-ready text for final confirmation results."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLAIM_CSV = ROOT / "results" / "final" / "tables" / "final_confirmation_claim_boundary.csv"
OUT = ROOT / "results" / "final" / "reports" / "manuscript_final_confirmation_text.md"


def main() -> None:
    if not CLAIM_CSV.exists():
        raise FileNotFoundError(f"Missing claim boundary table: {CLAIM_CSV}")

    with CLAIM_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    by_scenario = {row["scenario"]: row for row in rows}

    lines = []
    lines.append("# Manuscript-Ready Final Confirmation Text")
    lines.append("")
    lines.append("## Replacement Results Paragraph")
    lines.append("")
    lines.append(
        "Under the frozen independent final-confirmation protocol, each scenario was evaluated "
        "using 30 independent seeds, 131,072 symbols per job, and the fixed shaping parameter "
        "nu = 0.36. A positive PCS effect was accepted only when the lower 95% confidence bound "
        "of the entropy-corrected BMD-rate gain was greater than zero. This stricter confirmation "
        "criterion did not support a confirmed positive gain in any evaluated scenario."
    )
    lines.append("")

    for scenario in ["C", "S", "C+S"]:
        row = by_scenario[scenario]
        lines.append(
            f"For {scenario}, the mean entropy-corrected BMD-rate gain was "
            f"{row['mean_gain_bit_per_symbol']} bit/symbol with a 95% confidence interval of "
            f"[{row['ci95_lower_bit_per_symbol']}, {row['ci95_upper_bit_per_symbol']}], "
            f"leading to the status `{row['status']}`."
        )

    lines.append("")
    lines.append(
        "Therefore, the final manuscript should not claim a confirmed PCS throughput improvement. "
        "Instead, the main contribution should be framed as a validation-aware reproducibility "
        "framework that detects when discovery-stage shaping gains do not survive stricter "
        "independent confirmation."
    )
    lines.append("")
    lines.append("## Replacement Claim Statement")
    lines.append("")
    lines.append(
        "The proposed validation-aware framework revealed that discovery-stage entropy-corrected "
        "PCS gains were not robust under a frozen 30-seed final-confirmation protocol. C-band was "
        "not positive, while S-band and C+S remained statistically inconclusive."
    )
    lines.append("")
    lines.append("## Sentences to Remove or Avoid")
    lines.append("")
    lines.append("- Avoid: confirmed PCS gain.")
    lines.append("- Avoid: robust throughput improvement.")
    lines.append("- Avoid: confirmed C/S/C+S shaping advantage.")
    lines.append("- Avoid: final validation proves PCS benefit.")
    lines.append("")
    lines.append("## Safer Contribution Wording")
    lines.append("")
    lines.append("- Entropy-corrected BMD-rate accounting.")
    lines.append("- Frozen independent confirmation protocol.")
    lines.append("- Reproducible claim-boundary reporting.")
    lines.append("- Demonstration that discovery-stage PCS gains may not survive stricter validation.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()