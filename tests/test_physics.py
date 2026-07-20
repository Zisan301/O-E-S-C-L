"""
tests/test_physics.py
=====================
Unit tests for physical constants and conversions.
"""

import numpy as np

from src.physics import (
    alpha_db_per_km_to_linear_per_m,
    alpha_linear_per_m_to_db_per_km,
    db_to_linear,
    dbm_to_watt,
    frequency_thz_to_wavelength_nm,
    linear_to_db,
    qam_entropy,
    wavelength_nm_to_frequency_thz,
    watt_to_dbm,
)


def test_db_linear_roundtrip():
    values = np.array([-20.0, 0.0, 10.0, 30.0])
    assert np.allclose(linear_to_db(db_to_linear(values)), values)


def test_dbm_watt_roundtrip():
    values = np.array([-10.0, 0.0, 3.0])
    assert np.allclose(watt_to_dbm(dbm_to_watt(values)), values)


def test_wavelength_frequency_roundtrip():
    wavelengths = np.array([1310.0, 1550.0, 1625.0])
    assert np.allclose(frequency_thz_to_wavelength_nm(wavelength_nm_to_frequency_thz(wavelengths)), wavelengths)


def test_alpha_roundtrip():
    alpha_db = 0.18
    assert np.isclose(alpha_linear_per_m_to_db_per_km(alpha_db_per_km_to_linear_per_m(alpha_db)), alpha_db)


def test_qam_entropy_uniform_64qam():
    probs = np.ones(64) / 64
    assert np.isclose(qam_entropy(probs), 6.0)
