"""Combine per-job final-confirmation CSV outputs.

This script expects real outputs in results/final/raw_confirmation/.
It refuses to produce a combined result if no real job files exist.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "results" / "final" / "raw_confirmation"
OUT_PATH = ROOT / "results" / "final" / "tables" / "confirmation_raw_results.csv"

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
    files = sorted(RAW_DIR.glob("confirm_*.csv"))

    if not files:
        raise FileNotFoundError(
            "No real per-job confirmation CSV files found in "
            f"{RAW_DIR}. Run real confirmation simulations first."
        )

    all_rows: list[dict[str, str]] = []

    for path in files:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != REQUIRED_COLUMNS:
                raise AssertionError(
                    f"Schema mismatch in {path}\n"
                    f"Expected: {REQUIRED_COLUMNS}\n"
                    f"Found: {reader.fieldnames}"
                )
            all_rows.extend(list(reader))

    if not all_rows:
        raise ValueError("Per-job files exist but contain no data rows.")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {OUT_PATH}")
    print(f"Combined rows: {len(all_rows)}")


if __name__ == "__main__":
    main()