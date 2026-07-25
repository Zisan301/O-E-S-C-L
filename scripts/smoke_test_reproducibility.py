from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "config/day12_external_alignment_config.yaml",
    "results/reports/day13_final_validation_status.md",
    "results/reports/day13_external_offset_calibration_report.md",
    "results/tables/day12_external_alignment_sweep.csv",
    "results/tables/day13_external_offset_calibration.csv",
    "results/tables/day13_external_offset_calibration_loo.csv",
    "validation_data/gnpy_day10_reference.csv",
]


def require_file(path: str) -> Path:
    p = PROJECT_ROOT / path
    if not p.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return p


def main() -> None:
    print("Running O-E-S-C-L reproducibility smoke test...")

    for f in REQUIRED_FILES:
        require_file(f)
        print(f"OK: {f}")

    day13 = pd.read_csv(PROJECT_ROOT / "results/tables/day13_external_offset_calibration.csv")
    loo = pd.read_csv(PROJECT_ROOT / "results/tables/day13_external_offset_calibration_loo.csv")

    if "calibrated_error_db" not in day13.columns:
        raise RuntimeError("Missing calibrated_error_db column in Day-13 calibration CSV.")

    if "loo_error_db" not in loo.columns:
        raise RuntimeError("Missing loo_error_db column in Day-13 LOO CSV.")

    calibrated_rmse = float((day13["calibrated_error_db"].astype(float).pow(2).mean()) ** 0.5)
    loo_rmse = float((loo["loo_error_db"].astype(float).pow(2).mean()) ** 0.5)

    if calibrated_rmse > 0.50:
        raise RuntimeError(f"Calibrated RMSE too high: {calibrated_rmse:.6f} dB")

    if loo_rmse > 0.75:
        raise RuntimeError(f"LOO RMSE too high: {loo_rmse:.6f} dB")

    print(f"Calibrated RMSE: {calibrated_rmse:.6f} dB")
    print(f"LOO RMSE: {loo_rmse:.6f} dB")
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
