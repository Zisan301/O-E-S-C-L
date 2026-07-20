from __future__ import annotations

from typing import Dict

import numpy as np

from .utils import db_to_linear, dbm_to_watts


def _complex_awgn(shape, variance: float, rng: np.random.Generator) -> np.ndarray:
    sigma = np.sqrt(max(float(variance), 1e-18) / 2.0)
    return sigma * (rng.normal(size=shape) + 1j * rng.normal(size=shape))


def ssfm_lite_propagate(
    tx_symbols: np.ndarray,
    launch_power_dbm: float,
    spans: int,
    band_cfg: Dict,
    cfg: Dict,
    rng: np.random.Generator,
) -> tuple[np.ndarray, Dict[str, float]]:
    """Practical SSFM-lite propagation.

    This is not a full production SSFM solver with pulse shaping and WDM coupling.
    It is a split-step-style symbol-domain approximation that applies dispersion
    phase rotation, nonlinear phase accumulation, attenuation/lumped gain, and ASE-like noise.
    It is intended to be a stronger validation model than the original analytical gate.
    """

    day4 = cfg["day4"]
    n = len(tx_symbols)
    steps_per_span = int(day4["ssfm_steps_per_span"])
    dz_km = float(cfg["simulation"]["span_length_km"]) / max(steps_per_span, 1)
    total_steps = int(spans) * steps_per_span

    beta2 = float(day4.get("beta2_ps2_per_km", -21.7))
    gamma = float(day4.get("gamma_w_inv_km", cfg["fiber"]["gamma_w_inv_km"]))
    attenuation_db_per_km = float(band_cfg.get("attenuation_db_per_km", day4["attenuation_db_per_km"]))
    noise_figure_db = float(band_cfg.get("noise_figure_db", day4["noise_figure_db"]))

    p_w = dbm_to_watts(float(launch_power_dbm))
    # Normalize symbol power to launch power.
    x = np.asarray(tx_symbols, dtype=np.complex128)
    x = x / np.sqrt(max(np.mean(np.abs(x) ** 2), 1e-15)) * np.sqrt(p_w / 1e-3)

    # Frequency grid in normalized symbol-rate units.
    freqs = np.fft.fftfreq(n, d=1.0)
    dispersion_strength = abs(beta2) * dz_km * 1.0e-4
    half_disp = np.exp(-0.5j * dispersion_strength * (2.0 * np.pi * freqs) ** 2)

    alpha_step = db_to_linear(-attenuation_db_per_km * dz_km)
    gain_span = db_to_linear(attenuation_db_per_km * float(cfg["simulation"]["span_length_km"]))

    ase_base = 1.5e-5
    ase_per_span = (
        ase_base
        * db_to_linear(noise_figure_db - 5.0)
        * db_to_linear((attenuation_db_per_km - 0.19) * 8.0)
        * float(day4.get("receiver_awgn_scale", 1.0))
    )

    y = x.copy()
    for step in range(total_steps):
        # Half dispersion
        y = np.fft.ifft(np.fft.fft(y) * half_disp)

        # Nonlinear phase
        nonlinear_phase = gamma * dz_km * np.abs(y) ** 2 * 0.08
        y = y * np.exp(1j * nonlinear_phase)

        # Half dispersion
        y = np.fft.ifft(np.fft.fft(y) * half_disp)

        # Distributed attenuation
        y = y * np.sqrt(alpha_step)

        # Lumped gain and ASE at end of each span
        if (step + 1) % steps_per_span == 0:
            y = y * np.sqrt(gain_span)
            y = y + _complex_awgn(y.shape, ase_per_span, rng)

    # Normalize back to unit constellation scale for receiver decisions.
    y = y / np.sqrt(max(np.mean(np.abs(x) ** 2), 1e-15))

    error = y - tx_symbols
    noise_var = float(np.mean(np.abs(error) ** 2))
    signal_power = float(np.mean(np.abs(tx_symbols) ** 2))
    gsnr_db = float(10.0 * np.log10(max(signal_power, 1e-15) / max(noise_var, 1e-15)))

    stats = {
        "ssfm_noise_var": noise_var,
        "ssfm_signal_power": signal_power,
        "ssfm_gsnr_db": gsnr_db,
        "ssfm_steps_total": int(total_steps),
        "launch_power_dbm": float(launch_power_dbm),
        "spans": int(spans),
    }
    return y, stats
