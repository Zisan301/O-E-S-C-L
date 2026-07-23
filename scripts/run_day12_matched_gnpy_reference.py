#!/usr/bin/env python
"""
Day-12 matched GNPy reference generation for O-E-S-C-L.

This script fixes the main mismatch seen after Day-11:
- GNPy default spectrum was 32 Gbaud / 50 GHz spacing.
- O-E-S-C-L uses 64 Gbaud / 75 GHz spacing.
- The prior S-band run still used C-band-like frequencies.

The script generates matched spectrum JSON files, matched network files,
a patched equipment file, runs GNPy for 8 cases, extracts receiver
"GSNR (signal bw, dB)", and writes validation_data/gnpy_day11_reference.csv.

Run from the project root, inside the gnpy_env:
    python scripts/run_day12_matched_gnpy_reference.py --config config/day12_matched_gnpy_reference_config.yaml
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

C_LIGHT = 299_792_458.0


def read_config(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required. Install with: pip install pyyaml")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def to_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value))


def wavelength_nm_to_frequency_hz(wavelength_nm: float) -> float:
    return C_LIGHT / (wavelength_nm * 1e-9)


def dispersion_ps_nm_km_to_s_m2(value: float) -> float:
    """GNPy uses SI dispersion units; 16.7 ps/nm/km -> 1.67e-05."""
    return value * 1e-6


def build_spectrum(center_hz: float, slot_width_hz: float, n_channels: int,
                   baud_rate_hz: float, roll_off: float, tx_osnr_db: float) -> Dict[str, Any]:
    if n_channels < 1:
        raise ValueError("n_channels must be >= 1")
    half = (n_channels - 1) / 2.0
    f_min = center_hz - half * slot_width_hz
    f_max = center_hz + half * slot_width_hz
    return {
        "spectrum": [
            {
                "f_min": f_min,
                "f_max": f_max,
                "baud_rate": baud_rate_hz,
                "slot_width": slot_width_hz,
                "roll_off": roll_off,
                "tx_osnr": tx_osnr_db,
            }
        ]
    }


def patch_frequency_ranges(obj: Any, f_min: float, f_max: float) -> None:
    """Recursively widen frequency ranges where present."""
    if isinstance(obj, dict):
        if "frequency" in obj and isinstance(obj["frequency"], dict):
            obj["frequency"]["min"] = f_min
            obj["frequency"]["max"] = f_max
        # common f_min/f_max entries in Edfa/SI blocks
        if "f_min" in obj and "f_max" in obj:
            try:
                obj["f_min"] = f_min
                obj["f_max"] = f_max
            except Exception:
                pass
        for v in obj.values():
            patch_frequency_ranges(v, f_min, f_max)
    elif isinstance(obj, list):
        for item in obj:
            patch_frequency_ranges(item, f_min, f_max)


def patch_si_and_modes(obj: Any, baud_rate_hz: float, spacing_hz: float, roll_off: float, tx_osnr_db: float) -> None:
    """Recursively align common SI/mode fields."""
    if isinstance(obj, dict):
        # SpectralInformation/SI-like blocks
        if "baud_rate" in obj:
            try:
                obj["baud_rate"] = baud_rate_hz
            except Exception:
                pass
        if "spacing" in obj:
            try:
                obj["spacing"] = spacing_hz
            except Exception:
                pass
        if "slot_width" in obj:
            try:
                obj["slot_width"] = spacing_hz
            except Exception:
                pass
        if "min_spacing" in obj:
            try:
                obj["min_spacing"] = spacing_hz
            except Exception:
                pass
        if "roll_off" in obj:
            try:
                obj["roll_off"] = roll_off
            except Exception:
                pass
        if "tx_osnr" in obj:
            try:
                obj["tx_osnr"] = tx_osnr_db
            except Exception:
                pass
        for v in obj.values():
            patch_si_and_modes(v, baud_rate_hz, spacing_hz, roll_off, tx_osnr_db)
    elif isinstance(obj, list):
        for item in obj:
            patch_si_and_modes(item, baud_rate_hz, spacing_hz, roll_off, tx_osnr_db)


def ensure_fiber_types(equipment: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    fibers = equipment.setdefault("Fiber", [])
    if not isinstance(fibers, list):
        raise RuntimeError("Unexpected equipment Fiber structure; expected list")
    existing = {item.get("type_variety") for item in fibers if isinstance(item, dict)}
    for band in ["C", "S"]:
        fcfg = cfg["gnpy"]["fiber"][band]
        tv = str(fcfg["type_variety"])
        if tv not in existing:
            fibers.append({
                "type_variety": tv,
                "dispersion": dispersion_ps_nm_km_to_s_m2(to_float(fcfg["dispersion_ps_nm_km"])),
                "effective_area": to_float(fcfg.get("effective_area_m2", 8.3e-11)),
                "pmd_coef": 1.265e-15,
            })


def ensure_wide_edfa(equipment: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    edfas = equipment.setdefault("Edfa", [])
    if not isinstance(edfas, list):
        raise RuntimeError("Unexpected equipment Edfa structure; expected list")
    target_tv = str(cfg["gnpy"]["edfa_type_variety"])
    if any(isinstance(item, dict) and item.get("type_variety") == target_tv for item in edfas):
        return
    base = None
    for item in edfas:
        if isinstance(item, dict) and item.get("type_variety") == "std_medium_gain":
            base = deepcopy(item)
            break
    if base is None:
        for item in edfas:
            if isinstance(item, dict) and item.get("type_def") == "variable_gain":
                base = deepcopy(item)
                break
    if base is None:
        base = {
            "type_def": "variable_gain",
            "gain_flatmax": 26,
            "gain_min": 12,
            "p_max": 23,
            "nf_min": 6,
            "nf_max": 10,
            "out_voa_auto": False,
            "allowed_for_design": True,
        }
    base["type_variety"] = target_tv
    base["f_min"] = to_float(cfg["gnpy"]["edfa_frequency_min_hz"])
    base["f_max"] = to_float(cfg["gnpy"]["edfa_frequency_max_hz"])
    # Keep it available for auto-design.
    base["allowed_for_design"] = True
    edfas.append(base)


def create_matched_equipment(cfg: Dict[str, Any], root: Path) -> Path:
    base_path = root / cfg["gnpy"]["base_equipment"]
    out_path = root / cfg["gnpy"]["matched_equipment"]
    if not base_path.exists():
        raise FileNotFoundError(f"Base equipment not found: {base_path}")
    equipment = json.loads(base_path.read_text(encoding="utf-8"))
    patch_frequency_ranges(equipment, to_float(cfg["gnpy"]["edfa_frequency_min_hz"]), to_float(cfg["gnpy"]["edfa_frequency_max_hz"]))
    patch_si_and_modes(
        equipment,
        to_float(cfg["gnpy"]["baud_rate_hz"]),
        to_float(cfg["gnpy"]["slot_width_hz"]),
        to_float(cfg["gnpy"]["roll_off"]),
        to_float(cfg["gnpy"]["tx_osnr_db"]),
    )
    ensure_fiber_types(equipment, cfg)
    ensure_wide_edfa(equipment, cfg)
    ensure_dir(out_path.parent)
    out_path.write_text(json.dumps(equipment, indent=2), encoding="utf-8")
    return out_path


def create_matched_networks(cfg: Dict[str, Any], root: Path) -> Dict[str, Path]:
    results: Dict[str, Path] = {}
    edfa_type = str(cfg["gnpy"]["edfa_type_variety"])
    for band in ["C", "S"]:
        base = root / cfg["gnpy"]["base_networks"][band]
        out = root / cfg["gnpy"]["matched_networks"][band]
        if not base.exists():
            raise FileNotFoundError(f"Base network not found: {base}")
        data = json.loads(base.read_text(encoding="utf-8"))
        fiber_tv = str(cfg["gnpy"]["fiber"][band]["type_variety"])
        loss_coef = to_float(cfg["gnpy"]["fiber"][band]["loss_coef_db_per_km"])
        for el in data.get("elements", []):
            if not isinstance(el, dict):
                continue
            if el.get("type") == "Fiber":
                el["type_variety"] = fiber_tv
                params = el.setdefault("params", {})
                params["loss_coef"] = loss_coef
                # Dispersion is defined in equipment by type_variety.
            elif el.get("type") == "Edfa":
                el["type_variety"] = edfa_type
        ensure_dir(out.parent)
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        results[band] = out
    return results


def create_spectra(cfg: Dict[str, Any], root: Path) -> Dict[str, Path]:
    results: Dict[str, Path] = {}
    baud = to_float(cfg["gnpy"]["baud_rate_hz"])
    slot = to_float(cfg["gnpy"]["slot_width_hz"])
    roll = to_float(cfg["gnpy"]["roll_off"])
    tx_osnr = to_float(cfg["gnpy"]["tx_osnr_db"])
    for band in ["C", "S"]:
        wl_nm = to_float(cfg["gnpy"]["center_wavelength_nm"][band])
        center = wavelength_nm_to_frequency_hz(wl_nm)
        n_ch = int(cfg["gnpy"]["n_channels"][band])
        data = build_spectrum(center, slot, n_ch, baud, roll, tx_osnr)
        path = root / cfg["gnpy"]["spectrum_files"][band]
        ensure_dir(path.parent)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        results[band] = path
    return results


def run_command(cmd: List[str], cwd: Path, log_path: Path) -> Tuple[int, str]:
    ensure_dir(log_path.parent)
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = proc.stdout or ""
    log_path.write_text(output, encoding="utf-8", errors="replace")
    return proc.returncode, output


def parse_receiver_gsnr_signal_bw(output: str) -> float | None:
    # Choose the last GSNR(signal bw) because GNPy prints trx_A first and trx_B later.
    vals = re.findall(r"GSNR\s*\(signal bw,\s*dB\):\s*([-+]?\d+(?:\.\d+)?)", output)
    if not vals:
        return None
    return float(vals[-1])


def parse_first_frequency_range(output: str) -> Tuple[float | None, float | None]:
    freqs = re.findall(r"^\s*\d+\s+([0-9]+\.[0-9]+)\s+", output, flags=re.MULTILINE)
    if not freqs:
        return None, None
    values = [float(x) for x in freqs]
    return min(values), max(values)


def read_existing_reference(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    if not path.exists():
        headers = ["scenario_group", "band", "spans", "launch_power_dbm", "reference_model", "reference_source", "reference_gsnr_db", "notes"]
        rows = []
        for scenario, band, spans in [("C", "C", 10), ("S", "S", 12)]:
            for p in [-2, 0, 2, 4]:
                rows.append({
                    "scenario_group": scenario,
                    "band": band,
                    "spans": str(spans),
                    "launch_power_dbm": str(p),
                    "reference_model": "GNPy",
                    "reference_source": "GNPy local Day-12 matched spectrum run",
                    "reference_gsnr_db": "",
                    "notes": "Matched 64 Gbaud, 75 GHz spectrum reference"
                })
        return headers, rows
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows = list(reader)
    return headers, rows


def update_day11_reference(path: Path, values: List[Dict[str, Any]]) -> None:
    headers, rows = read_existing_reference(path)
    required = ["scenario_group", "band", "spans", "launch_power_dbm", "reference_model", "reference_source", "reference_gsnr_db", "notes"]
    for h in required:
        if h not in headers:
            headers.append(h)
    by_key = {(str(v["scenario_group"]), str(v["band"]), str(v["spans"]), str(v["launch_power_dbm"])): v for v in values}
    existing_keys = set()
    for row in rows:
        key = (row.get("scenario_group", ""), row.get("band", ""), row.get("spans", ""), str(int(float(row.get("launch_power_dbm", "0")))))
        if key in by_key:
            v = by_key[key]
            row["reference_model"] = "GNPy"
            row["reference_source"] = "GNPy local Day-12 matched spectrum run"
            row["reference_gsnr_db"] = f"{float(v['reference_gsnr_db']):.4f}"
            row["notes"] = "Matched 64 Gbaud, 75 GHz spectrum; receiver GSNR(signal bw)"
            existing_keys.add(key)
    for key, v in by_key.items():
        if key not in existing_keys:
            rows.append({
                "scenario_group": key[0],
                "band": key[1],
                "spans": key[2],
                "launch_power_dbm": key[3],
                "reference_model": "GNPy",
                "reference_source": "GNPy local Day-12 matched spectrum run",
                "reference_gsnr_db": f"{float(v['reference_gsnr_db']):.4f}",
                "notes": "Matched 64 Gbaud, 75 GHz spectrum; receiver GSNR(signal bw)"
            })
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in headers})


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    headers = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_report(path: Path, cfg: Dict[str, Any], rows: List[Dict[str, Any]], notes: List[str]) -> None:
    ensure_dir(path.parent)
    lines: List[str] = []
    lines.append("# Day-12 Matched GNPy Reference Report\n")
    lines.append("Day-12 regenerates external GNPy GSNR values using a matched custom spectrum.\n")
    lines.append("## Matching changes\n")
    lines.append(f"- Baud rate: `{cfg['gnpy']['baud_rate_hz']}` Hz\n")
    lines.append(f"- Slot width / spacing: `{cfg['gnpy']['slot_width_hz']}` Hz\n")
    lines.append(f"- C center wavelength: `{cfg['gnpy']['center_wavelength_nm']['C']}` nm\n")
    lines.append(f"- S center wavelength: `{cfg['gnpy']['center_wavelength_nm']['S']}` nm\n")
    lines.append(f"- C channels: `{cfg['gnpy']['n_channels']['C']}`\n")
    lines.append(f"- S channels: `{cfg['gnpy']['n_channels']['S']}`\n")
    lines.append("\n## Extracted receiver GSNR values\n")
    if rows:
        lines.append("| band | spans | launch power (dBm) | GSNR signal bw (dB) | freq min THz | freq max THz | status |\n")
        lines.append("|---|---:|---:|---:|---:|---:|---|\n")
        for r in rows:
            lines.append(
                f"| {r['band']} | {r['spans']} | {r['launch_power_dbm']} | "
                f"{r.get('reference_gsnr_db', '')} | {r.get('freq_min_thz', '')} | {r.get('freq_max_thz', '')} | {r.get('status', '')} |\n"
            )
    else:
        lines.append("No GNPy values were extracted. Check logs.\n")
    if notes:
        lines.append("\n## Notes / warnings\n")
        for n in notes:
            lines.append(f"- {n}\n")
    lines.append("\n## Next step\n")
    lines.append("Run Day-11 again after this script updates `validation_data/gnpy_day11_reference.csv`:\n\n")
    lines.append("```powershell\n")
    lines.append("python scripts\\run_day11_external_validation.py --config config\\day11_external_validation_config.yaml\n")
    lines.append("```\n")
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/day12_matched_gnpy_reference_config.yaml")
    parser.add_argument("--prepare-only", action="store_true", help="Only generate equipment/network/spectrum files; do not run GNPy")
    parser.add_argument("--run-day11", action="store_true", help="Run Day-11 after updating the reference CSV")
    args = parser.parse_args()

    root = Path.cwd()
    cfg_path = root / args.config
    cfg = read_config(cfg_path)

    notes: List[str] = []
    equipment_path = create_matched_equipment(cfg, root)
    networks = create_matched_networks(cfg, root)
    spectra = create_spectra(cfg, root)

    print("Created matched equipment:", equipment_path)
    print("Created matched networks:", networks)
    print("Created matched spectra:", spectra)

    rows: List[Dict[str, Any]] = []
    if not args.prepare_only:
        cmd_name = str(cfg["gnpy"].get("command", "gnpy-transmission-example"))
        powers = [int(p) for p in cfg["gnpy"]["powers_dbm"]]
        log_dir = root / cfg["output"]["logs_dir"]
        for band in ["C", "S"]:
            spans = 10 if band == "C" else 12
            for p in powers:
                log_path = log_dir / f"gnpy_day12_{band}_{spans}sp_{p:+d}dBm.log"
                cmd = [
                    cmd_name,
                    str(networks[band]),
                    "-e", str(equipment_path),
                    "--spectrum", str(spectra[band]),
                    "--show-channels",
                    "-po", str(p),
                ]
                print("Running:", " ".join(cmd))
                rc, output = run_command(cmd, root, log_path)
                gsnr = parse_receiver_gsnr_signal_bw(output)
                fmin, fmax = parse_first_frequency_range(output)
                row = {
                    "scenario_group": band,
                    "band": band,
                    "spans": spans,
                    "launch_power_dbm": p,
                    "reference_model": "GNPy",
                    "reference_source": "GNPy local Day-12 matched spectrum run",
                    "reference_gsnr_db": "" if gsnr is None else f"{gsnr:.4f}",
                    "freq_min_thz": "" if fmin is None else f"{fmin:.5f}",
                    "freq_max_thz": "" if fmax is None else f"{fmax:.5f}",
                    "return_code": rc,
                    "status": "ok" if (rc == 0 and gsnr is not None) else "failed",
                    "log_path": str(log_path),
                    "notes": "Matched 64 Gbaud, 75 GHz spectrum; receiver GSNR(signal bw)",
                }
                if rc != 0:
                    notes.append(f"GNPy command failed for {band} {spans} spans {p:+d} dBm. See {log_path}")
                if gsnr is None:
                    notes.append(f"Could not parse GSNR(signal bw) for {band} {spans} spans {p:+d} dBm. See {log_path}")
                rows.append(row)

        table_path = root / cfg["output"]["table"]
        write_csv(table_path, rows)
        print("Wrote:", table_path)

        ok_rows = [r for r in rows if r.get("status") == "ok"]
        if cfg["output"].get("update_day11_reference_csv", True) and len(ok_rows) == 8:
            ref_path = root / cfg["output"]["day11_reference_csv"]
            update_day11_reference(ref_path, ok_rows)
            print("Updated:", ref_path)
        else:
            notes.append("Day-11 reference CSV was not updated because not all 8 GNPy runs completed successfully.")

        if args.run_day11 or bool(cfg["output"].get("run_day11_after", False)):
            day11_cfg = str(cfg["output"].get("day11_config", "config/day11_external_validation_config.yaml"))
            day11_cmd = [sys.executable, "scripts/run_day11_external_validation.py", "--config", day11_cfg]
            rc, out = run_command(day11_cmd, root, root / "results/logs/day12_run_day11_after.log")
            print(out)
            if rc != 0:
                notes.append("Day-11 rerun returned a non-zero code. See results/logs/day12_run_day11_after.log")

    report_path = root / cfg["output"]["report"]
    write_report(report_path, cfg, rows, notes)
    print("Report:", report_path)
    print("Day-12 completed. Next: rerun Day-11 and send the report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
