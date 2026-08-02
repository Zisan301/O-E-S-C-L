"""Final-confirmation engine adapter.

This module reuses the existing Day-8 waveform surrogate engine but writes
publication-facing confirmation rows with entropy-corrected BMD quantities.

It does not modify old Day-8 code.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.oescl.config import load_config
from src.oescl.day8_q3_band_comparison import _run_one


REQUIRED_COLUMNS = [
    "scenario",
    "stage",
    "seed",
    "symbols",
    "nu",
    "spans",
    "launch_power_dbm",
    "uniform_bmd_rate_bit_per_symbol",
    "pcs_stored_score_bit_per_symbol",
    "entropy_correction_bit_per_symbol",
    "pcs_corrected_bmd_rate_bit_per_symbol",
    "delta_corrected_bmd_gain_bit_per_symbol",
    "ber_uniform",
    "ber_pcs",
    "gsnr_uniform_db",
    "gsnr_pcs_db",
    "notes",
]


def scenario_bands(scenario: str) -> list[str]:
    if scenario == "C":
        return ["C"]
    if scenario == "S":
        return ["S"]
    if scenario == "C+S":
        return ["C", "S"]
    raise ValueError(f"Unsupported scenario: {scenario}")


def mean_metric(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows]
    return sum(values) / len(values)


def load_day8_config(symbols: int) -> dict[str, Any]:
    cfg_path = ROOT / "config" / "day8_q3_band_comparison_config.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Missing Day-8 config: {cfg_path}")

    cfg = load_config(str(cfg_path))
    cfg["day8"]["symbols"] = int(symbols)
    return cfg


def run_confirmation_job(
    scenario: str,
    seed: int,
    symbols: int,
    nu: float,
    spans: int,
    launch_power_dbm: float,
) -> dict[str, Any]:
    """Run one final-confirmation job and return one publication-facing row."""

    cfg = load_day8_config(symbols)
    bands = scenario_bands(scenario)

    uniform_rows = []
    pcs_rows = []

    for band in bands:
        uniform_rows.append(
            _run_one(
                seed=int(seed),
                scenario=scenario,
                band=band,
                spans=int(spans),
                power=float(launch_power_dbm),
                nu=0.0,
                cfg=cfg,
            )
        )

        pcs_rows.append(
            _run_one(
                seed=int(seed),
                scenario=scenario,
                band=band,
                spans=int(spans),
                power=float(launch_power_dbm),
                nu=float(nu),
                cfg=cfg,
            )
        )

    uniform_bmd = mean_metric(uniform_rows, "bmd_gmi_bits_per_symbol")
    pcs_stored_score = mean_metric(pcs_rows, "bmd_gmi_bits_per_symbol")

    pcs_entropy = mean_metric(pcs_rows, "symbol_entropy_bits")
    entropy_correction = 4.0 - pcs_entropy

    pcs_corrected_bmd = pcs_stored_score - entropy_correction
    delta_corrected = pcs_corrected_bmd - uniform_bmd

    ber_uniform = mean_metric(uniform_rows, "ber")
    ber_pcs = mean_metric(pcs_rows, "ber")
    gsnr_uniform = mean_metric(uniform_rows, "gsnr_db")
    gsnr_pcs = mean_metric(pcs_rows, "gsnr_db")

    notes = "day8_waveform_surrogate_confirmation_adapter"
    if scenario == "C+S":
        notes += "; C+S uses existing Day-8 two-band surrogate and stress/penalty logic"

    return {
        "scenario": scenario,
        "stage": "final_confirmation",
        "seed": int(seed),
        "symbols": int(symbols),
        "nu": float(nu),
        "spans": int(spans),
        "launch_power_dbm": float(launch_power_dbm),
        "uniform_bmd_rate_bit_per_symbol": uniform_bmd,
        "pcs_stored_score_bit_per_symbol": pcs_stored_score,
        "entropy_correction_bit_per_symbol": entropy_correction,
        "pcs_corrected_bmd_rate_bit_per_symbol": pcs_corrected_bmd,
        "delta_corrected_bmd_gain_bit_per_symbol": delta_corrected,
        "ber_uniform": ber_uniform,
        "ber_pcs": ber_pcs,
        "gsnr_uniform_db": gsnr_uniform,
        "gsnr_pcs_db": gsnr_pcs,
        "notes": notes,
    }


def format_confirmation_row(row: dict[str, Any]) -> dict[str, str]:
    """Format row for stable CSV writing."""

    formatted: dict[str, str] = {}
    for key in REQUIRED_COLUMNS:
        value = row[key]
        if isinstance(value, float):
            formatted[key] = f"{value:.10g}"
        else:
            formatted[key] = str(value)
    return formatted