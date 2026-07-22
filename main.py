from __future__ import annotations
import argparse, sys
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
    parser = argparse.ArgumentParser(description='O-E-S-C-L simulation pipeline.')
    parser.add_argument('--config', type=str, default='config/conference_config.yaml')
    parser.add_argument('--mode', type=str, default='full', choices=['smoke','full','day1','day2','day4','day4cal','day5','day6','day8'])
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    set_global_seed(int(cfg['simulation']['seed']))
    output_dir = Path(cfg['output']['root'])
    ensure_dir(output_dir)
    if args.mode == 'day1':
        from src.oescl.day1 import run_day1_ieee_optica_upgrade
        b = run_day1_ieee_optica_upgrade(cfg=cfg); print(f"\nDay-1 completed. Report: {Path(b['report_path']).resolve()}"); return
    if args.mode == 'day2':
        from src.oescl.day2 import run_day2_ieee_optica_upgrade
        b = run_day2_ieee_optica_upgrade(cfg=cfg); print(f"\nDay-2 completed. Report: {Path(b['report_path']).resolve()}"); return
    if args.mode == 'day4':
        from src.oescl.day4 import run_day4_optica_scientific_upgrade
        b = run_day4_optica_scientific_upgrade(cfg=cfg); print(f"\nDay-4 completed. Report: {Path(b['report_path']).resolve()}"); return
    if args.mode == 'day4cal':
        from src.oescl.day4_calibration import run_day4_calibration_fix
        b = run_day4_calibration_fix(cfg=cfg); print(f"\nDay-4 calibration completed. Report: {Path(b['report_path']).resolve()}"); return
    if args.mode == 'day5':
        from src.oescl.day5 import run_day5_optica_evidence
        b = run_day5_optica_evidence(cfg=cfg); print(f"\nDay-5 completed. Report: {Path(b['report_path']).resolve()}"); return
    if args.mode == 'day6':
        from src.oescl.day6 import run_day6_pcs_confirmation
        b = run_day6_pcs_confirmation(cfg=cfg); print(f"\nDay-6 completed. Report: {Path(b['report_path']).resolve()}"); return
    if args.mode == 'day8':
        from src.oescl.day8_q3_band_comparison import run_day8_q3_band_comparison
        b = run_day8_q3_band_comparison(cfg=cfg)
        print('\nO-E-S-C-L Day-8 Q3 C/S/C+S band comparison completed.')
        print(f"Report: {Path(b['report_path']).resolve()}")
        print(f"Acceptance report: {Path(b['acceptance_report_path']).resolve()}")
        print(f"LaTeX snippet: {Path(b['latex_snippet_path']).resolve()}")
        return
    rb = run_experiment(cfg=cfg, mode=args.mode)
    val = validate_results(result_bundle=rb, cfg=cfg)
    rp = write_summary_report(result_bundle=rb, validation=val, cfg=cfg, mode=args.mode)
    print(f"\nPipeline completed. Report: {rp.resolve()}")
    if not val['passed']:
        for e in val['errors']: print('-', e)
        raise SystemExit(2)
    print('\nValidation: PASSED')
if __name__ == '__main__': main()
