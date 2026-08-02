"""Generate independent confirmation experiment plan for C/S/C+S PCS results."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "final_confirmation_plan.json"
TABLE_PATH = ROOT / "results" / "final" / "tables" / "confirmation_experiment_plan.csv"
REPORT_PATH = ROOT / "results" / "final" / "reports" / "confirmation_experiment_plan_report.md"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))


def seed_list(seed_start: int, seed_end: int) -> list[int]:
    return list(range(seed_start, seed_end + 1))


def main() -> None:
    config = load_config()
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for stage in config["stages"]:
        seeds = seed_list(stage["seed_start"], stage["seed_end"])
        for op in config["frozen_operating_points"]:
            for seed in seeds:
                rows.append({
                    "plan_name": config["plan_name"],
                    "stage": stage["stage"],
                    "scenario": op["scenario"],
                    "seed": seed,
                    "symbols": stage["symbols"],
                    "nu": op["nu"],
                    "spans": op["spans"],
                    "launch_power_dbm": op["launch_power_dbm"],
                    "allowed_to_select_operating_point": stage["allowed_to_select_operating_point"],
                    "current_status": op["current_status"],
                    "priority": op["priority"],
                })

    with TABLE_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    final_rows = [r for r in rows if r["stage"] == "final_confirmation"]
    discovery_rows = [r for r in rows if r["stage"] == "discovery"]
    validation_rows = [r for r in rows if r["stage"] == "validation"]

    lines = []
    lines.append("# Independent Confirmation Experiment Plan")
    lines.append("")
    lines.append("Purpose: independently confirm entropy-corrected PCS gains for C, S, and C+S using frozen operating points.")
    lines.append("")
    lines.append("## Claim rule")
    lines.append("")
    lines.append(config["claim_rule"])
    lines.append("")
    lines.append("## Experiment stages")
    lines.append("")
    lines.append("| Stage | Seeds | Symbols | Selection allowed | Purpose |")
    lines.append("|---|---:|---:|---:|---|")
    for stage in config["stages"]:
        n_seeds = stage["seed_end"] - stage["seed_start"] + 1
        lines.append("| {} | {} | {} | {} | {} |".format(
            stage["stage"],
            n_seeds,
            stage["symbols"],
            stage["allowed_to_select_operating_point"],
            stage["purpose"],
        ))

    lines.append("")
    lines.append("## Frozen operating points")
    lines.append("")
    lines.append("| Scenario | nu | Spans | Launch power dBm | Current status | Priority |")
    lines.append("|---|---:|---:|---:|---|---|")
    for op in config["frozen_operating_points"]:
        lines.append("| {} | {} | {} | {} | {} | {} |".format(
            op["scenario"],
            op["nu"],
            op["spans"],
            op["launch_power_dbm"],
            op["current_status"],
            op["priority"],
        ))

    lines.append("")
    lines.append("## Planned run counts")
    lines.append("")
    lines.append("- Discovery rows: {}".format(len(discovery_rows)))
    lines.append("- Validation rows: {}".format(len(validation_rows)))
    lines.append("- Final confirmation rows: {}".format(len(final_rows)))
    lines.append("- Total planned rows: {}".format(len(rows)))
    lines.append("")
    lines.append("## Final confirmation requirement")
    lines.append("")
    lines.append("For a scenario to be called confirmed positive, the final confirmation set must satisfy: lower 95 percent confidence bound greater than zero.")
    lines.append("")
    lines.append("Current evidence boundary: S strongest, C borderline, and C+S exploratory until this confirmation plan is executed.")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {TABLE_PATH}")
    print(f"Wrote {REPORT_PATH}")
    print(f"Total planned rows: {len(rows)}")


if __name__ == "__main__":
    main()