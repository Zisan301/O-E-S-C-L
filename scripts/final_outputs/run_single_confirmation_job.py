"""Run one frozen final-confirmation job.

This script validates job arguments and writes one real confirmation CSV row
using the existing Day-8 waveform surrogate engine through a clean adapter.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.oescl.final_outputs.confirmation_engine import (
    REQUIRED_COLUMNS,
    format_confirmation_row,
    run_confirmation_job,
)


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


def write_log(args: argparse.Namespace, lines: list[str]) -> None:
    log_path = ROOT / args.log
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(lines), encoding="utf-8")


def write_csv_row(args: argparse.Namespace, row: dict[str, str]) -> None:
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerow(row)


def main() -> None:
    args = parse_args()
    validate_args(args)

    if args.dry_run:
        write_log(
            args,
            [
                "DRY RUN ONLY - no scientific result generated.",
                "",
                f"scenario={args.scenario}",
                f"seed={args.seed}",
                f"symbols={args.symbols}",
                f"nu={args.nu}",
                f"spans={args.spans}",
                f"launch_power_dbm={args.launch_power_dbm}",
                f"planned_output={args.output}",
            ],
        )
        print(f"PASS dry-run validation for {args.scenario} seed {args.seed}")
        return

    row = run_confirmation_job(
        scenario=args.scenario,
        seed=args.seed,
        symbols=args.symbols,
        nu=args.nu,
        spans=args.spans,
        launch_power_dbm=args.launch_power_dbm,
    )

    formatted = format_confirmation_row(row)
    write_csv_row(args, formatted)

    write_log(
        args,
        [
            "REAL CONFIRMATION JOB COMPLETED",
            "",
            f"scenario={args.scenario}",
            f"seed={args.seed}",
            f"symbols={args.symbols}",
            f"nu={args.nu}",
            f"spans={args.spans}",
            f"launch_power_dbm={args.launch_power_dbm}",
            f"output={args.output}",
            "",
            f"delta_corrected_bmd_gain_bit_per_symbol={formatted['delta_corrected_bmd_gain_bit_per_symbol']}",
            f"ber_uniform={formatted['ber_uniform']}",
            f"ber_pcs={formatted['ber_pcs']}",
            f"gsnr_uniform_db={formatted['gsnr_uniform_db']}",
            f"gsnr_pcs_db={formatted['gsnr_pcs_db']}",
        ],
    )

    print(f"PASS real confirmation job: {args.scenario} seed {args.seed}")
    print(f"Wrote {ROOT / args.output}")


if __name__ == "__main__":
    main()