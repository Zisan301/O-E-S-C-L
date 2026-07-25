from __future__ import annotations

import numpy as np

from .constellation import (
    square_16qam_points,
    decision_indices,
    entropy_bits,
)


_EPS = 1e-15


def gray_labels_16qam() -> np.ndarray:
    axis_bits = {
        -3: [0, 0],
        -1: [0, 1],
        1: [1, 1],
        3: [1, 0],
    }
    levels = [-3, -1, 1, 3]
    labels = []
    for y in levels:
        for x in levels:
            labels.append(axis_bits[x] + axis_bits[y])
    return np.array(labels, dtype=int)


def indices_to_bits(indices: np.ndarray) -> np.ndarray:
    labels = gray_labels_16qam()
    return labels[np.asarray(indices, dtype=int)]


def estimate_noise_variance_from_decisions(rx_symbols: np.ndarray, tx_symbols: np.ndarray) -> float:
    return float(np.mean(np.abs(rx_symbols - tx_symbols) ** 2))


def _logsumexp(a: np.ndarray, axis: int = 1) -> np.ndarray:
    """Small local logsumexp helper to avoid adding a SciPy runtime dependency."""
    amax = np.max(a, axis=axis, keepdims=True)
    safe = np.where(np.isfinite(amax), amax, 0.0)
    out = safe + np.log(np.sum(np.exp(a - safe), axis=axis, keepdims=True))
    return np.squeeze(out, axis=axis)


def _normalise_priors(priors: np.ndarray | None, n_points: int) -> np.ndarray:
    if priors is None:
        priors = np.ones(n_points, dtype=float) / n_points
    priors = np.asarray(priors, dtype=float)
    if priors.shape != (n_points,):
        raise ValueError(f"Expected {n_points} constellation priors, got shape {priors.shape}.")
    priors = np.clip(priors, _EPS, 1.0)
    return priors / np.sum(priors)


def bit_metric_bmd_awgn_details(
    tx_indices: np.ndarray,
    rx_symbols: np.ndarray,
    noise_var: float,
    priors: np.ndarray | None = None,
    max_samples: int | None = None,
) -> dict[str, float]:
    """Estimate entropy-aware BMD-GMI and NGMI for Gray-labelled 16QAM.

    The previous implementation used the uniform-input bit expression
    ``1 - E[log2(1 + exp(-(-1)^b LLR))]`` and then returned ``GMI / m`` as
    NGMI.  That is not adequate for probabilistically shaped 16QAM because the
    symbol entropy is lower than ``m`` and the bit priors are nonuniform.

    This function uses the BMD achievable-rate form used in the manuscript
    strengthening plan:

        R_BMD = H(X) - sum_i H(B_i | Y)

    and reports the normalized metric as

        NGMI = 1 - (H(X) - R_BMD) / m.

    The returned ``bmd_gmi_bits_per_symbol`` is backward-compatible with the
    old ``gmi`` output name used by downstream scripts, but it is now
    entropy-aware when shaped priors are supplied.
    """
    points = square_16qam_points()
    labels = gray_labels_16qam()
    tx_indices = np.asarray(tx_indices, dtype=int)
    rx = np.asarray(rx_symbols)

    if len(tx_indices) != len(rx):
        raise ValueError("tx_indices and rx_symbols must have the same length.")

    if max_samples is not None and len(rx) > int(max_samples):
        sample_idx = np.linspace(0, len(rx) - 1, int(max_samples)).astype(int)
        rx = rx[sample_idx]
        tx_indices = tx_indices[sample_idx]

    priors = _normalise_priors(priors, len(points))
    symbol_entropy = entropy_bits(priors)
    m = int(labels.shape[1])

    noise_var = max(float(noise_var), 1e-12)
    d2 = np.abs(rx.reshape(-1, 1) - points.reshape(1, -1)) ** 2
    log_joint = -d2 / noise_var + np.log(priors.reshape(1, -1))
    log_norm = _logsumexp(log_joint, axis=1)
    log_post = log_joint - log_norm.reshape(-1, 1)

    tx_bits = labels[tx_indices]
    conditional_entropy_sum = 0.0

    for bit_pos in range(m):
        bit_values = tx_bits[:, bit_pos]
        mask0 = labels[:, bit_pos] == 0
        mask1 = ~mask0

        log_p0 = _logsumexp(log_post[:, mask0], axis=1)
        log_p1 = _logsumexp(log_post[:, mask1], axis=1)
        log_p_true = np.where(bit_values == 0, log_p0, log_p1)
        h_bit_given_y = -float(np.mean(log_p_true / np.log(2.0)))
        conditional_entropy_sum += max(0.0, h_bit_given_y)

    bmd_gmi = symbol_entropy - conditional_entropy_sum
    bmd_gmi = float(np.clip(bmd_gmi, 0.0, symbol_entropy))
    ngmi = 1.0 - (symbol_entropy - bmd_gmi) / float(m)
    ngmi = float(np.clip(ngmi, 0.0, 1.0))

    return {
        "symbol_entropy_bits": float(symbol_entropy),
        "bmd_gmi_bits_per_symbol": bmd_gmi,
        "ngmi": ngmi,
        "conditional_bit_entropy_sum": float(conditional_entropy_sum),
    }


def bit_metric_gmi_awgn(
    tx_indices: np.ndarray,
    rx_symbols: np.ndarray,
    noise_var: float,
    priors: np.ndarray | None = None,
    max_samples: int | None = None,
) -> tuple[float, float]:
    """Backward-compatible wrapper returning entropy-aware BMD-GMI and NGMI."""
    details = bit_metric_bmd_awgn_details(
        tx_indices=tx_indices,
        rx_symbols=rx_symbols,
        noise_var=noise_var,
        priors=priors,
        max_samples=max_samples,
    )
    return details["bmd_gmi_bits_per_symbol"], details["ngmi"]


def ber_from_decision(tx_indices: np.ndarray, rx_symbols: np.ndarray) -> float:
    rx_indices = decision_indices(rx_symbols)
    tx_bits = indices_to_bits(tx_indices)
    rx_bits = indices_to_bits(rx_indices)
    return float(np.mean(tx_bits != rx_bits))
