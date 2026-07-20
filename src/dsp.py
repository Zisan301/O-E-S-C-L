"""
src/dsp.py
==========
Coherent receiver DSP with reference-based diagnostics for reproducible
simulation evaluation.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.fft import fft, ifft, fftfreq

from .modulation import qam_symbols_to_indices
from .physics import linear_to_db


def receiver_dsp(rx_amp: dict[str, Any], dsp_cfg: dict[str, Any], fiber: dict[str, Any], tx_signal: dict[str, Any] | None = None) -> dict[str, Any]:
    field = np.asarray(rx_amp["field"], dtype=np.complex128).copy()
    if field.ndim != 2:
        raise ValueError("receiver_dsp expects field shape (channels, samples)")
    n_ch, n_samples = field.shape
    dt = float(rx_amp["time_step_s"])
    omega = 2.0 * np.pi * fftfreq(n_samples, dt)

    if str(dsp_cfg.get("cd_compensation", "frequency_domain_fft")).lower() != "none":
        length_m = float(fiber["length_km"]) * 1_000.0
        beta2 = float(fiber.get("beta2_s2_per_m", 0.0))
        beta3 = float(fiber.get("beta3_s3_per_m", 0.0))
        cd_inverse = np.exp(1j * beta2 * omega**2 * length_m / 2.0 - 1j * beta3 * omega**3 * length_m / 6.0)
        field = ifft(fft(field, axis=-1) * cd_inverse.reshape(1, -1), axis=-1)

    tx_ref = None if tx_signal is None else np.asarray(tx_signal["field"], dtype=np.complex128)
    if tx_ref is not None:
        tx_ref = tx_ref[:, :n_samples]
        field = field[:, :tx_ref.shape[1]]
        n_samples = field.shape[1]
        field, alignment = _align_to_reference(field, tx_ref)
    else:
        field, alignment = _blind_phase_search(field, dsp_cfg)

    field = _power_normalize(field, tx_ref)
    constellation = np.asarray((tx_signal or rx_amp).get("constellation", _default_constellation()), dtype=np.complex128)
    decisions_idx = qam_symbols_to_indices(_normalize_for_decision(field), constellation)
    decisions = constellation[decisions_idx]

    if tx_ref is not None:
        tx_norm = _power_normalize(tx_ref, tx_ref)
        snr_pre_nli_dB, evm = _measure_snr_evm(_normalize_for_decision(field), _normalize_for_decision(tx_norm))
    else:
        snr_pre_nli_dB = np.full(n_ch, np.nan)
        evm = np.full(n_ch, np.nan)

    return {
        "field": field,
        "rx_aligned": field,
        "decisions": decisions,
        "decision_indices": decisions_idx,
        "time_step_s": dt,
        "n_channels": n_ch,
        "n_samples": n_samples,
        "snr_pre_nli_dB": snr_pre_nli_dB,
        "evm_per_channel": evm,
        "phase_estimates_rad": alignment["phase_rad"],
        "delay_estimates_samples": alignment["delay_samples"],
        "freq_grid": rx_amp.get("freq_grid"),
        "channel_metadata": rx_amp.get("channel_metadata"),
        "constellation": constellation,
        "constellation_bits": (tx_signal or rx_amp).get("constellation_bits"),
        "diagnostics": {"alignment_method": alignment["method"]},
    }


def _align_to_reference(rx: np.ndarray, tx: np.ndarray, max_delay: int = 64) -> tuple[np.ndarray, dict[str, Any]]:
    n_ch, n_samples = rx.shape
    aligned = np.empty_like(rx)
    phases = np.zeros(n_ch, dtype=float)
    delays = np.zeros(n_ch, dtype=int)
    for ch in range(n_ch):
        best_delay = 0
        best_metric = -np.inf
        for delay in range(-max_delay, max_delay + 1):
            shifted = np.roll(rx[ch], delay)
            metric = abs(np.vdot(tx[ch], shifted))
            if metric > best_metric:
                best_metric = metric
                best_delay = delay
        shifted = np.roll(rx[ch], best_delay)
        phase = np.angle(np.vdot(shifted, tx[ch]))
        aligned[ch] = shifted * np.exp(1j * phase)
        phases[ch] = phase
        delays[ch] = best_delay
    return aligned, {"phase_rad": phases, "delay_samples": delays, "method": "reference_correlation"}


def _blind_phase_search(field: np.ndarray, dsp_cfg: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    constellation = _default_constellation()
    bps_states = int(dsp_cfg.get("bps_states", 64))
    window = int(dsp_cfg.get("bps_window", 256))
    phases_grid = np.linspace(-np.pi / 4.0, np.pi / 4.0, bps_states)
    corrected = field.copy()
    n_ch, n_samples = field.shape
    phase_est = np.zeros(n_ch, dtype=float)
    for ch in range(n_ch):
        chunk = field[ch, : min(window, n_samples)]
        metrics = []
        for phi in phases_grid:
            rotated = chunk * np.exp(1j * phi)
            dist = np.min(np.abs(rotated[:, None] - constellation[None, :]) ** 2, axis=1)
            metrics.append(np.mean(dist))
        best_phi = float(phases_grid[int(np.argmin(metrics))])
        corrected[ch] *= np.exp(1j * best_phi)
        phase_est[ch] = best_phi
    return corrected, {"phase_rad": phase_est, "delay_samples": np.zeros(n_ch, dtype=int), "method": "blind_phase_search"}


def _power_normalize(field: np.ndarray, reference: np.ndarray | None) -> np.ndarray:
    if reference is None:
        target_power = np.ones((field.shape[0], 1), dtype=float)
    else:
        target_power = np.mean(np.abs(reference) ** 2, axis=1, keepdims=True)
    power = np.mean(np.abs(field) ** 2, axis=1, keepdims=True)
    return field * np.sqrt(target_power / np.maximum(power, 1e-300))


def _normalize_for_decision(field: np.ndarray) -> np.ndarray:
    power = np.mean(np.abs(field) ** 2, axis=1, keepdims=True)
    return field / np.sqrt(np.maximum(power, 1e-300))


def _measure_snr_evm(rx: np.ndarray, tx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    err = rx - tx
    sig_power = np.mean(np.abs(tx) ** 2, axis=1)
    noise_power = np.mean(np.abs(err) ** 2, axis=1)
    snr = sig_power / np.maximum(noise_power, 1e-300)
    evm = np.sqrt(noise_power / np.maximum(sig_power, 1e-300))
    return np.asarray(linear_to_db(snr), dtype=float), evm.astype(float)


def _default_constellation() -> np.ndarray:
    levels = np.array([-7, -5, -3, -1, 1, 3, 5, 7], dtype=float)
    i_grid, q_grid = np.meshgrid(levels, levels, indexing="ij")
    const = (i_grid + 1j * q_grid).reshape(-1)
    return const / np.sqrt(np.mean(np.abs(const) ** 2))
