"""
src/amplifiers.py
=================
Physically consistent per-band optical amplification and ASE noise injection.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .physics import H_J_S, C_M_PER_S, db_to_linear, linear_to_db, osnr_reference_bandwidth_hz


def apply_amplifiers(rx_raw: dict[str, Any], bands: dict[str, dict[str, Any]], rng: np.random.Generator | None = None) -> dict[str, Any]:
    rng = rng or np.random.default_rng()
    field = np.asarray(rx_raw["field"], dtype=np.complex128).copy()
    if field.ndim != 2:
        raise ValueError("apply_amplifiers currently expects field shape (channels, samples)")
    n_ch, n_samples = field.shape
    dt = float(rx_raw["time_step_s"])
    metadata = rx_raw.get("channel_metadata") or _metadata_from_bands(bands)
    if len(metadata) != n_ch:
        raise ValueError(f"channel metadata length {len(metadata)} does not match field channels {n_ch}")

    gain_dB = np.zeros(n_ch, dtype=float)
    nf_dB = np.zeros(n_ch, dtype=float)
    ase_power_W = np.zeros(n_ch, dtype=float)
    osnr_dB = np.zeros(n_ch, dtype=float)
    noise_equiv_bw_hz = float(1.0 / dt)

    for ch, meta in enumerate(metadata):
        band_key = meta["band"]
        band = bands[band_key]
        ripple = float(band.get("gain_ripple_dB", 0.0)) * np.sin(2 * np.pi * ch / max(n_ch, 1))
        gain_dB[ch] = float(band["gain_dB"]) + ripple
        nf_dB[ch] = float(band["noise_figure_dB"])
        gain_linear = float(db_to_linear(gain_dB[ch]))
        nf_linear = float(db_to_linear(nf_dB[ch]))
        n_sp = max(nf_linear * gain_linear / (2.0 * max(gain_linear - 1.0, 1e-300)), 0.5)
        frequency_hz = float(meta.get("frequency_THz", 0.0)) * 1e12
        if frequency_hz <= 0:
            wavelength_m = float(band.get("center_nm", 1550.0)) * 1e-9
            frequency_hz = C_M_PER_S / wavelength_m

        ase_power = 2.0 * n_sp * H_J_S * frequency_hz * max(gain_linear - 1.0, 0.0) * noise_equiv_bw_hz
        ase_power_W[ch] = ase_power
        field[ch, :] *= np.sqrt(gain_linear)
        noise_sigma = np.sqrt(ase_power / 2.0)
        noise = noise_sigma * (rng.standard_normal(n_samples) + 1j * rng.standard_normal(n_samples))
        field[ch, :] += noise

        signal_power = float(np.mean(np.abs(field[ch, :]) ** 2))
        center_nm = float(band.get("center_nm", meta.get("wavelength_nm", 1550.0)))
        ref_bw = osnr_reference_bandwidth_hz(center_nm)
        ase_ref = 2.0 * n_sp * H_J_S * frequency_hz * max(gain_linear - 1.0, 0.0) * ref_bw
        osnr_dB[ch] = float(linear_to_db(signal_power / max(ase_ref, 1e-300)))

    return {
        "field": field,
        "time_step_s": dt,
        "n_channels": n_ch,
        "n_samples": n_samples,
        "freq_grid": rx_raw.get("freq_grid"),
        "channel_metadata": metadata,
        "gain_dB_per_channel": gain_dB,
        "nf_dB_per_channel": nf_dB,
        "ase_noise_power_W": ase_power_W,
        "osnr_dB": osnr_dB,
        "diagnostics": {"noise_equiv_bw_hz": noise_equiv_bw_hz},
    }


def _metadata_from_bands(bands: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    metadata: list[dict[str, Any]] = []
    index = 0
    for band_key, band in bands.items():
        for _ in range(int(band["channels"])):
            metadata.append({
                "index": index,
                "band": band_key,
                "frequency_THz": C_M_PER_S / (float(band.get("center_nm", 1550.0)) * 1e-9) / 1e12,
                "wavelength_nm": float(band.get("center_nm", 1550.0)),
            })
            index += 1
    return metadata
