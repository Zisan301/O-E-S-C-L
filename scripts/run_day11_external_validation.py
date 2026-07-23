from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.oescl.config import load_config
from src.oescl.day11_external_validation import run_day11_external_validation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Day-11 external GSNR benchmark validation.")
    parser.add_argument(
        "--config",
        type=str,
        default="config/day11_external_validation_config.yaml",
        help="Path to Day-11 validation config.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    bundle = run_day11_external_validation(cfg)
    print("\nO-E-S-C-L Day-11 external validation completed.")
    print(f"Report: {Path(bundle['report_path']).resolve()}")
    print(f"External check: {Path(bundle['external_check_csv']).resolve()}")
    print(f"Validation errors: {Path(bundle['validation_errors_csv']).resolve()}")
    print(f"LaTeX snippet: {Path(bundle['latex_snippet_path']).resolve()}")
    if not bundle.get("external_reference_gate_passed", False):
        print("\nExternal reference gate did not pass yet.")
        print("Fill validation_data\\gnpy_day11_reference.csv with real GNPy/GN/EGN GSNR values and rerun.")


if __name__ == "__main__":
    main()
