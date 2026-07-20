from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.oescl.config import load_config
from src.oescl.experiments import run_experiment
from src.oescl.reporting import write_summary_report
from src.oescl.validation import validate_results
from src.oescl.utils import set_global_seed, ensure_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="O-E-S-C-L conference/IEEE-Optica simulation pipeline."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/conference_config.yaml",
        help="Path to YAML configuration file.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="full",
        choices=["smoke", "full", "day1", "day2"],
        help="Run smoke, full, Day-1, or Day-2 IEEE/Optica upgrade experiments.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    set_global_seed(int(cfg["simulation"]["seed"]))

    output_dir = Path(cfg["output"]["root"])
    ensure_dir(output_dir)

    if args.mode == "day1":
        from src.oescl.day1 import run_day1_ieee_optica_upgrade

        day1_bundle = run_day1_ieee_optica_upgrade(cfg=cfg)
        print("\nO-E-S-C-L Day-1 IEEE/Optica upgrade completed.")
        print(f"Results root: {output_dir.resolve()}")
        print(f"Day-1 report: {Path(day1_bundle['report_path']).resolve()}")
        print(f"Day-1 LaTeX snippet: {Path(day1_bundle['latex_snippet_path']).resolve()}")
        return

    if args.mode == "day2":
        from src.oescl.day2 import run_day2_ieee_optica_upgrade

        day2_bundle = run_day2_ieee_optica_upgrade(cfg=cfg)
        print("\nO-E-S-C-L Day-2 IEEE/Optica upgrade completed.")
        print(f"Results root: {output_dir.resolve()}")
        print(f"Day-2 report: {Path(day2_bundle['report_path']).resolve()}")
        print(f"Day-2 LaTeX snippet: {Path(day2_bundle['latex_snippet_path']).resolve()}")
        print("\nGenerated Day-2 figures:")
        for p in day2_bundle["figure_paths"]:
            print(f"- {Path(p).resolve()}")
        return

    result_bundle = run_experiment(cfg=cfg, mode=args.mode)
    validation = validate_results(result_bundle=result_bundle, cfg=cfg)
    report_path = write_summary_report(
        result_bundle=result_bundle,
        validation=validation,
        cfg=cfg,
        mode=args.mode,
    )

    print("\nO-E-S-C-L conference pipeline completed.")
    print(f"Mode: {args.mode}")
    print(f"Results root: {output_dir.resolve()}")
    print(f"Summary report: {report_path.resolve()}")

    if not validation["passed"]:
        print("\nWARNING: Validation gates did not pass.")
        for item in validation["errors"]:
            print(f"- {item}")
        raise SystemExit(2)

    print("\nValidation: PASSED")


if __name__ == "__main__":
    main()
