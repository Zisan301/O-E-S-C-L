"""Check confirmation raw-result template schema."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "results" / "final" / "tables" / "confirmation_raw_results_template.csv"

REQUIRED_COLUMNS = [
    "scenario",
    "stage",
    "seed",
    "symbols",
    "nu",
    "spans",
    "launch_power_dbm",
    "uniform_bmd_rate_bit_per_symbol",
    "pcs_stored_score_bit_per_symbol",
    "entropy_correction_bit_per_symbol",
    "pcs_corrected_bmd_rate_bit_per_symbol",
    "delta_corrected_bmd_gain_bit_per_symbol",
    "ber_uniform",
    "ber_pcs",
    "gsnr_uniform_db",
    "gsnr_pcs_db",
    "notes",
]


def main() -> None:
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Missing template: {TEMPLATE}")

    with TEMPLATE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)

    if header != REQUIRED_COLUMNS:
        raise AssertionError(
            "Template columns mismatch.\n"
            f"Expected: {REQUIRED_COLUMNS}\n"
            f"Found: {header}"
        )

    print("PASS: confirmation raw-result template schema is valid.")


if __name__ == "__main__":
    main()