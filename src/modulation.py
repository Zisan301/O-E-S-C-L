"""
src/modulation.py
=================
Reproducible WDM grid generation and 64-QAM/PCS symbol generation.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np

from .physics import dbm_to_watt, frequency_thz_to_wavelength_nm, qam_entropy, wavelength_nm_to_frequency_thz


@dataclass(frozen=True)
class ChannelMetadata:
    index: int
    band: str
    frequency_THz: float
    wavelength_nm: float
    launch_power_dBm: float
    symbol_rate_Gbaud: float


def _qam64_constellation() -> tuple[np.ndarray, np.ndarray]:
    levels = np.array([-7, -5, -3, -1, 1, 3, 5, 7], dtype=float)
    i_grid, q_grid = np.meshgrid(levels, levels, indexing="ij")
    constellation = (i_grid + 1j * q_grid).reshape(-1)
    constellation = constellation / np.sqrt(np.mean(np.abs(constellation) ** 2))
    indices = np.arange(64, dtype=np.uint8)
    i_idx = indices // 8
    q_idx = indices % 8
    bit_labels = np.concatenate([_dec_to_gray_bits(i_idx, 3), _dec_to_gray_bits(q_idx, 3)], axis=1)
    return constellation.astype(np.complex128), bit_labels.astype(np.uint8)


def _dec_to_gray_bits(values: np.ndarray, bits: int) -> np.ndarray:
    gray = values ^ (values >> 1)
    out = np.zeros((values.size, bits), dtype=np.uint8)
    for bit in range(bits):
        out[:, bit] = (gray >> (bits - 1 - bit)) & 1
    return out


def _solve_mb_nu(energies: np.ndarray, target_entropy_bits: float, tol: float = 1e-5) -> float:
    max_entropy = np.log2(energies.size)
    if target_entropy_bits >= max_entropy - tol:
        return 0.0
    if target_entropy_bits <= 0.0:
        return 1e6

    lo, hi = 0.0, 1.0
    for _ in range(80):
        probs_hi = np.exp(-hi * energies)
        probs_hi /= np.sum(probs_hi)
        if qam_entropy(probs_hi) <= target_entropy_bits:
            break
        hi *= 2.0
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        probs_mid = np.exp(-mid * energies)
        probs_mid /= np.sum(probs_mid)
        entropy = qam_entropy(probs_mid)
        if abs(entropy - target_entropy_bits) < tol:
            return float(mid)
        if entropy > target_entropy_bits:
            lo = mid
        else:
            hi = mid
    return float(0.5 * (lo + hi))


def build_band_plan(bands_cfg: dict[str, dict[str, Any]], aggregate_cfg: dict[str, Any]) -> dict[str, Any]:
    spacing_ghz = float(aggregate_cfg.get("channel_spacing_GHz", aggregate_cfg.get("spacing_GHz", 33.0)))
    spacing_thz = spacing_ghz / 1_000.0
    symbol_rate = float(aggregate_cfg.get("per_channel_symbol_rate_Gbaud", aggregate_cfg.get("symbol_rate_Gbaud", 32.0)))
    channels: dict[str, np.ndarray] = {}
    metadata: list[dict[str, Any]] = []
    all_freqs: list[float] = []

    index = 0
    for band_key, band in bands_cfg.items():
        n_ch = int(band["channels"])
        center_nm = float(band.get("center_nm", 0.5 * (float(band["wavelength_min_nm"]) + float(band["wavelength_max_nm"]))))
        center_thz = float(wavelength_nm_to_frequency_thz(center_nm))
        offsets = (np.arange(n_ch, dtype=float) - (n_ch - 1) / 2.0) * spacing_thz
        freqs = center_thz + offsets
        wavelengths = frequency_thz_to_wavelength_nm(freqs)

        wl_min = float(band.get("wavelength_min_nm", np.min(wavelengths)))
        wl_max = float(band.get("wavelength_max_nm", np.max(wavelengths)))
        inside = (wavelengths >= min(wl_min, wl_max) - 1e-9) & (wavelengths <= max(wl_min, wl_max) + 1e-9)
        if not np.all(inside):
            raise ValueError(f"Band {band_key} grid exceeds wavelength limits; reduce channels or spacing")

        channels[band_key] = freqs.astype(float)
        launch_power = float(band.get("launch_power_dBm", aggregate_cfg.get("default_launch_power_dBm", 0.0)))
        for f_thz, wl_nm in zip(freqs, wavelengths):
            meta = ChannelMetadata(
                index=index,
                band=band_key,
                frequency_THz=float(f_thz),
                wavelength_nm=float(wl_nm),
                launch_power_dBm=launch_power,
                symbol_rate_Gbaud=symbol_rate,
            )
            metadata.append(asdict(meta))
            all_freqs.append(float(f_thz))
            index += 1

    total_channels = sum(len(v) for v in channels.values())
    expected_channels = int(aggregate_cfg.get("total_channels", total_channels))
    if total_channels != expected_channels:
        raise ValueError(f"Channel count mismatch: generated {total_channels}, expected {expected_channels}")

    occupied_bandwidth_THz = total_channels * spacing_thz
    expected_bw = float(aggregate_cfg.get("total_bandwidth_THz", occupied_bandwidth_THz))
    tolerance = float(aggregate_cfg.get("bandwidth_tolerance_THz", max(1.0, 0.03 * expected_bw)))
    if abs(occupied_bandwidth_THz - expected_bw) > tolerance:
        raise ValueError(
            f"Occupied bandwidth {occupied_bandwidth_THz:.3f} THz differs from configured {expected_bw:.3f} THz"
        )

    return {
        "channels": channels,
        "all_freqs": np.asarray(all_freqs, dtype=float),
        "n_channels": total_channels,
        "channel_spacing_GHz": spacing_ghz,
        "symbol_rate_Gbaud": symbol_rate,
        "total_occupied_bandwidth_THz": occupied_bandwidth_THz,
        "channel_metadata": metadata,
    }


def generate_pcs_symbols(
    band_plan: dict[str, Any],
    modulation: dict[str, Any],
    launch_power: dict[str, float] | None = None,
    samples: int | None = None,
    rng: np.random.Generator | None = None,
) -> dict[str, Any]:
    rng = rng or np.random.default_rng(int(modulation.get("seed", 0)))
    n_ch = int(band_plan["n_channels"])
    n_samples = int(samples or modulation.get("symbols_per_run", 8192))
    symbol_rate = float(band_plan.get("symbol_rate_Gbaud", modulation.get("symbol_rate_Gbaud", 32.0)))
    dt = 1.0 / (symbol_rate * 1e9)

    constellation, bit_table = _qam64_constellation()
    energies = np.abs(constellation) ** 2
    mode = str(modulation.get("pcs_distribution", "maxwell-boltzmann")).lower()
    learning_mode = str(modulation.get("pcs_learning_method", "mb")).lower()

    if mode in {"uniform", "none"} or learning_mode == "none":
        probabilities = np.full(constellation.size, 1.0 / constellation.size)
        nu = 0.0
    else:
        target_entropy = float(modulation.get("entropy_target_bits", np.log2(constellation.size)))
        nu = _solve_mb_nu(energies, target_entropy)
        probabilities = np.exp(-nu * energies)
        probabilities /= np.sum(probabilities)

    entropy_bits = qam_entropy(probabilities)
    symbol_indices = rng.choice(constellation.size, size=(n_ch, n_samples), p=probabilities).astype(np.uint8)
    bit_labels = bit_table[symbol_indices]
    field = constellation[symbol_indices].astype(np.complex128)

    metadata = band_plan.get("channel_metadata", [])
    for ch in range(n_ch):
        band = metadata[ch]["band"] if metadata else None
        if launch_power and band is not None:
            p_dbm = float(launch_power.get(f"{band}_dBm_per_channel", metadata[ch].get("launch_power_dBm", 0.0)))
        else:
            p_dbm = float(metadata[ch].get("launch_power_dBm", 0.0)) if metadata else 0.0
        field[ch, :] *= np.sqrt(float(dbm_to_watt(p_dbm)))
        if metadata:
            metadata[ch]["launch_power_dBm"] = p_dbm

    return {
        "field": field,
        "time_step_s": dt,
        "n_channels": n_ch,
        "n_samples": n_samples,
        "freq_grid": np.asarray(band_plan["all_freqs"], dtype=float),
        "constellation": constellation,
        "constellation_bits": bit_table,
        "symbol_indices": symbol_indices,
        "bit_labels": bit_labels,
        "probabilities": probabilities,
        "entropy_bits": float(entropy_bits),
        "mb_nu": float(nu),
        "average_symbol_energy": float(np.sum(probabilities * energies)),
        "channel_metadata": metadata,
    }


def qam_symbols_to_indices(symbols: np.ndarray, constellation: np.ndarray) -> np.ndarray:
    flat = np.asarray(symbols).reshape(-1)
    distances = np.abs(flat[:, None] - constellation[None, :])
    return np.argmin(distances, axis=1).reshape(np.asarray(symbols).shape).astype(np.uint8)


def qam_symbols_to_bits(symbols: np.ndarray, constellation: np.ndarray, bit_table: np.ndarray) -> np.ndarray:
    return bit_table[qam_symbols_to_indices(symbols, constellation)]
