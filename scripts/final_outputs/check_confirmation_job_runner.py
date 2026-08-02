"""Check confirmation runner dry-run behavior."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    log_path = ROOT / "results" / "final" / "logs" / "dry_run_check.log"

    cmd = [
        "python",
        "scripts/final_outputs/run_single_confirmation_job.py",
        "--scenario", "C",
        "--seed", "21",
        "--symbols", "131072",
        "--nu", "0.36",
        "--spans", "10",
        "--launch-power-dbm", "2.0",
        "--output", "results/final/raw_confirmation/dry_run_check.csv",
        "--log", "results/final/logs/dry_run_check.log",
        "--dry-run",
    ]

    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)

    if result.returncode != 0:
        raise AssertionError(
            "Dry-run command failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    if not log_path.exists():
        raise FileNotFoundError(f"Dry-run log was not created: {log_path}")

    text = log_path.read_text(encoding="utf-8")
    if "DRY RUN ONLY" not in text:
        raise AssertionError("Dry-run log does not contain expected marker.")

    print("PASS: confirmation job runner validates frozen jobs in dry-run mode.")


if __name__ == "__main__":
    main()