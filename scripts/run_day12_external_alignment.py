from __future__ import annotations

import copy
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import gnpy
import numpy as np
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.oescl.config import load_config
from src.oescl.day8_q3_band_comparison import _run_one


def center_freq_from_nm(nm: float) -> float:
    return 299_792_458.0 / (nm * 1e-9)


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_gnpy_case_files(
    validation_dir: Path,
    spans: int,
    span_length_km: float,
    attenuation_db_per_km: float,
    noise_figure_db: float,
    center_nm: float,
    baud_rate_gbaud: float,
    channel_spacing_ghz: float,
    channels: int,
    launch_power_dbm: float,
) -> tuple[Path, Path, Path, Path, float]:
    example_data = Path(gnpy.__file__).resolve().parent / "example-data"
    eqpt = example_data / "eqpt_config.json"

    if not eqpt.exists():
        raise FileNotFoundError(f"Cannot find GNPy eqpt_config.json at {eqpt}")

    network_path = validation_dir / f"day12_gnpy_c_{spans}span_network.json"
    extra_eqpt_path = validation_dir / f"day12_gnpy_c_{spans}span_extra_equipment.json"
    spectrum_path = validation_dir / f"day12_gnpy_c_{spans}span_spectrum.json"

    span_loss_db = span_length_km * attenuation_db_per_km

    elements = [
        {
            "uid": "Site_A",
            "type": "Transceiver",
            "metadata": {
                "location": {
                    "city": "Site A",
                    "region": "",
                    "latitude": 0,
                    "longitude": 0,
                }
            },
        }
    ]

    connections = []
    previous = "Site_A"

    for i in range(1, spans + 1):
        fiber_uid = f"Span{i}"
        edfa_uid = f"Edfa{i}"

        elements.append({
            "uid": fiber_uid,
            "type": "Fiber",
            "type_variety": "SSMF",
            "params": {
                "length": span_length_km,
                "loss_coef": attenuation_db_per_km,
                "length_units": "km",
                "att_in": 0,
                "con_in": 0,
                "con_out": 0,
                "pmd_coef": 1.265e-15,
            },
            "metadata": {
                "location": {
                    "region": "",
                    "latitude": i,
                    "longitude": 0,
                }
            },
        })

        connections.append({"from_node": previous, "to_node": fiber_uid})

        elements.append({
            "uid": edfa_uid,
            "type": "Edfa",
            "type_variety": "day12_nf_fixed_gain",
            "operational": {
                "gain_target": span_loss_db,
                "tilt_target": 0,
                "out_voa": 0,
            },
            "metadata": {
                "location": {
                    "region": "",
                    "latitude": i + 0.1,
                    "longitude": 0,
                }
            },
        })

        connections.append({"from_node": fiber_uid, "to_node": edfa_uid})
        previous = edfa_uid

    elements.append({
        "uid": "Site_B",
        "type": "Transceiver",
        "metadata": {
            "location": {
                "city": "Site B",
                "region": "",
                "latitude": spans + 1,
                "longitude": 0,
            }
        },
    })

    connections.append({"from_node": previous, "to_node": "Site_B"})

    network = {
        "network_name": f"Day-12 C-band {spans}x80km GNPy reference",
        "elements": elements,
        "connections": connections,
    }

    extra_eqpt = {
        "Edfa": [
            {
                "type_variety": "day12_nf_fixed_gain",
                "type_def": "fixed_gain",
                "gain_flatmax": max(17, span_loss_db + 2),
                "gain_min": max(5, span_loss_db - 5),
                "p_max": 23,
                "nf0": noise_figure_db,
                "out_voa_auto": False,
                "allowed_for_design": False,
            }
        ]
    }

    center_freq_hz = center_freq_from_nm(center_nm)
    spacing_hz = channel_spacing_ghz * 1e9
    half = (channels - 1) // 2

    f_min = center_freq_hz - half * spacing_hz
    f_max = center_freq_hz + half * spacing_hz

    spectrum = {
        "spectrum": [
            {
                "f_min": f_min,
                "f_max": f_max,
                "slot_width": spacing_hz,
                "baud_rate": baud_rate_gbaud * 1e9,
                "roll_off": 0.15,
                "tx_osnr": 40,
                "tx_power_dbm": launch_power_dbm,
                "label": f"day12-C-1550nm-64G-{channels}ch-{spans}span",
            }
        ]
    }

    network_path.write_text(json.dumps(network, indent=2), encoding="utf-8")
    extra_eqpt_path.write_text(json.dumps(extra_eqpt, indent=2), encoding="utf-8")
    spectrum_path.write_text(json.dumps(spectrum, indent=2), encoding="utf-8")

    return eqpt, network_path, extra_eqpt_path, spectrum_path, center_freq_hz / 1e12


def parse_center_channel_gsnr(text: str, target_freq_thz: float) -> float | None:
    rows = []

    for line in text.splitlines():
        m = re.match(
            r"^\s*(\d+)\s+"
            r"([-+]?\d+(?:\.\d+)?)\s+"
            r"([-+]?\d+(?:\.\d+)?)\s+"
            r"([-+]?\d+(?:\.\d+)?)\s+"
            r"([-+]?\d+(?:\.\d+)?)\s+"
            r"([-+]?\d+(?:\.\d+)?)\s*$",
            line,
        )

        if not m:
            continue

        try:
            ch = int(m.group(1))
            freq_thz = float(m.group(2))
            gsnr_signal_bw_db = float(m.group(6))
        except ValueError:
            continue

        if 180.0 <= freq_thz <= 205.0 and 0.0 < gsnr_signal_bw_db < 60.0:
            rows.append((abs(freq_thz - target_freq_thz), ch, freq_thz, gsnr_signal_bw_db))

    if rows:
        rows.sort(key=lambda x: x[0])
        return float(rows[0][3])

    vals = []
    for m in re.findall(r"GSNR \(signal bw, dB\):\s*([-+]?\d+(?:\.\d+)?)", text):
        try:
            vals.append(float(m))
        except ValueError:
            pass

    if vals:
        return vals[-1]

    return None


def run_gnpy_case(
    validation_dir: Path,
    spans: int,
    cfg: dict,
) -> tuple[float, Path]:
    g = cfg["day12"]["gnpy"]
    eqpt, network, extra_eqpt, spectrum, target_freq_thz = write_gnpy_case_files(
        validation_dir=validation_dir,
        spans=spans,
        span_length_km=float(g["span_length_km"]),
        attenuation_db_per_km=float(g["attenuation_db_per_km"]),
        noise_figure_db=float(g["noise_figure_db"]),
        center_nm=float(g["center_nm"]),
        baud_rate_gbaud=float(g["baud_rate_gbaud"]),
        channel_spacing_ghz=float(g["channel_spacing_ghz"]),
        channels=int(g["channels"]),
        launch_power_dbm=float(cfg["day12"]["launch_power_dbm"]),
    )

    stdout_path = validation_dir / f"day12_gnpy_c_{spans}span_stdout.txt"

    cmd = [
        "gnpy-transmission-example",
        "-e", str(eqpt),
        "--extra-equipment", str(extra_eqpt),
        "--spectrum", str(spectrum),
        "--show-channels",
        "-po", str(float(cfg["day12"]["launch_power_dbm"])),
        str(network),
        "Site_A",
        "Site_B",
    ]

    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        text=True,
        capture_output=True,
        shell=False,
    )

    combined = ""
    combined += "COMMAND:\n" + " ".join(cmd) + "\n\n"
    combined += "STDOUT:\n" + result.stdout + "\n\n"
    combined += "STDERR:\n" + result.stderr + "\n"

    stdout_path.write_text(combined, encoding="utf-8")

    if result.returncode != 0:
        raise RuntimeError(f"GNPy failed for spans={spans}. See {stdout_path}")

    gsnr = parse_center_channel_gsnr(combined, target_freq_thz)
    if gsnr is None:
        raise RuntimeError(f"Could not parse GNPy GSNR for spans={spans}. See {stdout_path}")

    return float(gsnr), stdout_path


def run_oescl_case(spans: int, cfg: dict, base_cfg: dict) -> tuple[float, float, int]:
    d12 = cfg["day12"]

    local = copy.deepcopy(base_cfg)
    local["day8"]["symbols"] = int(d12["symbols"])
    local["day5"]["ssfm_steps_per_span"] = int(d12["ssfm_steps_per_span"])

    values = []
    for seed in map(int, d12["seeds"]):
        row = _run_one(
            seed,
            str(d12["scenario_group"]),
            str(d12["band"]),
            int(spans),
            float(d12["launch_power_dbm"]),
            float(d12["pcs_nu"]),
            local,
        )
        values.append(float(row["gsnr_db"]))

    return float(np.mean(values)), float(np.std(values, ddof=1)) if len(values) > 1 else 0.0, len(values)


def main() -> None:
    cfg_path = PROJECT_ROOT / "config/day12_external_alignment_config.yaml"
    cfg = load_yaml(cfg_path)

    base_cfg_path = PROJECT_ROOT / cfg["base_config"]
    base_cfg = load_config(str(base_cfg_path))

    tables_dir = ensure_dir(PROJECT_ROOT / cfg["day12"]["output"]["tables"])
    reports_dir = ensure_dir(PROJECT_ROOT / cfg["day12"]["output"]["reports"])
    validation_dir = ensure_dir(PROJECT_ROOT / cfg["day12"]["output"]["validation_data"])

    rows = []

    for spans in map(int, cfg["day12"]["spans_list"]):
        print(f"Running Day-12 span case: {spans}")

        gnpy_gsnr, gnpy_stdout = run_gnpy_case(validation_dir, spans, cfg)
        oescl_mean, oescl_std, n_seeds = run_oescl_case(spans, cfg, base_cfg)

        error = oescl_mean - gnpy_gsnr

        rows.append({
            "scenario_group": cfg["day12"]["scenario_group"],
            "band": cfg["day12"]["band"],
            "spans": spans,
            "span_length_km": float(cfg["day12"]["gnpy"]["span_length_km"]),
            "total_length_km": spans * float(cfg["day12"]["gnpy"]["span_length_km"]),
            "launch_power_dbm": float(cfg["day12"]["launch_power_dbm"]),
            "gnpy_reference_gsnr_db": gnpy_gsnr,
            "oescl_uniform_gsnr_mean_db": oescl_mean,
            "oescl_uniform_gsnr_std_db": oescl_std,
            "oescl_n_seeds": n_seeds,
            "gsnr_error_db": error,
            "abs_gsnr_error_db": abs(error),
            "gnpy_stdout": str(gnpy_stdout.relative_to(PROJECT_ROOT)),
        })

    df = pd.DataFrame(rows)
    out_csv = tables_dir / "day12_external_alignment_sweep.csv"
    df.to_csv(out_csv, index=False)

    errors = df["gsnr_error_db"].astype(float).to_numpy()
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    mean_offset = float(np.mean(errors))
    std_offset = float(np.std(errors, ddof=1)) if len(errors) > 1 else 0.0
    error_range = float(np.max(errors) - np.min(errors)) if len(errors) else 0.0

    x = df["spans"].astype(float).to_numpy()
    y = df["gsnr_error_db"].astype(float).to_numpy()
    slope = float(np.polyfit(x, y, 1)[0]) if len(df) >= 2 else 0.0

    if std_offset <= 1.0 and abs(slope) <= 0.25:
        decision = "mostly_constant_offset"
        interpretation = (
            "The O-E-S-C-L absolute GSNR scale appears conservatively offset from GNPy, "
            "but the offset is relatively stable across span count."
        )
    else:
        decision = "span_dependent_mismatch"
        interpretation = (
            "The O-E-S-C-L vs GNPy mismatch changes materially with span count. "
            "This suggests a span-dependent noise/nonlinear scaling mismatch."
        )

    report_path = reports_dir / "day12_external_alignment_report.md"

    report = []
    report.append("# Day-12 External GNPy Alignment Sweep")
    report.append("")
    report.append("Day-12 compares O-E-S-C-L uniform GSNR against independent GNPy center-channel GSNR across multiple C-band span counts.")
    report.append("")
    report.append("## Sweep summary")
    report.append(df.round(6).to_markdown(index=False))
    report.append("")
    report.append("## Aggregate alignment metrics")
    report.append(f"- RMSE: `{rmse:.6f} dB`")
    report.append(f"- Mean error / offset: `{mean_offset:.6f} dB`")
    report.append(f"- Offset standard deviation: `{std_offset:.6f} dB`")
    report.append(f"- Error range: `{error_range:.6f} dB`")
    report.append(f"- Error-vs-span slope: `{slope:.6f} dB/span`")
    report.append("")
    report.append("## Decision")
    report.append(f"- `{decision}`")
    report.append("")
    report.append("## Interpretation")
    report.append(interpretation)
    report.append("")
    report.append("## Manuscript implication")
    if decision == "mostly_constant_offset":
        report.append(
            "Do not claim formal absolute GNPy validation yet. It may be acceptable to report the GNPy comparison as an external calibration diagnostic and to focus manuscript claims on PCS gain trends after explaining the conservative GSNR offset."
        )
    else:
        report.append(
            "Do not claim external validation. The next step should be a Day-13 tuning/calibration step for the absolute GSNR scale before using GNPy as validation evidence."
        )

    report_path.write_text("\n".join(report), encoding="utf-8")

    print("Day-12 external alignment sweep completed.")
    print(f"CSV: {out_csv}")
    print(f"Report: {report_path}")
    print(f"Decision: {decision}")
    print(f"RMSE: {rmse:.6f} dB")
    print(f"Mean offset: {mean_offset:.6f} dB")
    print(f"Offset std: {std_offset:.6f} dB")
    print(f"Slope: {slope:.6f} dB/span")


if __name__ == "__main__":
    main()
