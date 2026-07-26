from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_day12_external_alignment import (  # noqa: E402
    parse_center_channel_gsnr,
    write_gnpy_case_files,
)
from src.oescl.config import load_config  # noqa: E402
from src.oescl.day8_q3_band_comparison import _run_one  # noqa: E402


BASE_CONFIG = PROJECT_ROOT / "config/day8_q3_band_comparison_config.yaml"
TABLES_DIR = PROJECT_ROOT / "results/tables"
REPORTS_DIR = PROJECT_ROOT / "results/reports"
VALIDATION_DIR = PROJECT_ROOT / "validation_data/day14"

SYMBOLS = 16384
SEEDS = [1, 2, 3]
SSFM_STEPS_PER_SPAN = 8
PCS_NU = 0.0

# Fixed offset learned from Day-13 C-band diagnostic.
# This is used only as a diagnostic calibration, not as raw validation.
DAY13_OFFSET_DB = 6.152843

CASES = [
    {
        "case_id": "day14_C_6sp_m1dBm_5ch_64G",
        "scenario_group": "C",
        "band": "C",
        "spans": 6,
        "launch_power_dbm": -1.0,
        "center_nm": 1550.0,
        "baud_rate_gbaud": 64.0,
        "channel_spacing_ghz": 100.0,
        "channels": 5,
    },
    {
        "case_id": "day14_C_12sp_3dBm_15ch_32G",
        "scenario_group": "C",
        "band": "C",
        "spans": 12,
        "launch_power_dbm": 3.0,
        "center_nm": 1550.0,
        "baud_rate_gbaud": 32.0,
        "channel_spacing_ghz": 50.0,
        "channels": 15,
    },
    {
        "case_id": "day14_S_8sp_1dBm_9ch_32G",
        "scenario_group": "S",
        "band": "S",
        "spans": 8,
        "launch_power_dbm": 1.0,
        "center_nm": 1500.0,
        "baud_rate_gbaud": 32.0,
        "channel_spacing_ghz": 75.0,
        "channels": 9,
    },
    {
        "case_id": "day14_S_12sp_3dBm_5ch_32G",
        "scenario_group": "S",
        "band": "S",
        "spans": 12,
        "launch_power_dbm": 3.0,
        "center_nm": 1500.0,
        "baud_rate_gbaud": 32.0,
        "channel_spacing_ghz": 100.0,
        "channels": 5,
    },
]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_gnpy_case(case: dict) -> tuple[float, Path]:
    case_dir = ensure_dir(VALIDATION_DIR / case["case_id"])

    eqpt, network, extra_eqpt, spectrum, target_freq_thz = write_gnpy_case_files(
        validation_dir=case_dir,
        spans=int(case["spans"]),
        span_length_km=80.0,
        attenuation_db_per_km=0.19,
        noise_figure_db=5.0,
        center_nm=float(case["center_nm"]),
        baud_rate_gbaud=float(case["baud_rate_gbaud"]),
        channel_spacing_ghz=float(case["channel_spacing_ghz"]),
        channels=int(case["channels"]),
        launch_power_dbm=float(case["launch_power_dbm"]),
    )

    stdout_path = case_dir / f"{case['case_id']}_gnpy_stdout.txt"

    cmd = [
        "gnpy-transmission-example",
        "-e",
        str(eqpt),
        "--extra-equipment",
        str(extra_eqpt),
        "--spectrum",
        str(spectrum),
        "--show-channels",
        "-po",
        str(float(case["launch_power_dbm"])),
        str(network),
        "Site_A",
        "Site_B",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            text=True,
            capture_output=True,
            shell=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Could not find gnpy-transmission-example. Activate the environment "
            "where GNPy is installed, then rerun this script."
        ) from exc

    combined = ""
    combined += "COMMAND:\n" + " ".join(cmd) + "\n\n"
    combined += "STDOUT:\n" + result.stdout + "\n\n"
    combined += "STDERR:\n" + result.stderr + "\n"
    stdout_path.write_text(combined, encoding="utf-8")

    if result.returncode != 0:
        raise RuntimeError(f"GNPy failed for {case['case_id']}. See {stdout_path}")

    gsnr = parse_center_channel_gsnr(combined, target_freq_thz)
    if gsnr is None:
        raise RuntimeError(f"Could not parse GNPy GSNR for {case['case_id']}.")

    return float(gsnr), stdout_path


def run_oescl_case(case: dict, base_cfg: dict) -> tuple[float, float, int]:
    local = copy.deepcopy(base_cfg)
    local["day8"]["symbols"] = int(SYMBOLS)
    local["day5"]["ssfm_steps_per_span"] = int(SSFM_STEPS_PER_SPAN)

    values: list[float] = []

    for seed in SEEDS:
        row = _run_one(
            int(seed),
            str(case["scenario_group"]),
            str(case["band"]),
            int(case["spans"]),
            float(case["launch_power_dbm"]),
            float(PCS_NU),
            local,
        )
        values.append(float(row["gsnr_db"]))

    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    return mean, std, len(values)


def write_report(df: pd.DataFrame) -> Path:
    ok = df[df["status"] == "ok"].copy()

    if ok.empty:
        raise RuntimeError("No successful Day-14 cases. Inspect GNPy stdout logs.")

    raw_errors = ok["raw_error_db"].astype(float).to_numpy()
    calibrated_errors = ok["calibrated_error_db"].astype(float).to_numpy()

    raw_rmse = float(np.sqrt(np.mean(raw_errors**2)))
    calibrated_rmse = float(np.sqrt(np.mean(calibrated_errors**2)))
    raw_mae = float(np.mean(np.abs(raw_errors)))
    calibrated_mae = float(np.mean(np.abs(calibrated_errors)))
    raw_max = float(np.max(np.abs(raw_errors)))
    calibrated_max = float(np.max(np.abs(calibrated_errors)))

    report_path = REPORTS_DIR / "day14_starter_independent_validation_report.md"

    lines = [
        "# Day-14 Starter Independent Validation",
        "",
        "This is a starter broader-validation run. It expands beyond the Day-12 C-band span-only sweep by varying band, span count, launch power, channel loading and baud rate.",
        "",
        "## Claim policy",
        "",
        "These results must be reported as diagnostic evidence only. Raw and calibrated errors must remain separate.",
        "",
        "## Case summary",
        "",
        "```text",
        df.round(6).to_string(index=False),
        "```",
        "",
        "## Aggregate metrics",
        "",
        f"- Raw RMSE: `{raw_rmse:.6f} dB`",
        f"- Raw MAE: `{raw_mae:.6f} dB`",
        f"- Raw max abs. error: `{raw_max:.6f} dB`",
        f"- Calibrated RMSE using fixed Day-13 offset: `{calibrated_rmse:.6f} dB`",
        f"- Calibrated MAE using fixed Day-13 offset: `{calibrated_mae:.6f} dB`",
        f"- Calibrated max abs. error using fixed Day-13 offset: `{calibrated_max:.6f} dB`",
        "",
        "## Interpretation",
        "",
        f"- Successful cases: `{len(ok)}` of `{len(df)}`.",
        f"- Failed cases: `{len(df) - len(ok)}` of `{len(df)}`.",
        "",
        "The fixed Day-13 offset does not transfer cleanly to this broader starter matrix. In the successful C-band cases, the calibrated RMSE is larger than the raw RMSE. Therefore, these Day-14 results should be reported as limitation evidence, not as broader external validation success.",
        "",
        "The S-band generated GNPy cases failed under the current automatic GNPy setup and are retained in the table instead of being hidden. This indicates that S-band external-reference generation needs a dedicated equipment/spectrum configuration before it can be used as validation evidence.",
        "",
        "## Manuscript implication",
        "",
        "Use Day-14 only to show that broader validation was attempted and that the Day-13 C-band offset is not universally transferable. Do not claim full C/S-band external validation from this starter run.",
        "",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    ensure_dir(TABLES_DIR)
    ensure_dir(REPORTS_DIR)
    ensure_dir(VALIDATION_DIR)

    if not BASE_CONFIG.exists():
        raise FileNotFoundError(f"Missing base config: {BASE_CONFIG}")

    base_cfg = load_config(str(BASE_CONFIG))

    rows = []

    for case in CASES:
        print(f"Running {case['case_id']}...")

        base_row = {
            "case_id": case["case_id"],
            "scenario_group": case["scenario_group"],
            "band": case["band"],
            "spans": case["spans"],
            "launch_power_dbm": case["launch_power_dbm"],
            "center_nm": case["center_nm"],
            "baud_rate_gbaud": case["baud_rate_gbaud"],
            "channel_spacing_ghz": case["channel_spacing_ghz"],
            "channels": case["channels"],
            "symbols": SYMBOLS,
            "seeds": ",".join(map(str, SEEDS)),
            "day13_fixed_offset_db": DAY13_OFFSET_DB,
        }

        try:
            gnpy_gsnr, gnpy_stdout = run_gnpy_case(case)
            oescl_mean, oescl_std, n_seeds = run_oescl_case(case, base_cfg)

            raw_error = oescl_mean - gnpy_gsnr
            calibrated_oescl = oescl_mean + DAY13_OFFSET_DB
            calibrated_error = calibrated_oescl - gnpy_gsnr

            rows.append(
                {
                    **base_row,
                    "status": "ok",
                    "failure_reason": "",
                    "gnpy_reference_gsnr_db": gnpy_gsnr,
                    "oescl_uniform_gsnr_mean_db": oescl_mean,
                    "oescl_uniform_gsnr_std_db": oescl_std,
                    "oescl_n_seeds": n_seeds,
                    "calibrated_oescl_gsnr_db": calibrated_oescl,
                    "raw_error_db": raw_error,
                    "calibrated_error_db": calibrated_error,
                    "abs_raw_error_db": abs(raw_error),
                    "abs_calibrated_error_db": abs(calibrated_error),
                    "gnpy_stdout": str(gnpy_stdout.relative_to(PROJECT_ROOT)),
                }
            )

        except Exception as exc:
            print(f"WARNING: {case['case_id']} failed: {exc}")
            rows.append(
                {
                    **base_row,
                    "status": "failed",
                    "failure_reason": str(exc),
                    "gnpy_reference_gsnr_db": float("nan"),
                    "oescl_uniform_gsnr_mean_db": float("nan"),
                    "oescl_uniform_gsnr_std_db": float("nan"),
                    "oescl_n_seeds": 0,
                    "calibrated_oescl_gsnr_db": float("nan"),
                    "raw_error_db": float("nan"),
                    "calibrated_error_db": float("nan"),
                    "abs_raw_error_db": float("nan"),
                    "abs_calibrated_error_db": float("nan"),
                    "gnpy_stdout": "",
                }
            )

    df = pd.DataFrame(rows)
    csv_path = TABLES_DIR / "day14_starter_independent_validation.csv"
    df.to_csv(csv_path, index=False)

    report_path = write_report(df)

    print("Day-14 starter independent validation completed.")
    print(f"CSV: {csv_path}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()