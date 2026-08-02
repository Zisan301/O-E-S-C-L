"""Check final-confirmation job list integrity."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
JOB_CSV = ROOT / "results" / "final" / "tables" / "confirmation_job_list.csv"


def main() -> None:
    if not JOB_CSV.exists():
        raise FileNotFoundError(f"Missing job list: {JOB_CSV}")

    with JOB_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if len(rows) != 90:
        raise AssertionError(f"Expected 90 final-confirmation jobs, found {len(rows)}")

    scenarios = {row["scenario"] for row in rows}
    if scenarios != {"C", "S", "C+S"}:
        raise AssertionError(f"Scenario mismatch: {scenarios}")

    for scenario in ["C", "S", "C+S"]:
        srows = [row for row in rows if row["scenario"] == scenario]
        if len(srows) != 30:
            raise AssertionError(f"{scenario} should have 30 jobs, found {len(srows)}")

        seeds = sorted({int(row["seed"]) for row in srows})
        if seeds != list(range(21, 51)):
            raise AssertionError(f"{scenario} seed range mismatch: {seeds}")

    job_ids = [row["job_id"] for row in rows]
    if len(job_ids) != len(set(job_ids)):
        raise AssertionError("Duplicate job_id found.")

    print("PASS: confirmation job list has 90 jobs, 30 per scenario, seeds 21-50.")


if __name__ == "__main__":
    main()