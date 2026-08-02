"""Check final entropy-corrected C/S/C+S output values."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "results" / "final" / "tables" / "entropy_corrected_band_results.csv"

EXPECTED = {
    "C": {"corrected": 0.022967, "rate": 2.450},
    "S": {"corrected": 0.039293, "rate": 4.191},
    "C+S": {"corrected": 0.043628, "rate": 4.654, "aggregate": 9.307},
}


def approx_equal(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) <= tol


def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing final output CSV: {CSV_PATH}")

    with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    seen = {row["scenario"]: row for row in rows}

    for scenario, expected in EXPECTED.items():
        if scenario not in seen:
            raise AssertionError(f"Missing scenario: {scenario}")

        row = seen[scenario]
        corrected = float(row["corrected_bmd_gain_bit_per_symbol"])
        rate = float(row["rate_gain_gbps_per_representative_channel"])

        if not approx_equal(corrected, expected["corrected"]):
            raise AssertionError(f"{scenario} corrected BMD mismatch: {corrected} != {expected["corrected"]}")

        if not approx_equal(rate, expected["rate"]):
            raise AssertionError(f"{scenario} rate mismatch: {rate} != {expected["rate"]}")

        if "aggregate" in expected:
            aggregate = float(row["aggregate_rate_gain_gbps"])
            if not approx_equal(aggregate, expected["aggregate"]):
                raise AssertionError(f"{scenario} aggregate mismatch: {aggregate} != {expected["aggregate"]}")

    print("PASS: entropy-corrected final C/S/C+S outputs match expected publication-facing values.")


if __name__ == "__main__":
    main()
