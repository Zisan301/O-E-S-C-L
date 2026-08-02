"""Generate final-confirmation job list from confirmation experiment plan.

This does not run simulations. It creates a reproducible job table and
PowerShell command list for the 90 frozen final-confirmation jobs.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = ROOT / "results" / "final" / "tables" / "confirmation_experiment_plan.csv"
JOB_CSV = ROOT / "results" / "final" / "tables" / "confirmation_job_list.csv"
JOB_PS1 = ROOT / "results" / "final" / "reports" / "confirmation_job_commands.ps1"
JOB_REPORT = ROOT / "results" / "final" / "reports" / "confirmation_job_list_report.md"


def scenario_slug(scenario: str) -> str:
    return scenario.replace("+", "plus").replace(" ", "").lower()


def main() -> None:
    if not PLAN_PATH.exists():
        raise FileNotFoundError(f"Missing confirmation plan table: {PLAN_PATH}")

    with PLAN_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    final_rows = [r for r in rows if r["stage"] == "final_confirmation"]
    if not final_rows:
        raise ValueError("No final_confirmation rows found in confirmation plan.")

    JOB_CSV.parent.mkdir(parents=True, exist_ok=True)
    JOB_PS1.parent.mkdir(parents=True, exist_ok=True)
    JOB_REPORT.parent.mkdir(parents=True, exist_ok=True)

    job_rows = []
    command_lines = []
    command_lines.append('$ErrorActionPreference = "Stop"')
    command_lines.append('Set-Location "E:\\VS Code\\O+E+S+C+L"')
    command_lines.append('')
    command_lines.append('Write-Host "Confirmation job command list only. Actual simulation runner is not connected yet." -ForegroundColor Yellow')
    command_lines.append('Write-Host "Use this file as the official list of frozen final-confirmation jobs." -ForegroundColor Yellow')
    command_lines.append('')

    for idx, row in enumerate(final_rows, start=1):
        scenario = row["scenario"]
        slug = scenario_slug(scenario)
        seed = int(row["seed"])
        symbols = int(row["symbols"])
        nu = float(row["nu"])
        spans = int(row["spans"])
        power = float(row["launch_power_dbm"])

        job_id = f"confirm_{idx:03d}_{slug}_seed{seed}"
        output_csv = f"results/final/raw_confirmation/{job_id}.csv"
        log_path = f"results/final/logs/{job_id}.log"

        command = (
            "python scripts/final_outputs/run_single_confirmation_job.py "
            f"--scenario \"{scenario}\" "
            f"--seed {seed} "
            f"--symbols {symbols} "
            f"--nu {nu} "
            f"--spans {spans} "
            f"--launch-power-dbm {power} "
            f"--output {output_csv} "
            f"--log {log_path}"
        )

        job_rows.append({
            "job_id": job_id,
            "scenario": scenario,
            "seed": seed,
            "symbols": symbols,
            "nu": nu,
            "spans": spans,
            "launch_power_dbm": power,
            "output_csv": output_csv,
            "log_path": log_path,
            "command": command,
            "status": "planned_not_run",
        })

        command_lines.append(f'Write-Host "Planned job {idx}/90: {job_id}" -ForegroundColor Cyan')
        command_lines.append(f'# {command}')
        command_lines.append('')

    with JOB_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(job_rows[0].keys()))
        writer.writeheader()
        writer.writerows(job_rows)

    JOB_PS1.write_text("\n".join(command_lines), encoding="utf-8")

    scenario_counts = {}
    for row in job_rows:
        scenario_counts[row["scenario"]] = scenario_counts.get(row["scenario"], 0) + 1

    lines = []
    lines.append("# Final Confirmation Job List")
    lines.append("")
    lines.append("This file defines the frozen final-confirmation simulation jobs.")
    lines.append("")
    lines.append("Important: these jobs are planned only. They are not fake results.")
    lines.append("")
    lines.append("## Job counts")
    lines.append("")
    lines.append("| Scenario | Jobs |")
    lines.append("|---|---:|")
    for scenario in sorted(scenario_counts):
        lines.append(f"| {scenario} | {scenario_counts[scenario]} |")
    lines.append("")
    lines.append(f"Total jobs: {len(job_rows)}")
    lines.append("")
    lines.append("## Output files")
    lines.append("")
    lines.append("- Job CSV: results/final/tables/confirmation_job_list.csv")
    lines.append("- PowerShell command list: results/final/reports/confirmation_job_commands.ps1")
    lines.append("")
    lines.append("## Next implementation step")
    lines.append("")
    lines.append("Connect run_single_confirmation_job.py to the real simulation engine, then run the 90 jobs and combine outputs into confirmation_raw_results.csv.")

    JOB_REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {JOB_CSV}")
    print(f"Wrote {JOB_PS1}")
    print(f"Wrote {JOB_REPORT}")
    print(f"Total final-confirmation jobs: {len(job_rows)}")


if __name__ == "__main__":
    main()