"""Entropy-corrected BMD utilities for publication-facing O-E-S-C-L outputs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EntropyCorrectedResult:
    scenario: str
    nu: float
    spans: int
    launch_power_dbm: float
    stored_score_gain_bit_per_symbol: float
    entropy_correction_bit_per_symbol: float
    corrected_bmd_gain_bit_per_symbol: float
    corrected_bmd_ci95_bit_per_symbol: float
    rate_gain_gbps_per_representative_channel: float
    rate_gain_ci95_gbps_per_representative_channel: float
    aggregate_rate_gain_gbps: float | None = None
    aggregate_rate_gain_ci95_gbps: float | None = None


def corrected_bmd_gain(stored_score_gain_bit_per_symbol: float, entropy_correction_bit_per_symbol: float) -> float:
    return stored_score_gain_bit_per_symbol - entropy_correction_bit_per_symbol


def rate_gain_gbps(corrected_bmd_gain_bit_per_symbol: float, symbol_rate_gbaud: float = 64.0, polarization_factor: float = 2.0, overhead_factor: float = 1.20) -> float:
    return corrected_bmd_gain_bit_per_symbol * symbol_rate_gbaud * polarization_factor / overhead_factor


def build_publication_band_results() -> list[EntropyCorrectedResult]:
    entropy_correction = 0.02961
    rows = [
        {"scenario": "C", "nu": 0.36, "spans": 10, "launch_power_dbm": 2.0, "stored_score_gain": 0.052577, "ci95_corrected": 0.0211, "aggregate_factor": None},
        {"scenario": "S", "nu": 0.36, "spans": 12, "launch_power_dbm": -2.0, "stored_score_gain": 0.068903, "ci95_corrected": 0.0140, "aggregate_factor": None},
        {"scenario": "C+S", "nu": 0.36, "spans": 12, "launch_power_dbm": 0.0, "stored_score_gain": 0.073238, "ci95_corrected": 0.0148, "aggregate_factor": 2.0},
    ]
    results: list[EntropyCorrectedResult] = []
    for row in rows:
        corrected = corrected_bmd_gain(row["stored_score_gain"], entropy_correction)
        rate = rate_gain_gbps(corrected)
        rate_ci = rate_gain_gbps(row["ci95_corrected"])
        aggregate_factor = row["aggregate_factor"]
        aggregate_rate = None if aggregate_factor is None else rate * aggregate_factor
        aggregate_ci = None if aggregate_factor is None else rate_ci * aggregate_factor
        results.append(EntropyCorrectedResult(
            scenario=row["scenario"],
            nu=row["nu"],
            spans=row["spans"],
            launch_power_dbm=row["launch_power_dbm"],
            stored_score_gain_bit_per_symbol=row["stored_score_gain"],
            entropy_correction_bit_per_symbol=entropy_correction,
            corrected_bmd_gain_bit_per_symbol=corrected,
            corrected_bmd_ci95_bit_per_symbol=row["ci95_corrected"],
            rate_gain_gbps_per_representative_channel=rate,
            rate_gain_ci95_gbps_per_representative_channel=rate_ci,
            aggregate_rate_gain_gbps=aggregate_rate,
            aggregate_rate_gain_ci95_gbps=aggregate_ci,
        ))
    return results
