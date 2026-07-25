from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path

import pandas as pd
import gnpy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATION_DIR = PROJECT_ROOT / "validation_data"
REPORT_DIR = PROJECT_ROOT / "results" / "reports"

VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def center_freq_from_nm(nm: float) -> float:
    return 299_792_458.0 / (nm * 1e-9)


def write_gnpy_files() -> tuple[Path, Path, Path, Path, float]:
    example_data = Path(gnpy.__file__).resolve().parent / "example-data"
    eqpt = example_data / "eqpt_config.json"

    if not eqpt.exists():
        raise FileNotFoundError(f"Cannot find GNPy eqpt_config.json at {eqpt}")

    network_path = VALIDATION_DIR / "day11_gnpy_c10_network.json"
    extra_eqpt_path = VALIDATION_DIR / "day11_gnpy_c10_extra_equipment.json"
    spectrum_path = VALIDATION_DIR / "day11_gnpy_c10_spectrum.json"

    span_length_km = 80.0
    loss_coef = 0.19
    span_loss_db = span_length_km * loss_coef

    elements = [
        {
            "uid": "Site_A",
            "type": "Transceiver",
            "metadata": {
                "location": {
                    "city": "Site A",
                    "region": "",
                    "latitude": 0,
                    "longitude": 0
                }
            }
        }
    ]

    connections = []
    previous = "Site_A"

    for i in range(1, 11):
        fiber_uid = f"Span{i}"
        edfa_uid = f"Edfa{i}"

        elements.append({
            "uid": fiber_uid,
            "type": "Fiber",
            "type_variety": "SSMF",
            "params": {
                "length": span_length_km,
                "loss_coef": loss_coef,
                "length_units": "km",
                "att_in": 0,
                "con_in": 0,
                "con_out": 0,
                "pmd_coef": 1.265e-15
            },
            "metadata": {
                "location": {
                    "region": "",
                    "latitude": i,
                    "longitude": 0
                }
            }
        })

        connections.append({"from_node": previous, "to_node": fiber_uid})

        elements.append({
            "uid": edfa_uid,
            "type": "Edfa",
            "type_variety": "day11_nf5_fixed_gain",
            "operational": {
                "gain_target": span_loss_db,
                "tilt_target": 0,
                "out_voa": 0
            },
            "metadata": {
                "location": {
                    "region": "",
                    "latitude": i + 0.1,
                    "longitude": 0
                }
            }
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
                "latitude": 11,
                "longitude": 0
            }
        }
    })

    connections.append({"from_node": previous, "to_node": "Site_B"})

    network = {
        "network_name": "Day-11 C-band 10x80km GNPy reference",
        "elements": elements,
        "connections": connections
    }

    extra_eqpt = {
        "Edfa": [
            {
                "type_variety": "day11_nf5_fixed_gain",
                "type_def": "fixed_gain",
                "gain_flatmax": 17,
                "gain_min": 14,
                "p_max": 23,
                "nf0": 5.0,
                "out_voa_auto": False,
                "allowed_for_design": False
            }
        ]
    }

    center_freq_hz = center_freq_from_nm(1550.0)
    spacing_hz = 75e9

    # 9 channels centered at 1550 nm.
    # Single-channel spectrum crashes GNPy EDFA interpolation.
    f_min = center_freq_hz - 4 * spacing_hz
    f_max = center_freq_hz + 4 * spacing_hz

    spectrum = {
        "spectrum": [
            {
                "f_min": f_min,
                "f_max": f_max,
                "slot_width": spacing_hz,
                "baud_rate": 64e9,
                "roll_off": 0.15,
                "tx_osnr": 40,
                "tx_power_dbm": 2.0,
                "label": "day11-C-1550nm-64G-9ch"
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

    # Fallback: parse final receiver GSNR signal-bandwidth line.
    vals = []
    for m in re.findall(r"GSNR \(signal bw, dB\):\s*([-+]?\d+(?:\.\d+)?)", text):
        try:
            vals.append(float(m))
        except ValueError:
            pass

    if vals:
        return vals[-1]

    return None


def update_reference_csv(gsnr_db: float) -> Path:
    csv_path = VALIDATION_DIR / "gnpy_day10_reference.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Missing {csv_path}. Run Day-11 prepare script first.")

    df = pd.read_csv(csv_path)

    mask = (
        (df["scenario_group"].astype(str) == "C")
        & (df["band"].astype(str) == "C")
        & (df["spans"].astype(int) == 10)
        & (df["launch_power_dbm"].astype(float) == 2.0)
    )

    if mask.sum() == 0:
        raise RuntimeError("Could not find C,C,10,+2 dBm row in gnpy_day10_reference.csv")

    df.loc[mask, "reference_model"] = "GNPy_9ch_center_channel"
    df.loc[mask, "reference_gsnr_db"] = f"{gsnr_db:.6f}"
    df.loc[mask, "notes"] = "Independent Day-11 GNPy 9-channel C-band center-channel GSNR reference."

    df.to_csv(csv_path, index=False)
    return csv_path


def main() -> None:
    eqpt, network, extra_eqpt, spectrum, target_freq_thz = write_gnpy_files()

    stdout_path = VALIDATION_DIR / "day11_gnpy_reference_stdout.txt"
    report_path = REPORT_DIR / "day11_gnpy_reference_report.md"

    cmd = [
        "gnpy-transmission-example",
        "-e", str(eqpt),
        "--extra-equipment", str(extra_eqpt),
        "--spectrum", str(spectrum),
        "--show-channels",
        "-po", "2",
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
        report_path.write_text(
            "# Day-11 GNPy Reference Report\n\n"
            "GNPy run failed. Inspect `validation_data/day11_gnpy_reference_stdout.txt`.\n",
            encoding="utf-8",
        )
        print("GNPy run failed.")
        print(f"Output: {stdout_path}")
        print(f"Report: {report_path}")
        raise SystemExit(result.returncode)

    gsnr = parse_center_channel_gsnr(combined, target_freq_thz)

    if gsnr is None:
        report_path.write_text(
            "# Day-11 GNPy Reference Report\n\n"
            "GNPy ran, but the script could not automatically parse center-channel GSNR.\n\n"
            "Open `validation_data/day11_gnpy_reference_stdout.txt`, find the final per-channel table, "
            "and use the center-channel `GSNR (signal bw, dB)` value.\n",
            encoding="utf-8",
        )
        print("GNPy ran, but GSNR was not auto-parsed.")
        print(f"Output: {stdout_path}")
        print(f"Report: {report_path}")
        return

    csv_path = update_reference_csv(gsnr)

    report = []
    report.append("# Day-11 GNPy Reference Report")
    report.append("")
    report.append("Independent GNPy reference was generated for the accepted Day-10 C-band case.")
    report.append("")
    report.append("## Case")
    report.append("- Scenario: C")
    report.append("- Band: C")
    report.append("- Spans: 10")
    report.append("- Span length: 80 km")
    report.append("- Launch power: +2 dBm")
    report.append("- Baud rate: 64 GBd")
    report.append("- Channel spacing / slot width: 75 GHz")
    report.append("- Center wavelength: 1550 nm")
    report.append("- Spectrum: 9 C-band channels centered at 1550 nm")
    report.append("")
    report.append("## Parsed GNPy reference")
    report.append(f"- reference_gsnr_db: `{gsnr:.6f}`")
    report.append("")
    report.append("## Updated file")
    report.append(f"- `{csv_path.relative_to(PROJECT_ROOT)}`")
    report.append("")
    report.append("Next: rerun Day-10 validation and check the external gate.")

    report_path.write_text("\n".join(report), encoding="utf-8")

    print("Day-11 GNPy reference completed.")
    print(f"Parsed reference_gsnr_db: {gsnr:.6f}")
    print(f"Updated CSV: {csv_path}")
    print(f"Report: {report_path}")
    print(f"Raw GNPy output: {stdout_path}")


if __name__ == "__main__":
    main()
