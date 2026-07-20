from __future__ import annotations

import numpy as np

from .constellation import square_16qam_points, decision_indices


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


def bit_metric_gmi_awgn(
    tx_indices: np.ndarray,
    rx_symbols: np.ndarray,
    noise_var: float,
    priors: np.ndarray | None = None,
    max_samples: int | None = None,
) -> tuple[float, float]:
    points = square_16qam_points()
    labels = gray_labels_16qam()
    tx_bits = indices_to_bits(tx_indices)

    rx = np.asarray(rx_symbols)
    if max_samples is not None and len(rx) > int(max_samples):
        idx = np.linspace(0, len(rx) - 1, int(max_samples)).astype(int)
        rx = rx[idx]
        tx_bits = tx_bits[idx]

    if priors is None:
        priors = np.ones(len(points), dtype=float) / len(points)
    priors = np.asarray(priors, dtype=float)
    priors = np.clip(priors, 1e-15, 1.0)
    priors = priors / np.sum(priors)

    noise_var = max(float(noise_var), 1e-9)
    d2 = np.abs(rx.reshape(-1, 1) - points.reshape(1, -1)) ** 2
    log_like = -d2 / noise_var + np.log(priors.reshape(1, -1))

    gmi = 0.0
    m = labels.shape[1]

    for bit_pos in range(m):
        mask0 = labels[:, bit_pos] == 0
        mask1 = labels[:, bit_pos] == 1

        max0 = np.max(log_like[:, mask0], axis=1, keepdims=True)
        max1 = np.max(log_like[:, mask1], axis=1, keepdims=True)

        logp0 = max0[:, 0] + np.log(np.sum(np.exp(log_like[:, mask0] - max0), axis=1))
        logp1 = max1[:, 0] + np.log(np.sum(np.exp(log_like[:, mask1] - max1), axis=1))

        llr = logp0 - logp1
        b = tx_bits[:, bit_pos]
        signed = np.where(b == 0, 1.0, -1.0) * llr
        ib = 1.0 - float(np.mean(np.log2(1.0 + np.exp(-np.clip(signed, -60, 60)))))
        gmi += max(0.0, ib)

    ngmi = float(np.clip(gmi / m, 0.0, 1.0))
    return float(np.clip(gmi, 0.0, m)), ngmi


def ber_from_decision(tx_indices: np.ndarray, rx_symbols: np.ndarray) -> float:
    rx_indices = decision_indices(rx_symbols)
    tx_bits = indices_to_bits(tx_indices)
    rx_bits = indices_to_bits(rx_indices)
    return float(np.mean(tx_bits != rx_bits))
