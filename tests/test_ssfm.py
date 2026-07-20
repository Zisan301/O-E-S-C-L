"""
tests/test_ssfm.py
==================
Validated SSFM tests: lossless power, attenuation, Kerr phase, Raman disabled,
and step-size convergence.
"""

import numpy as np

from src.fiber_channel import run_ssfm, run_step_size_convergence
from src.modulation import build_band_plan, generate_pcs_symbols
from src.physics import alpha_db_per_km_to_linear_per_m


def _single_channel_tx(samples=512):
    bands = {"C": {"channels": 1, "center_nm": 1550.0, "wavelength_min_nm": 1540.0, "wavelength_max_nm": 1560.0, "gain_dB": 20, "noise_figure_dB": 5}}
    aggregate = {"total_channels": 1, "channel_spacing_GHz": 33.0, "per_channel_symbol_rate_Gbaud": 32.0, "total_bandwidth_THz": 0.033}
    plan = build_band_plan(bands, aggregate)
    tx = generate_pcs_symbols(plan, {"pcs_distribution": "uniform", "symbols_per_run": samples}, {"C_dBm_per_channel": 0}, rng=np.random.default_rng(5))
    return tx


def test_lossless_power_conservation():
    tx = _single_channel_tx()
    fiber = {"length_km": 1.0, "alpha_linear_per_m": 0.0, "beta2_s2_per_m": -2.17e-26, "beta3_s3_per_m": 0.0, "gamma_per_W_per_m": 0.0}
    ssfm = {"spatial_step_m": 100.0, "include_raman": False}
    rx = run_ssfm(tx, fiber, ssfm)
    assert np.isclose(np.mean(np.abs(tx["field"]) ** 2), np.mean(np.abs(rx["field"]) ** 2), rtol=1e-5)


def test_attenuation_matches_db_per_km():
    tx = _single_channel_tx()
    alpha_db = 0.2
    length_km = 10.0
    fiber = {"length_km": length_km, "alpha_linear_per_m": alpha_db_per_km_to_linear_per_m(alpha_db), "beta2_s2_per_m": 0.0, "beta3_s3_per_m": 0.0, "gamma_per_W_per_m": 0.0}
    rx = run_ssfm(tx, fiber, {"spatial_step_m": 1000.0, "include_raman": False})
    expected_ratio = 10 ** (-(alpha_db * length_km) / 10.0)
    measured_ratio = np.mean(np.abs(rx["field"]) ** 2) / np.mean(np.abs(tx["field"]) ** 2)
    assert np.isclose(measured_ratio, expected_ratio, rtol=1e-3)


def test_kerr_phase_known_solution():
    tx = _single_channel_tx(samples=256)
    fiber = {"length_km": 1.0, "alpha_linear_per_m": 0.0, "beta2_s2_per_m": 0.0, "beta3_s3_per_m": 0.0, "gamma_per_W_per_m": 1.27e-3}
    rx = run_ssfm(tx, fiber, {"spatial_step_m": 100.0, "include_raman": False})
    expected_phase = fiber["gamma_per_W_per_m"] * np.abs(tx["field"]) ** 2 * fiber["length_km"] * 1000.0
    actual_phase = np.angle(rx["field"] * np.conj(tx["field"]))
    assert np.mean(np.abs(np.cos(expected_phase) - np.cos(actual_phase))) < 1e-3


def test_raman_disabled_has_no_raman_tilt():
    tx = _single_channel_tx()
    fiber = {"length_km": 1.0, "alpha_linear_per_m": 0.0, "beta2_s2_per_m": 0.0, "beta3_s3_per_m": 0.0, "gamma_per_W_per_m": 0.0}
    rx = run_ssfm(tx, fiber, {"spatial_step_m": 100.0, "include_raman": False})
    assert np.allclose(rx["diagnostics"]["raman_tilt_dB"], 0.0)


def test_step_size_convergence():
    tx = _single_channel_tx(samples=128)
    fiber = {"length_km": 1.0, "alpha_linear_per_m": 0.0, "beta2_s2_per_m": -2.17e-26, "beta3_s3_per_m": 0.0, "gamma_per_W_per_m": 1.27e-3}
    ssfm = {"include_raman": False}
    result = run_step_size_convergence(tx, fiber, ssfm, [500.0, 250.0, 125.0])
    assert result["relative_l2_error"][-1] == 0.0
    assert result["relative_l2_error"][0] >= result["relative_l2_error"][1]
