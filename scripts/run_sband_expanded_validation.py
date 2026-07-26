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
VALIDATION_DIR = PROJECT_ROOT / "validation_data/day15_sband_expanded"

SYMBOLS = 16384
SEEDS = [1, 2, 3]
SSFM_STEPS_PER_SPAN = 8
PCS_NU = 0.0
SPAN_LENGTH_KM = 80.0

S_ATTENUATION_DB_PER_KM = 0.22
S_NOISE_FIGURE_DB = 5.5
S_EDFA_F_MIN_HZ = 196.0e12
S_EDFA_F_MAX_HZ = 202.0e12

# Keep S-band validation focused: first vary span count and launch power at a
# stable 1520-nm diagnostic wavelength. Wavelength-only smoke evidence is useful,
# but span/power diversity is stronger for manuscript evidence.
CASES = [
    {
        "case_id": "day15_S_1520nm_6sp_m1dBm_3ch_32G",
        "scenario_group": "S",
        "band": "S",
        "spans": 6,
        "launch_power_dbm": -1.0,
        "center_nm": 1520.0,
        "baud_rate_gbaud": 32.0,
        "channel_spacing_ghz": 100.0,
        "channels": 3,
    },
    {
        "case_id": "day15_S_1520nm_6sp_0dBm_3ch_32G",
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
        "case_id": "day15_S_1520nm_6sp_1dBm_3ch_32G",
        "scenario_group": "S",
        "band": "S",
        "spans": 6,
        "launch_power_dbm": 1.0,
        "center_nm": 1520.0,
        "baud_rate_gbaud": 32.0,
        "channel_spacing_ghz": 100.0,
        "channels": 3,
    },
    {
        "case_id": "day15_S_1520nm_8sp_0dBm_3ch_32G",
        "scenario_group": "S",
        "band": "S",
        "spans": 8,
        "launch_power_dbm": 0.0,
        "center_nm": 1520.0,
        "baud_rate_gbaud": 32.0,
        "channel_spacing_ghz": 100.0,
        "channels": 3,
    },
    {
        "case_id": "day15_S_1520nm_10sp_0dBm_3ch_32G",
        "scenario_group": "S",
        "band": "S",
        "spans": 10,
        "launch_power_dbm": 0.0,
        "center_nm": 1520.0,
        "baud_rate_gbaud": 32.0,
        "channel_spacing_ghz": 100.0,
        "channels": 3,
    },
    {
        "case_id": "day15_S_1520nm_12sp_0dBm_3ch_32G",
        "scenario_group": "S",
        "band": "S",
        "spans": 12,
        "launch_power_dbm": 0.0,
        "center_nm": 1520.0,
        "baud_rate_gbaud": 32.0,
        "channel_spacing_ghz": 100.0,
        "channels": 3,
    },
    {
        "case_id": "day15_S_1520nm_8sp_2dBm_3ch_32G",
        "scenario_group": "S",
        "band": "S",
        "spans": 8,
        "launch_power_dbm": 2.0,
        "center_nm": 1520.0,
        "baud_rate_gbaud": 32.0,
        "channel_spacing_ghz": 100.0,
        "channels": 3,
    },
    {
        "case_id": "day15_S_1520nm_10sp_2dBm_3ch_32G",
        "scenario_group": "S",
        "band": "S",
        "spans": 10,
        "launch_power_dbm": 2.0,
        "center_nm": 1520.0,
        "baud_rate_gbaud": 32.0,
        "channel_spacing_ghz": 100.0,
        "channels": 3,
    },
]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def patch_sband_extra_equipment(extra_eqpt_path: Path) -> None:
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
    patch_sband_extra_equipment(extra_eqpt)

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
    combined += f"RETURN_CODE: {result.returncode}\n\n"
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


def add_offset_columns(df: pd.DataFrame) -> pd.DataFrame:
    ok_mask = df["status"] == "ok"
    df["sband_offset_db"] = np.nan
    df["calibrated_oescl_gsnr_db"] = np.nan
    df["calibrated_error_db"] = np.nan
    df["abs_calibrated_error_db"] = np.nan
    df["loo_offset_db"] = np.nan
    df["loo_calibrated_error_db"] = np.nan
    df["abs_loo_calibrated_error_db"] = np.nan

    if not ok_mask.any():
        return df

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

    ok_indices = list(df.index[ok_mask])
    if len(ok_indices) > 1:
        for idx in ok_indices:
            train = [i for i in ok_indices if i != idx]
            loo_offset = float(
                np.mean(
                    df.loc[train, "gnpy_reference_gsnr_db"].astype(float)
                    - df.loc[train, "oescl_uniform_gsnr_mean_db"].astype(float)
                )
            )
            err = float(
                df.loc[idx, "oescl_uniform_gsnr_mean_db"]
                + loo_offset
                - df.loc[idx, "gnpy_reference_gsnr_db"]
            )
            df.loc[idx, "loo_offset_db"] = loo_offset
            df.loc[idx, "loo_calibrated_error_db"] = err
            df.loc[idx, "abs_loo_calibrated_error_db"] = abs(err)

    return df


def metric_block(ok: pd.DataFrame, prefix: str, col: str) -> list[str]:
    vals = ok[col].astype(float).to_numpy()
    if len(vals) == 0:
        return []
    return [
        f"- {prefix} RMSE: `{float(np.sqrt(np.mean(vals**2))):.6f} dB`.",
        f"- {prefix} MAE: `{float(np.mean(np.abs(vals))):.6f} dB`.",
        f"- {prefix} max abs. error: `{float(np.max(np.abs(vals))):.6f} dB`.",
    ]


def write_report(df: pd.DataFrame) -> Path:
    ok = df[df["status"] == "ok"].copy()
    report_path = REPORTS_DIR / "sband_expanded_gnpy_validation_report.md"

    lines = [
        "# Day-15 Expanded S-band GNPy Validation",
        "",
        "This run expands the passing S-band smoke test into a small span/power-diverse diagnostic matrix.",
        "It should still be reported as external-reference diagnostic evidence rather than experimental validation.",
        "",
        "## Claim policy",
        "",
        "S-band results are valid only for the generated GNPy equipment/spectrum configuration and the tested operating points.",
        "Raw, offset-calibrated and leave-one-out calibrated errors must remain separate.",
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
            "No expanded S-band GNPy case completed. Inspect per-case stdout logs under validation_data/day15_sband_expanded.",
            "",
        ]
    else:
        lines += [
            "## Aggregate metrics for successful rows",
            "",
            f"- Successful cases: `{len(ok)}` of `{len(df)}`.",
            f"- S-band diagnostic offset: `{float(ok['sband_offset_db'].iloc[0]):.6f} dB`.",
        ]
        lines += metric_block(ok, "Raw", "raw_error_db")
        lines += metric_block(ok, "Offset-calibrated", "calibrated_error_db")
        if ok["loo_calibrated_error_db"].notna().any():
            lines += metric_block(ok.dropna(subset=["loo_calibrated_error_db"]), "Leave-one-out calibrated", "loo_calibrated_error_db")
        lines += [
            "",
            "## Interpretation",
            "",
            "If most or all rows pass with low offset-calibrated and leave-one-out error, this can upgrade the manuscript from 'S-band failed starter cases' to 'S-band diagnostic extension'.",
            "If leave-one-out error is large, report the result as limited same-matrix calibration rather than transferable S-band validation.",
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
        print(f"Running expanded S-band case: {case['case_id']}")
        status, failure_reason, gnpy_gsnr, stdout_path = run_gnpy_case(case)

        row = {
            **case,
            "span_length_km": SPAN_LENGTH_KM,
            "symbols": SYMBOLS,
            "seeds": ",".join(str(s) for s in SEEDS),
            "s_attenuation_db_per_km": S_ATTENUATION_DB_PER_KM,
            "s_noise_figure_db": S_NOISE_FIGURE_DB,
            "s_edfa_f_min_thz": S_EDFA_F_MIN_HZ / 1e12,
            "s_edfa_f_max_thz": S_EDFA_F_MAX_HZ / 1e12,
            "status": status,
            "failure_reason": failure_reason,
            "gnpy_reference_gsnr_db": gnpy_gsnr if gnpy_gsnr is not None else np.nan,
            "oescl_uniform_gsnr_mean_db": np.nan,
            "oescl_uniform_gsnr_std_db": np.nan,
            "oescl_n_seeds": 0,
            "raw_error_db": np.nan,
            "abs_raw_error_db": np.nan,
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

    df = add_offset_columns(pd.DataFrame(rows))
    table_path = TABLES_DIR / "sband_expanded_gnpy_validation.csv"
    df.to_csv(table_path, index=False)
    report_path = write_report(df)

    print(f"Wrote {table_path.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {report_path.relative_to(PROJECT_ROOT)}")
    print(
        df[
            [
                "case_id",
                "status",
                "gnpy_reference_gsnr_db",
                "oescl_uniform_gsnr_mean_db",
                "raw_error_db",
                "calibrated_error_db",
                "loo_calibrated_error_db",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
