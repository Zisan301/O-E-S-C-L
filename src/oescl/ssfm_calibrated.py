from __future__ import annotations

from typing import Dict

import numpy as np


def complex_awgn(shape, variance: float, rng: np.random.Generator) -> np.ndarray:
    sigma = np.sqrt(max(float(variance), 1e-18) / 2.0)
    return sigma * (rng.normal(size=shape) + 1j * rng.normal(size=shape))


def _align_complex_gain(rx: np.ndarray, tx: np.ndarray) -> np.ndarray:
    h = np.vdot(rx, tx) / max(np.vdot(rx, rx), 1e-15)
    return h * rx


def calibrated_ssfm_lite(
    tx_symbols: np.ndarray,
    cfg: Dict,
    band: str,
    spans: int,
    launch_power_dbm: float,
    regime: str,
    rng: np.random.Generator,
    disable_noise: bool = False,
    disable_nonlinearity: bool = False,
    disable_dispersion: bool = False,
) -> tuple[np.ndarray, Dict[str, float]]:
    """Calibrated SSFM-lite symbol-domain propagation with receiver CD compensation.

    The previous calibrated version applied dispersion but did not compensate it
    at the coherent receiver. That made the linear-dispersion-only sanity test
    look impaired. This version stores the accumulated dispersion transfer
    function and applies the inverse transfer at the receiver when
    `receiver_dispersion_compensation` is enabled.
    """
    cal = cfg["day4_calibration"]
    band_cfg = cfg["bands"][band]

    x = np.asarray(tx_symbols, dtype=np.complex128)
    x = x / np.sqrt(max(np.mean(np.abs(x) ** 2), 1e-15))
    y = x.copy()

    steps_per_span = int(cal["ssfm_steps_per_span"])
    total_steps = int(spans) * steps_per_span

    regime_cfg = cal["regimes"][regime]
    ase_mult = float(regime_cfg["ase_multiplier"])
    nl_mult = float(regime_cfg["nonlinear_multiplier"])
    imp_mult = float(regime_cfg["implementation_multiplier"])

    power_rel = 10.0 ** (float(launch_power_dbm) / 10.0)
    dispersion_ps = abs(float(band_cfg["dispersion_ps_nm_km"]))
    attenuation = float(band_cfg["attenuation_db_per_km"])
    noise_figure = float(band_cfg["noise_figure_db"])

    n = len(y)
    freqs = np.fft.fftfreq(n)
    dispersion_strength = (
        float(cal["dispersion_strength_scale"])
        * (dispersion_ps / 16.7)
        * (int(spans) / 6.0)
        / max(steps_per_span, 1)
    )

    # One half-step transfer. Two halves are applied per split-step.
    half_disp = np.exp(-0.5j * dispersion_strength * (2.0 * np.pi * freqs) ** 2)

    nonlinear_strength = (
        float(cal["nonlinear_strength_scale"])
        * power_rel
        * (int(spans) / 6.0)
        * nl_mult
        / max(total_steps, 1)
    )

    ase_var_span = (
        float(cal["ase_noise_base"])
        * ase_mult
        * (noise_figure / 5.0)
        * (attenuation / 0.20)
        * (int(spans) / 6.0)
        / max(int(spans), 1)
        * float(cal.get("receiver_awgn_scale", 1.0))
    )

    phase_noise_std = float(cal["phase_noise_std"]) * np.sqrt(ase_mult)

    # Track accumulated linear dispersion for coherent receiver CD compensation.
    accumulated_dispersion = np.ones_like(freqs, dtype=np.complex128)

    for step in range(total_steps):
        if not disable_dispersion:
            y = np.fft.ifft(np.fft.fft(y) * half_disp)
            accumulated_dispersion *= half_disp

        if not disable_nonlinearity:
            amp_centered = np.abs(y) ** 2 - np.mean(np.abs(y) ** 2)
            y = y * np.exp(1j * nonlinear_strength * amp_centered)

        if not disable_dispersion:
            y = np.fft.ifft(np.fft.fft(y) * half_disp)
            accumulated_dispersion *= half_disp

        if bool(cal.get("normalize_each_span", True)) and ((step + 1) % steps_per_span == 0):
            y = y / np.sqrt(max(np.mean(np.abs(y) ** 2), 1e-15))

        if not disable_noise and ((step + 1) % steps_per_span == 0):
            y = y + complex_awgn(y.shape, ase_var_span, rng)
            if phase_noise_std > 0:
                y = y * np.exp(1j * rng.normal(0.0, phase_noise_std, size=y.shape))

    if bool(cal.get("receiver_dispersion_compensation", True)) and not disable_dispersion:
        # Inverse CD compensation, as a coherent receiver DSP block would do.
        y = np.fft.ifft(np.fft.fft(y) * np.conj(accumulated_dispersion))

    if not disable_noise:
        imp_var = float(cal["implementation_noise_base"]) * imp_mult
        y = y + complex_awgn(y.shape, imp_var, rng)

    y = _align_complex_gain(y, x)

    err = y - x
    noise_var = float(np.mean(np.abs(err) ** 2))
    gsnr_db = float(10.0 * np.log10(float(np.mean(np.abs(x) ** 2)) / max(noise_var, 1e-15)))

    return y, {
        "calibrated_noise_var": noise_var,
        "calibrated_gsnr_db": gsnr_db,
        "regime": regime,
        "spans": int(spans),
        "launch_power_dbm": float(launch_power_dbm),
        "band": band,
        "total_steps": int(total_steps),
        "receiver_dispersion_compensation": bool(cal.get("receiver_dispersion_compensation", True)),
    }
