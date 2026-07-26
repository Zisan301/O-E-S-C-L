from __future__ import annotations

import copy
import json
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
VALIDATION_DIR = PROJECT_ROOT / "validation_data/day15_sband"

# Keep this starter run deliberately small. After one S-band GNPy case passes,
# expand channel count, span count and launch-power diversity.
SYMBOLS = 16384
SEEDS = [1, 2, 3]
SSFM_STEPS_PER_SPAN = 8
PCS_NU = 0.0
SPAN_LENGTH_KM = 80.0

# S-band parameters already present in config/day8_q3_band_comparison_config.yaml.
S_ATTENUATION_DB_PER_KM = 0.22
S_NOISE_FIGURE_DB = 5.5

# Approximate S-band equipment window for this starter diagnostic.
# These bounds cover the small 1490--1520 nm smoke grid and keep the entire
# channel slots inside the amplifier bandwidth. This is still a diagnostic
# configuration, not a vendor-specific amplifier model.
S_EDFA_F_MIN_HZ = 196.0e12
S_EDFA_F_MAX_HZ = 202.0e12

CASES = [
    {
        "case_id": "day15_S_smoke_1520nm_6sp_0dBm_3ch_32G",
        "scenario_group": "S",
        "band": "S",
        "spans": 6,
        "launch_power_dbm": 0.0,
        "center_nm": 1520.0,
        "baud_rate_gbaud": 32.0,
        "channel_spacing_ghz": 100.0,
        "channels": 3,
    },
    {
        "case_id": "day15_S_smoke_1510nm_6sp_0dBm_3ch_32G",
        "scenario_group": "S",
        "band": "S",
        "spans": 6,
        "launch_power_dbm": 0.0,
        "center_nm": 1510.0,
        "baud_rate_gbaud": 32.0,
        "channel_spacing_ghz": 100.0,
        "channels": 3,
    },
    {
        "case_id": "day15_S_smoke_1500nm_6sp_0dBm_3ch_32G",
        "scenario_group": "S",
        "band": "S",
        "spans": 6,
        "launch_power_dbm": 0.0,
        "center_nm": 1500.0,
        "baud_rate_gbaud": 32.0,
        "channel_spacing_ghz": 100.0,
        "channels": 3,
    },
    {
        "case_id": "day15_S_smoke_1490nm_6sp_0dBm_3ch_32G",
        "scenario_group": "S",
        "band": "S",
        "spans": 6,
        "launch_power_dbm": 0.0,
        "center_nm": 1490.0,
        "baud_rate_gbaud": 32.0,
        "channel_spacing_ghz": 100.0,
        "channels": 3,
    },
]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def patch_extra_equipment_for_sband(extra_eqpt_path: Path) -> None:
    """Add an explicit S-band frequency window to the generated EDFA variety."""
    data = json.loads(extra_eqpt_path.read_text(encoding="utf-8"))

    for edfa in data.get("Edfa", []):
        edfa["f_min"] = S_EDFA_F_MIN_HZ
        edfa["f_max"] = S_EDFA_F_MAX_HZ

    extra_eqpt_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def run_gnpy_case(case: dict) -> tuple[str, str, float | None, Path | None]:
    case_dir = ensure_dir(VALIDATION_DIR / str(case["case_id"]))

    eqpt, network, extra_eqpt, spectrum, target_freq_thz = write_gnpy_case_files(
        validation_dir=case_dir,
        spans=int(case["spans"]),
        span_length_km=SPAN_LENGTH_KM,
        attenuation_db_per_km=S_ATTENUATION_DB_PER_KM,
        noise_figure_db=S_NOISE_FIGURE_DB,
        center_nm=float(case["center_nm"]),
        baud_rate_gbaud=float(case["baud_rate_gbaud"]),
        channel_spacing_ghz=float(case["channel_spacing_ghz"]),
        channels=int(case["channels"]),
        launch_power_dbm=float(case["launch_power_dbm"]),
    )

    patch_extra_equipment_for_sband(extra_eqpt)

    stdout_path = case_dir / f"{case['case_id']}_gnpy_stdout.txt"

    cmd = [
        "gnpy-transmission-example",
        "-vv",
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
    combined += f"RETURN_CODE:\n{result.returncode}\n\n"
    combined += "STDOUT:\n" + result.stdout + "\n\n"
    combined += "STDERR:\n" + result.stderr + "\n"
    stdout_path.write_text(combined, encoding="utf-8")

    if result.returncode != 0:
        return "failed", f"GNPy failed. See {stdout_path}", None, stdout_path

    gsnr = parse_center_channel_gsnr(combined, target_freq_thz)
    if gsnr is None:
        return "failed", f"Could not parse GNPy GSNR. See {stdout_path}", None, stdout_path

    return "ok", "", float(gsnr), stdout_path


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
    report_path = REPORTS_DIR / "sband_starter_gnpy_validation_report.md"

    lines = [
        "# Day-15 S-band Starter GNPy Validation",
        "",
        "This run tests whether a dedicated S-band GNPy setup can produce external-reference GSNR rows.",
        "The cases intentionally begin with a small 3-channel, 32-GBd, 100-GHz grid before larger S-band validation is attempted.",
        "",
        "## Claim policy",
        "",
        "These rows are S-band diagnostic evidence only. They must not be reported as full S-band validation until multiple operating points pass and calibration is documented.",
        "",
        "## Case summary",
        "",
        "```text",
        df.round(6).to_string(index=False),
        "```",
        "",
    ]

    if ok.empty:
        lines += [
            "## Interpretation",
            "",
            "No S-band GNPy smoke case completed. Inspect the per-case stdout files under validation_data/day15_sband.",
            "This means the next fix should target the GNPy S-band equipment/spectrum generation rather than manuscript claims.",
            "",
        ]
    else:
        raw_errors = ok["raw_error_db"].astype(float).to_numpy()
        calibrated_errors = ok["calibrated_error_db"].astype(float).to_numpy()
        raw_rmse = float(np.sqrt(np.mean(raw_errors**2)))
        calibrated_rmse = float(np.sqrt(np.mean(calibrated_errors**2)))
        raw_mae = float(np.mean(np.abs(raw_errors)))
        calibrated_mae = float(np.mean(np.abs(calibrated_errors)))
        lines += [
            "## Aggregate metrics for successful rows",
            "",
            f"- Successful cases: `{len(ok)}` of `{len(df)}`.",
            f"- S-band diagnostic offset: `{float(ok['sband_offset_db'].iloc[0]):.6f} dB`.",
            f"- Raw RMSE: `{raw_rmse:.6f} dB`.",
            f"- Raw MAE: `{raw_mae:.6f} dB`.",
            f"- S-band offset-calibrated RMSE: `{calibrated_rmse:.6f} dB`.",
            f"- S-band offset-calibrated MAE: `{calibrated_mae:.6f} dB`.",
            "",
            "## Interpretation",
            "",
            "At least one S-band GNPy case completed. If fewer than three operating points pass, treat this as smoke-test evidence only.",
            "The next step is to expand around the passing wavelength with more spans, launch powers and channel counts.",
            "",
        ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    ensure_dir(TABLES_DIR)
    ensure_dir(REPORTS_DIR)
    ensure_dir(VALIDATION_DIR)

    base_cfg = load_config(BASE_CONFIG)
    rows: list[dict] = []

    for case in CASES:
        print(f"Running S-band starter case: {case['case_id']}")
        status, failure_reason, gnpy_gsnr, stdout_path = run_gnpy_case(case)

        row = {
            **case,
            "span_length_km": SPAN_LENGTH_KM,
            "symbols": SYMBOLS,
            "seeds": ",".join(str(s) for s in SEEDS),
            "s_attenuation_db_per_km": S_ATTENUATION_DB_PER_KM,
            "s_noise_figure_db": S_NOISE_FIGURE_DB,
            "s_edfa_f_min_hz": S_EDFA_F_MIN_HZ,
            "s_edfa_f_max_hz": S_EDFA_F_MAX_HZ,
            "status": status,
            "failure_reason": failure_reason,
            "gnpy_reference_gsnr_db": gnpy_gsnr if gnpy_gsnr is not None else np.nan,
            "oescl_uniform_gsnr_mean_db": np.nan,
            "oescl_uniform_gsnr_std_db": np.nan,
            "oescl_n_seeds": 0,
            "raw_error_db": np.nan,
            "abs_raw_error_db": np.nan,
            "sband_offset_db": np.nan,
            "calibrated_oescl_gsnr_db": np.nan,
            "calibrated_error_db": np.nan,
            "abs_calibrated_error_db": np.nan,
            "gnpy_stdout": str(stdout_path.relative_to(PROJECT_ROOT)) if stdout_path else "",
        }

        if status == "ok" and gnpy_gsnr is not None:
            mean, std, n = run_oescl_case(case, base_cfg)
            row["oescl_uniform_gsnr_mean_db"] = mean
            row["oescl_uniform_gsnr_std_db"] = std
            row["oescl_n_seeds"] = n
            row["raw_error_db"] = mean - float(gnpy_gsnr)
            row["abs_raw_error_db"] = abs(mean - float(gnpy_gsnr))

        rows.append(row)

    df = pd.DataFrame(rows)
    ok_mask = df["status"] == "ok"
    if ok_mask.any():
        offset = float(
            np.mean(
                df.loc[ok_mask, "gnpy_reference_gsnr_db"].astype(float)
                - df.loc[ok_mask, "oescl_uniform_gsnr_mean_db"].astype(float)
            )
        )
        df.loc[ok_mask, "sband_offset_db"] = offset
        df.loc[ok_mask, "calibrated_oescl_gsnr_db"] = (
            df.loc[ok_mask, "oescl_uniform_gsnr_mean_db"].astype(float) + offset
        )
        df.loc[ok_mask, "calibrated_error_db"] = (
            df.loc[ok_mask, "calibrated_oescl_gsnr_db"].astype(float)
            - df.loc[ok_mask, "gnpy_reference_gsnr_db"].astype(float)
        )
        df.loc[ok_mask, "abs_calibrated_error_db"] = df.loc[
            ok_mask, "calibrated_error_db"
        ].abs()

    table_path = TABLES_DIR / "sband_starter_gnpy_validation.csv"
    df.to_csv(table_path, index=False)
    report_path = write_report(df)

    print(f"Wrote {table_path.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {report_path.relative_to(PROJECT_ROOT)}")
    print(df[["case_id", "status", "gnpy_reference_gsnr_db", "oescl_uniform_gsnr_mean_db", "raw_error_db", "calibrated_error_db"]].to_string(index=False))


if __name__ == "__main__":
    main()
