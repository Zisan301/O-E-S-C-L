"""Check confirmation experiment plan integrity."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "final_confirmation_plan.json"
TABLE_PATH = ROOT / "results" / "final" / "tables" / "confirmation_experiment_plan.csv"


def main() -> None:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config: {CONFIG_PATH}")
    if not TABLE_PATH.exists():
        raise FileNotFoundError(f"Missing table: {TABLE_PATH}")

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))

    with TABLE_PATH.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    scenarios = {row["scenario"] for row in rows}
    required_scenarios = {"C", "S", "C+S"}
    if scenarios != required_scenarios:
        raise AssertionError(f"Scenario mismatch: {scenarios}")

    stages = {row["stage"] for row in rows}
    required_stages = {"discovery", "validation", "final_confirmation"}
    if stages != required_stages:
        raise AssertionError(f"Stage mismatch: {stages}")

    final_rows = [row for row in rows if row["stage"] == "final_confirmation"]
    final_seeds = sorted({int(row["seed"]) for row in final_rows})

    if len(final_seeds) < int(config["minimum_confirmation_seeds"]):
        raise AssertionError("Not enough final confirmation seeds.")

    for row in final_rows:
        if int(row["symbols"]) < int(config["minimum_symbols"]):
            raise AssertionError("Final confirmation symbols below minimum.")
        if row["allowed_to_select_operating_point"].lower() != "false":
            raise AssertionError("Final confirmation must not allow operating-point selection.")

    expected_final_rows = len(required_scenarios) * len(final_seeds)
    if len(final_rows) != expected_final_rows:
        raise AssertionError(f"Final row count mismatch: {len(final_rows)} != {expected_final_rows}")

    print("PASS: confirmation experiment plan contains C, S, C+S with independent frozen final-confirmation seeds.")


if __name__ == "__main__":
    main()