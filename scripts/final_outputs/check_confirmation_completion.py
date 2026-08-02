"""Check final-confirmation completion after full 90-job run."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "results" / "final" / "raw_confirmation"
COMBINED = ROOT / "results" / "final" / "tables" / "confirmation_raw_results.csv"
SUMMARY = ROOT / "results" / "final" / "tables" / "confirmation_statistical_summary.csv"


def main() -> None:
    raw_files = sorted(RAW_DIR.glob("confirm_*.csv"))

    if len(raw_files) != 90:
        raise AssertionError(f"Expected 90 raw confirmation files, found {len(raw_files)}")

    if not COMBINED.exists():
        raise FileNotFoundError(f"Missing combined result table: {COMBINED}")

    with COMBINED.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if len(rows) != 90:
        raise AssertionError(f"Expected 90 combined rows, found {len(rows)}")

    counts = {}
    seeds_by_scenario = {}

    for row in rows:
        scenario = row["scenario"]
        counts[scenario] = counts.get(scenario, 0) + 1
        seeds_by_scenario.setdefault(scenario, set()).add(int(row["seed"]))

    expected_scenarios = {"C", "S", "C+S"}
    if set(counts) != expected_scenarios:
        raise AssertionError(f"Scenario mismatch: {set(counts)}")

    for scenario in sorted(expected_scenarios):
        if counts[scenario] != 30:
            raise AssertionError(f"{scenario} should have 30 rows, found {counts[scenario]}")

        seeds = sorted(seeds_by_scenario[scenario])
        if seeds != list(range(21, 51)):
            raise AssertionError(f"{scenario} seed mismatch: {seeds}")

    if not SUMMARY.exists():
        raise FileNotFoundError(f"Missing statistical summary table: {SUMMARY}")

    print("PASS: final confirmation is complete with 90 jobs, 30 per scenario, seeds 21-50.")


if __name__ == "__main__":
    main()