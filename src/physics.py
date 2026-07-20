"""
src/physics.py
===============
Shared physical constants and unit-conversion helpers for the O+E+S+C+L
optical transmission simulation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


C_M_PER_S = 299_792_458.0
H_J_S = 6.626_070_15e-34
KB_J_PER_K = 1.380_649e-23
OSNR_REF_BW_HZ = 12.5e9  # 0.1 nm reference bandwidth near 1550 nm.


@dataclass(frozen=True)
class PhysicalConstants:
    speed_of_light_m_per_s: float = C_M_PER_S
    planck_j_s: float = H_J_S
    boltzmann_j_per_k: float = KB_J_PER_K
    osnr_reference_bandwidth_hz: float = OSNR_REF_BW_HZ


def db_to_linear(value_db: float | np.ndarray) -> float | np.ndarray:
    return np.power(10.0, np.asarray(value_db) / 10.0)


def linear_to_db(value_linear: float | np.ndarray, floor: float = 1e-300) -> float | np.ndarray:
    return 10.0 * np.log10(np.maximum(np.asarray(value_linear), floor))


def dbm_to_watt(value_dbm: float | np.ndarray) -> float | np.ndarray:
    return 1e-3 * db_to_linear(value_dbm)


def watt_to_dbm(value_watt: float | np.ndarray, floor: float = 1e-300) -> float | np.ndarray:
    return 10.0 * np.log10(np.maximum(np.asarray(value_watt), floor) / 1e-3)


def wavelength_nm_to_frequency_thz(wavelength_nm: float | np.ndarray) -> float | np.ndarray:
    wavelength_m = np.asarray(wavelength_nm) * 1e-9
    return C_M_PER_S / wavelength_m / 1e12


def frequency_thz_to_wavelength_nm(frequency_thz: float | np.ndarray) -> float | np.ndarray:
    frequency_hz = np.asarray(frequency_thz) * 1e12
    return C_M_PER_S / frequency_hz * 1e9


def alpha_db_per_km_to_linear_per_m(alpha_db_per_km: float) -> float:
    """Convert power attenuation in dB/km to power attenuation alpha in 1/m."""
    return float(alpha_db_per_km) * np.log(10.0) / 10.0 / 1_000.0


def alpha_linear_per_m_to_db_per_km(alpha_linear_per_m: float) -> float:
    return float(alpha_linear_per_m) * 10.0 / np.log(10.0) * 1_000.0


def osnr_reference_bandwidth_hz(center_wavelength_nm: float | None = None) -> float:
    """Return the conventional 0.1 nm OSNR reference bandwidth.

    If a center wavelength is supplied, calculate the exact optical-frequency
    bandwidth corresponding to 0.1 nm. Otherwise return 12.5 GHz.
    """
    if center_wavelength_nm is None:
        return OSNR_REF_BW_HZ
    lam_m = float(center_wavelength_nm) * 1e-9
    return C_M_PER_S / (lam_m * lam_m) * 0.1e-9


def qam_entropy(probabilities: Iterable[float]) -> float:
    p = np.asarray(list(probabilities), dtype=float)
    p = p[p > 0.0]
    if p.size == 0:
        return 0.0
    p = p / np.sum(p)
    return float(-np.sum(p * np.log2(p)))


def complex_average_power(field: np.ndarray, axis=None) -> np.ndarray:
    return np.mean(np.abs(field) ** 2, axis=axis)


def normalize_complex_power(field: np.ndarray, target_power_w: float = 1.0, axis=-1) -> np.ndarray:
    power = complex_average_power(field, axis=axis)
    scale = np.sqrt(float(target_power_w) / np.maximum(power, 1e-300))
    return field * np.expand_dims(scale, axis=axis) if np.ndim(scale) else field * scale


def confidence_interval_95(values: np.ndarray, axis: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    arr = np.asarray(values, dtype=float)
    mean = np.mean(arr, axis=axis)
    if arr.shape[axis] <= 1:
        zeros = np.zeros_like(mean)
        return mean, zeros, zeros
    std = np.std(arr, axis=axis, ddof=1)
    n = arr.shape[axis]
    half_width = 1.96 * std / np.sqrt(n)
    return mean, mean - half_width, mean + half_width


def ensure_finite(name: str, value: np.ndarray | float) -> None:
    arr = np.asarray(value)
    if not np.all(np.isfinite(arr)):
        raise FloatingPointError(f"{name} contains NaN or Inf values")
