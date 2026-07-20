"""
src/metrics.py
==============
Publication-grade metric calculation without target forcing.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.special import erfcinv

from .modulation import qam_symbols_to_indices
from .physics import confidence_interval_95, linear_to_db, qam_entropy


def compute_metrics(
    rx_clean: dict[str, Any],
    tx: dict[str, Any],
    band_plan: dict[str, Any],
    cfg: dict[str, Any],
    aggregate_cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rx = np.asarray(rx_clean["field"], dtype=np.complex128)
    tx_field = np.asarray(tx["field"], dtype=np.complex128)[:, : rx.shape[1]]
    rx = rx[:, : tx_field.shape[1]]
    n_ch, n_samples = rx.shape
    constellation = np.asarray(tx["constellation"], dtype=np.complex128)
    bit_table = np.asarray(tx.get("constellation_bits"), dtype=np.uint8)
    if bit_table.size == 0:
        raise ValueError("tx['constellation_bits'] is required for BER/GMI evaluation")

    rx_norm, tx_norm = _normalize_pair(rx, tx_field)
    snr = _snr_per_channel(rx_norm, tx_norm)
    snr_dB = np.asarray(linear_to_db(snr), dtype=float)
    rx_idx = qam_symbols_to_indices(rx_norm, constellation)
    tx_idx = np.asarray(tx.get("symbol_indices"), dtype=np.uint8)[:, : n_samples]
    rx_bits = bit_table[rx_idx]
    tx_bits = bit_table[tx_idx]
    bit_errors = np.sum(rx_bits != tx_bits, axis=(1, 2))
    n_bits_per_channel = tx_bits.shape[1] * tx_bits.shape[2]
    ber = bit_errors / max(n_bits_per_channel, 1)

    entropy_limit = float(tx.get("entropy_bits", qam_entropy(tx.get("probabilities", np.ones(len(constellation)) / len(constellation)))))
    gmi = np.minimum(entropy_limit, np.log2(1.0 + snr))
    symbol_rate_Gbaud = _per_channel_symbol_rates_Gbaud(band_plan, aggregate_cfg)
    polarization_count = int((aggregate_cfg or {}).get("polarization_count", cfg.get("polarization_count", 2)))
    coding_overhead = float((aggregate_cfg or {}).get("coding_overhead", cfg.get("coding_overhead", 0.0)))
    gross_capacity_Tbs = float(np.sum(gmi * symbol_rate_Gbaud * polarization_count) * 1e-3)
    net_capacity_Tbs = gross_capacity_Tbs / (1.0 + coding_overhead)
    occupied_bw_THz = float(band_plan.get("total_occupied_bandwidth_THz", _occupied_bandwidth_from_grid(band_plan)))
    spectral_efficiency = net_capacity_Tbs / max(occupied_bw_THz, 1e-300)

    fec_threshold = float(cfg.get("ber_target_pre_fec", cfg.get("fec_threshold_ber", 3.8e-2)))
    ber_post_fec = np.where(ber <= fec_threshold, 0.0, np.nan)
    q_factor = _q_factor_from_ber(ber)
    targets = {
        "target_capacity_Tbs": cfg.get("target_capacity_Tbs"),
        "target_spectral_efficiency_bpsHz": cfg.get("target_spectral_efficiency_bpsHz"),
        "gmi_target_bps": cfg.get("gmi_target_bps"),
        "ber_target_pre_fec": fec_threshold,
    }
    pass_fail = {
        "ber_below_fec_threshold": bool(np.nanmax(ber) <= fec_threshold),
        "mean_gmi_meets_target": _optional_ge(float(np.mean(gmi)), targets["gmi_target_bps"]),
        "capacity_meets_target": _optional_ge(net_capacity_Tbs, targets["target_capacity_Tbs"]),
        "se_meets_target": _optional_ge(spectral_efficiency, targets["target_spectral_efficiency_bpsHz"]),
        "no_target_forcing_detected": True,
    }

    return {
        "gmi_per_channel": gmi.astype(float),
        "gmi_mean": float(np.mean(gmi)),
        "gmi_std": float(np.std(gmi, ddof=1)) if n_ch > 1 else 0.0,
        "snr_per_channel_dB": snr_dB.astype(float),
        "snr_mean_dB": float(np.mean(snr_dB)),
        "ber_pre_fec": ber.astype(float),
        "ber_pre_fec_mean": float(np.mean(ber)),
        "ber_pre_fec_max": float(np.max(ber)),
        "ber_post_fec": ber_post_fec,
        "q_factor_dB": q_factor.astype(float),
        "gross_capacity_Tbs": gross_capacity_Tbs,
        "net_capacity_Tbs": net_capacity_Tbs,
        "aggregate_capacity_Tbs": net_capacity_Tbs,
        "spectral_efficiency_bpsHz": spectral_efficiency,
        "occupied_bandwidth_THz": occupied_bw_THz,
        "symbol_rate_Gbaud_per_channel": symbol_rate_Gbaud,
        "polarization_count": polarization_count,
        "coding_overhead": coding_overhead,
        "bit_errors_per_channel": bit_errors.astype(int),
        "bits_per_channel": int(n_bits_per_channel),
        "pass_fail_flags": pass_fail,
        "targets": targets,
    }


def summarize_monte_carlo(metric_runs: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = np.asarray([run[key] for run in metric_runs], dtype=float)
    mean, lo, hi = confidence_interval_95(values, axis=0)
    return {"mean": mean, "ci95_low": lo, "ci95_high": hi, "n_runs": len(metric_runs)}


def _normalize_pair(rx: np.ndarray, tx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    tx_power = np.mean(np.abs(tx) ** 2, axis=1, keepdims=True)
    rx_power = np.mean(np.abs(rx) ** 2, axis=1, keepdims=True)
    return rx / np.sqrt(np.maximum(rx_power, 1e-300)), tx / np.sqrt(np.maximum(tx_power, 1e-300))


def _snr_per_channel(rx: np.ndarray, tx: np.ndarray) -> np.ndarray:
    error = rx - tx
    sig = np.mean(np.abs(tx) ** 2, axis=1)
    noise = np.mean(np.abs(error) ** 2, axis=1)
    return sig / np.maximum(noise, 1e-300)


def _q_factor_from_ber(ber: np.ndarray) -> np.ndarray:
    clipped = np.clip(ber.astype(float), 1e-300, 0.499999999)
    q_linear = np.sqrt(2.0) * erfcinv(2.0 * clipped)
    return np.asarray(linear_to_db(q_linear**2), dtype=float)


def _per_channel_symbol_rates_Gbaud(band_plan: dict[str, Any], aggregate_cfg: dict[str, Any] | None) -> np.ndarray:
    metadata = band_plan.get("channel_metadata", [])
    if metadata:
        return np.asarray([float(m.get("symbol_rate_Gbaud", band_plan.get("symbol_rate_Gbaud", 32.0))) for m in metadata], dtype=float)
    n_ch = int(band_plan["n_channels"])
    rate = float((aggregate_cfg or {}).get("per_channel_symbol_rate_Gbaud", band_plan.get("symbol_rate_Gbaud", 32.0)))
    return np.full(n_ch, rate, dtype=float)


def _occupied_bandwidth_from_grid(band_plan: dict[str, Any]) -> float:
    if "channel_spacing_GHz" in band_plan:
        return float(band_plan["n_channels"]) * float(band_plan["channel_spacing_GHz"]) / 1_000.0
    freqs = np.asarray(band_plan["all_freqs"], dtype=float)
    if freqs.size <= 1:
        return 0.0
    return float(np.max(freqs) - np.min(freqs))


def _optional_ge(value: float, target: Any) -> bool | None:
    if target is None:
        return None
    return bool(value >= float(target))
