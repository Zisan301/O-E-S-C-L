from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np


@dataclass
class WaveformResult:
    rx_symbols: np.ndarray
    tx_symbols_aligned: np.ndarray
    tx_indices_aligned: np.ndarray
    priors: np.ndarray
    stats: Dict[str, float]


def rrc_filter(beta: float, sps: int, span_symbols: int) -> np.ndarray:
    n = int(span_symbols) * int(sps)
    t = np.arange(-n / 2, n / 2 + 1, dtype=float) / float(sps)
    h = np.zeros_like(t)

    for i, ti in enumerate(t):
        if abs(ti) < 1e-12:
            h[i] = 1.0 + beta * (4.0 / np.pi - 1.0)
        elif beta > 0 and abs(abs(ti) - 1.0 / (4.0 * beta)) < 1e-10:
            h[i] = (
                beta
                / np.sqrt(2.0)
                * (
                    (1.0 + 2.0 / np.pi) * np.sin(np.pi / (4.0 * beta))
                    + (1.0 - 2.0 / np.pi) * np.cos(np.pi / (4.0 * beta))
                )
            )
        else:
            numerator = (
                np.sin(np.pi * ti * (1.0 - beta))
                + 4.0 * beta * ti * np.cos(np.pi * ti * (1.0 + beta))
            )
            denominator = np.pi * ti * (1.0 - (4.0 * beta * ti) ** 2)
            h[i] = numerator / denominator

    h = h / np.sqrt(max(np.sum(h ** 2), 1e-15))
    return h.astype(float)


def pulse_shape(symbols: np.ndarray, h: np.ndarray, sps: int) -> np.ndarray:
    up = np.zeros(len(symbols) * int(sps), dtype=np.complex128)
    up[:: int(sps)] = symbols
    return np.convolve(up, h, mode="full")


def matched_filter_and_downsample(waveform: np.ndarray, h: np.ndarray, sps: int, n_symbols: int) -> np.ndarray:
    mf = np.convolve(waveform, h[::-1].conj(), mode="full")
    delay = len(h) - 1
    symbols = mf[delay:: int(sps)]
    return symbols[:n_symbols]


def _complex_awgn(shape, variance: float, rng: np.random.Generator) -> np.ndarray:
    sigma = np.sqrt(max(float(variance), 1e-18) / 2.0)
    return sigma * (rng.normal(size=shape) + 1j * rng.normal(size=shape))


def _align_gain(rx: np.ndarray, tx: np.ndarray) -> np.ndarray:
    h = np.vdot(rx, tx) / max(np.vdot(rx, rx), 1e-15)
    return h * rx


def waveform_ssfm_channel(
    tx_symbols: np.ndarray,
    tx_indices: np.ndarray,
    priors: np.ndarray,
    cfg: Dict,
    band: str,
    spans: int,
    launch_power_dbm: float,
    stress: Dict,
    rng: np.random.Generator,
    disable_noise: bool = False,
    disable_nonlinearity: bool = False,
    disable_dispersion: bool = False,
) -> WaveformResult:
    day5 = cfg["day5"]
    sps = int(day5["samples_per_symbol"])
    h = rrc_filter(float(day5["rrc_rolloff"]), sps, int(day5["rrc_span_symbols"]))

    x = np.asarray(tx_symbols, dtype=np.complex128)
    x = x / np.sqrt(max(np.mean(np.abs(x) ** 2), 1e-15))

    waveform = pulse_shape(x, h, sps)
    waveform = waveform / np.sqrt(max(np.mean(np.abs(waveform) ** 2), 1e-15))

    n = len(waveform)
    freqs = np.fft.fftfreq(n, d=1.0 / sps)

    steps_per_span = int(day5["ssfm_steps_per_span"])
    total_steps = int(spans) * steps_per_span
    band_cfg = cfg["bands"][band]

    dispersion = (
        float(day5["dispersion_scale"])
        * abs(float(band_cfg["dispersion_ps_nm_km"])) / 16.7
        * (int(spans) / 6.0)
        / max(steps_per_span, 1)
    )
    half_disp = np.exp(-0.5j * dispersion * (2.0 * np.pi * freqs / max(sps, 1)) ** 2)

    power_rel = 10.0 ** (float(launch_power_dbm) / 10.0)
    nonlinear_strength = (
        float(day5["nonlinear_scale"])
        * power_rel
        * float(stress["nonlinear"])
        * (int(spans) / 6.0)
        / max(total_steps, 1)
    )

    attenuation_factor = 1.0
    accumulated_dispersion = np.ones_like(freqs, dtype=np.complex128)
    y = waveform.copy()

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

        if bool(day5["normalize_per_span"]) and ((step + 1) % steps_per_span == 0):
            y = y / np.sqrt(max(np.mean(np.abs(y) ** 2), 1e-15))

        if not disable_noise and ((step + 1) % steps_per_span == 0):
            # ASE-like noise, scaled by band noise figure and stress.
            nf_scale = float(band_cfg["noise_figure_db"]) / 5.0
            loss_scale = float(band_cfg["attenuation_db_per_km"]) / 0.20
            noise_var = float(stress["noise"]) * nf_scale * loss_scale / max(int(spans), 1)
            y = y + _complex_awgn(y.shape, noise_var, rng)

            phase_std = float(stress.get("phase", 0.0))
            if phase_std > 0:
                y = y * np.exp(1j * rng.normal(0.0, phase_std, size=y.shape))

    if bool(day5["receiver_cd_compensation"]) and not disable_dispersion:
        y = np.fft.ifft(np.fft.fft(y) * np.conj(accumulated_dispersion))

    if not disable_noise:
        y = y + _complex_awgn(y.shape, float(stress["implementation"]), rng)

    rx = matched_filter_and_downsample(y, h, sps, len(x))
    rx = _align_gain(rx, x)

    stats = {
        "waveform_samples": int(n),
        "sps": int(sps),
        "spans": int(spans),
        "launch_power_dbm": float(launch_power_dbm),
        "band": band,
        "stress_name": str(stress["name"]),
        "stress_noise": float(stress["noise"]),
        "stress_nonlinear": float(stress["nonlinear"]),
        "stress_implementation": float(stress["implementation"]),
        "total_steps": int(total_steps),
        "receiver_cd_compensation": bool(day5["receiver_cd_compensation"]),
    }

    return WaveformResult(
        rx_symbols=rx,
        tx_symbols_aligned=x[: len(rx)],
        tx_indices_aligned=np.asarray(tx_indices)[: len(rx)],
        priors=priors,
        stats=stats,
    )
