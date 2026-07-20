from __future__ import annotations

from typing import Dict

import numpy as np

from .constellation import decision_indices, entropy_bits, indices_to_symbols


def estimate_symbol_error_rate(tx_indices: np.ndarray, rx_symbols: np.ndarray) -> float:
    rx_indices = decision_indices(rx_symbols)
    return float(np.mean(rx_indices != tx_indices))


def estimate_ber_from_ser(ser: float, bits_per_symbol: float) -> float:
    bits = max(float(bits_per_symbol), 1.0)
    return float(np.clip(ser / bits, 0.0, 1.0))


def estimate_gsnr_db(tx_symbols: np.ndarray, rx_symbols: np.ndarray) -> float:
    error = rx_symbols - tx_symbols
    signal_power = float(np.mean(np.abs(tx_symbols) ** 2))
    noise_power = float(np.mean(np.abs(error) ** 2))
    return float(10.0 * np.log10(max(signal_power, 1e-15) / max(noise_power, 1e-15)))


def estimate_gmi_ngmi(
    gsnr_db: float,
    probs: np.ndarray,
    modulation_order: int = 16,
) -> tuple[float, float]:
    entropy = entropy_bits(probs)
    snr_linear = 10.0 ** (gsnr_db / 10.0)

    # Conservative AWGN-inspired approximation; suitable for simulation screening,
    # not a substitute for exact bit-metric decoding GMI.
    shannon_like = np.log2(1.0 + snr_linear)
    shaping_penalty = max(0.0, np.log2(modulation_order) - entropy)
    gmi = min(entropy, shannon_like - 0.30 * shaping_penalty)
    gmi = float(np.clip(gmi, 0.0, entropy))
    ngmi = float(np.clip(gmi / max(entropy, 1e-12), 0.0, 1.0))
    return gmi, ngmi


def net_rate_tbps(
    gmi_bits_per_symbol: float,
    baud_rate_gbaud: float,
    n_channels: int,
    polarization_modes: int,
    fec_overhead: float = 0.20,
) -> float:
    gross_tbps = (
        gmi_bits_per_symbol
        * baud_rate_gbaud
        * 1e9
        * n_channels
        * polarization_modes
        / 1e12
    )
    return float(gross_tbps / (1.0 + fec_overhead))


def compute_channel_metrics(
    tx_symbols: np.ndarray,
    tx_indices: np.ndarray,
    rx_symbols: np.ndarray,
    probs: np.ndarray,
    cfg: Dict,
) -> Dict[str, float]:
    entropy = entropy_bits(probs)
    ser = estimate_symbol_error_rate(tx_indices, rx_symbols)
    ber = estimate_ber_from_ser(ser, entropy)
    gsnr_db = estimate_gsnr_db(tx_symbols, rx_symbols)
    gmi, ngmi = estimate_gmi_ngmi(gsnr_db=gsnr_db, probs=probs)
    rate = net_rate_tbps(
        gmi_bits_per_symbol=gmi,
        baud_rate_gbaud=float(cfg["simulation"]["baud_rate_gbaud"]),
        n_channels=1,
        polarization_modes=int(cfg["fiber"]["polarization_modes"]),
    )

    return {
        "entropy_bits_per_symbol": float(entropy),
        "ser": float(ser),
        "ber": float(ber),
        "gsnr_db": float(gsnr_db),
        "gmi_bits_per_symbol": float(gmi),
        "ngmi": float(ngmi),
        "net_rate_tbps": float(rate),
    }
