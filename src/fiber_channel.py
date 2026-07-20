"""
src/fiber_channel.py
====================
Validated scalar/Manakov-style split-step Fourier propagation with diagnostics.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.fft import fft, ifft, fftfreq

from .physics import alpha_db_per_km_to_linear_per_m, ensure_finite


def _as_channel_sample(field: np.ndarray) -> tuple[np.ndarray, bool]:
    arr = np.asarray(field, dtype=np.complex128)
    if arr.ndim == 2:
        return arr[:, None, :], False
    if arr.ndim == 3:
        return arr, True
    raise ValueError("field must have shape (channels, samples) or (channels, polarizations, samples)")


def run_ssfm(tx_signal: dict[str, Any], fiber: dict[str, Any], ssfm: dict[str, Any]) -> dict[str, Any]:
    field3, was_3d = _as_channel_sample(tx_signal["field"])
    field3 = field3.copy()
    n_ch, n_pol, n_samples = field3.shape
    dt = float(tx_signal["time_step_s"])
    length_m = float(fiber["length_km"]) * 1_000.0
    dz_requested = float(ssfm.get("spatial_step_m", 1_000.0))
    if dz_requested <= 0:
        raise ValueError("ssfm.spatial_step_m must be positive")
    n_steps = max(1, int(np.ceil(length_m / dz_requested)))
    dz = length_m / n_steps

    alpha = float(fiber.get("alpha_linear_per_m", alpha_db_per_km_to_linear_per_m(float(fiber.get("attenuation_dB_per_km", 0.0)))))
    beta2 = float(fiber.get("beta2_s2_per_m", 0.0))
    beta3 = float(fiber.get("beta3_s3_per_m", 0.0))
    gamma = float(fiber.get("gamma_per_W_per_m", 0.0))
    manakov_factor = 8.0 / 9.0 if n_pol == 2 or str(ssfm.get("model", "scalar")).lower() == "manakov" else 1.0

    omega = 2.0 * np.pi * fftfreq(n_samples, dt)
    half_linear = np.exp((-alpha / 2.0 + -1j * beta2 * omega**2 / 2.0 + 1j * beta3 * omega**3 / 6.0) * (dz / 2.0))
    half_linear = half_linear.reshape(1, 1, -1)

    diagnostics = {
        "z_km": [],
        "mean_power_W": [],
        "energy_error_rel": [],
        "nonlinear_phase_mean_rad": [],
        "raman_tilt_dB": [],
    }
    initial_energy = float(np.sum(np.abs(field3) ** 2))
    include_raman = bool(ssfm.get("include_raman", False))
    raman_coeff = float(ssfm.get("raman_tilt_coeff_per_W_per_km_per_THz", 0.0))
    freqs = np.asarray(tx_signal.get("freq_grid", np.arange(n_ch)), dtype=float)
    freq_offsets = freqs - np.mean(freqs)

    for step in range(n_steps):
        field3 = ifft(fft(field3, axis=-1) * half_linear, axis=-1)
        total_power = np.sum(np.abs(field3) ** 2, axis=1, keepdims=True)
        nonlinear_phase = manakov_factor * gamma * total_power * dz
        field3 *= np.exp(1j * nonlinear_phase)

        raman_tilt_dB = 0.0
        if include_raman and raman_coeff != 0.0:
            mean_ch_power = np.mean(total_power[:, 0, :], axis=1)
            weighted_power = float(np.mean(mean_ch_power))
            tilt_db_per_ch = -raman_coeff * weighted_power * (dz / 1_000.0) * freq_offsets
            field3 *= np.power(10.0, (tilt_db_per_ch / 20.0)).reshape(n_ch, 1, 1)
            raman_tilt_dB = float(np.max(tilt_db_per_ch) - np.min(tilt_db_per_ch))

        field3 = ifft(fft(field3, axis=-1) * half_linear, axis=-1)

        if step == 0 or step == n_steps - 1 or (step + 1) % max(1, n_steps // 10) == 0:
            energy = float(np.sum(np.abs(field3) ** 2))
            diagnostics["z_km"].append((step + 1) * dz / 1_000.0)
            diagnostics["mean_power_W"].append(float(np.mean(np.abs(field3) ** 2)))
            diagnostics["energy_error_rel"].append((energy - initial_energy) / max(initial_energy, 1e-300))
            diagnostics["nonlinear_phase_mean_rad"].append(float(np.mean(nonlinear_phase)))
            diagnostics["raman_tilt_dB"].append(raman_tilt_dB)

    ensure_finite("rx field", field3)
    out_field = field3 if was_3d else field3[:, 0, :]
    return {
        "field": out_field,
        "time_step_s": dt,
        "n_channels": n_ch,
        "n_polarizations": n_pol,
        "n_samples": n_samples,
        "freq_grid": tx_signal.get("freq_grid"),
        "distance_km": float(fiber["length_km"]),
        "ssfm_step_m": dz,
        "ssfm_steps": n_steps,
        "diagnostics": {k: np.asarray(v, dtype=float) for k, v in diagnostics.items()},
        "channel_metadata": tx_signal.get("channel_metadata"),
    }


def run_step_size_convergence(tx_signal: dict[str, Any], fiber: dict[str, Any], ssfm: dict[str, Any], step_sizes_m: list[float]) -> dict[str, Any]:
    references = []
    for step in step_sizes_m:
        cfg = dict(ssfm)
        cfg["spatial_step_m"] = float(step)
        references.append(run_ssfm(tx_signal, fiber, cfg)["field"])
    finest = references[-1]
    errors = [float(np.linalg.norm(field - finest) / max(np.linalg.norm(finest), 1e-300)) for field in references]
    return {"step_sizes_m": np.asarray(step_sizes_m, dtype=float), "relative_l2_error": np.asarray(errors, dtype=float)}


def validate_physics(tx_signal: dict[str, Any], fiber: dict[str, Any], ssfm: dict[str, Any]) -> dict[str, Any]:
    linear_fiber = dict(fiber, attenuation_dB_per_km=0.0, alpha_linear_per_m=0.0, gamma_per_W_per_m=0.0)
    linear_ssfm = dict(ssfm, include_raman=False, include_self_steepening=False)
    rx = run_ssfm(tx_signal, linear_fiber, linear_ssfm)
    tx_power = float(np.mean(np.abs(tx_signal["field"]) ** 2))
    rx_power = float(np.mean(np.abs(rx["field"]) ** 2))
    power_error = abs(rx_power - tx_power) / max(tx_power, 1e-300)
    return {"lossless_power_error_rel": power_error, "passed": bool(power_error < 1e-5)}
