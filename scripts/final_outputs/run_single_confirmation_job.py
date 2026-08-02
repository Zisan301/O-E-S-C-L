"""Run one frozen final-confirmation job.

This is a strict runner skeleton. It validates job arguments and supports
--dry-run only until the real O-E-S-C-L simulation engine is connected.

It must not generate fake scientific results.
"""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True, choices=["C", "S", "C+S"])
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--symbols", required=True, type=int)
    parser.add_argument("--nu", required=True, type=float)
    parser.add_argument("--spans", required=True, type=int)
    parser.add_argument("--launch-power-dbm", required=True, type=float)
    parser.add_argument("--output", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.seed < 21 or args.seed > 50:
        raise ValueError("Final-confirmation seed must be between 21 and 50.")
    if args.symbols < 131072:
        raise ValueError("Final-confirmation symbols must be at least 131072.")
    if abs(args.nu - 0.36) > 1e-12:
        raise ValueError("Frozen confirmation nu must be 0.36.")

    expected = {
        "C": {"spans": 10, "power": 2.0},
        "S": {"spans": 12, "power": -2.0},
        "C+S": {"spans": 12, "power": 0.0},
    }

    exp = expected[args.scenario]
    if args.spans != exp["spans"]:
        raise ValueError(f"{args.scenario} spans must be {exp['spans']}.")
    if abs(args.launch_power_dbm - exp["power"]) > 1e-12:
        raise ValueError(f"{args.scenario} launch power must be {exp['power']} dBm.")


def write_dry_run_log(args: argparse.Namespace) -> None:
    log_path = ROOT / args.log
    log_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "DRY RUN ONLY - no scientific result generated.",
        "",
        f"scenario={args.scenario}",
        f"seed={args.seed}",
        f"symbols={args.symbols}",
        f"nu={args.nu}",
        f"spans={args.spans}",
        f"launch_power_dbm={args.launch_power_dbm}",
        f"planned_output={args.output}",
        "",
        "Next step: connect this runner to the real O-E-S-C-L simulation engine.",
    ]

    log_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    validate_args(args)

    if args.dry_run:
        write_dry_run_log(args)
        print(f"PASS dry-run validation for {args.scenario} seed {args.seed}")
        return

    raise NotImplementedError(
        "Real simulation engine is not connected yet. "
        "Run with --dry-run for validation only, or implement engine integration."
    )


if __name__ == "__main__":
    main()