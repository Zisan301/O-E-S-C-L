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
        description="O-E-S-C-L IEEE/Optica simulation pipeline."
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
        choices=["smoke", "full", "day1", "day2", "day4", "day4cal", "day5", "day6"],
        help="Run smoke, full, Day-1, Day-2, Day-4, Day-4 calibration, Day-5, or Day-6 experiments.",
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
        bundle = run_day1_ieee_optica_upgrade(cfg=cfg)
        print("\nO-E-S-C-L Day-1 IEEE/Optica upgrade completed.")
        print(f"Report: {Path(bundle['report_path']).resolve()}")
        return

    if args.mode == "day2":
        from src.oescl.day2 import run_day2_ieee_optica_upgrade
        bundle = run_day2_ieee_optica_upgrade(cfg=cfg)
        print("\nO-E-S-C-L Day-2 IEEE/Optica upgrade completed.")
        print(f"Report: {Path(bundle['report_path']).resolve()}")
        return

    if args.mode == "day4":
        from src.oescl.day4 import run_day4_optica_scientific_upgrade
        bundle = run_day4_optica_scientific_upgrade(cfg=cfg)
        print("\nO-E-S-C-L Day-4 Optica scientific upgrade completed.")
        print(f"Report: {Path(bundle['report_path']).resolve()}")
        return

    if args.mode == "day4cal":
        from src.oescl.day4_calibration import run_day4_calibration_fix
        bundle = run_day4_calibration_fix(cfg=cfg)
        print("\nO-E-S-C-L Day-4 calibration/fix completed.")
        print(f"Calibration report: {Path(bundle['report_path']).resolve()}")
        print(f"Calibrated comparison report: {Path(bundle['comparison_report_path']).resolve()}")
        return

    if args.mode == "day5":
        from src.oescl.day5 import run_day5_optica_evidence
        bundle = run_day5_optica_evidence(cfg=cfg)
        print("\nO-E-S-C-L Day-5 Optica evidence run completed.")
        print(f"Report: {Path(bundle['report_path']).resolve()}")
        print(f"Acceptance gate: {Path(bundle['acceptance_report_path']).resolve()}")
        return

    if args.mode == "day6":
        from src.oescl.day6 import run_day6_pcs_confirmation
        bundle = run_day6_pcs_confirmation(cfg=cfg)
        print("\nO-E-S-C-L Day-6 PCS confirmation run completed.")
        print(f"Report: {Path(bundle['report_path']).resolve()}")
        print(f"Acceptance gate: {Path(bundle['acceptance_report_path']).resolve()}")
        print(f"LaTeX snippet: {Path(bundle['latex_snippet_path']).resolve()}")
        print("\nGenerated Day-6 figures:")
        for p in bundle["figure_paths"]:
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
