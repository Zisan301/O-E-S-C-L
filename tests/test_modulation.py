"""
tests/test_modulation.py
========================
Tests for WDM band plan and PCS generation.
"""

import numpy as np

from src.modulation import build_band_plan, generate_pcs_symbols


def _cfg():
    bands = {
        "C": {"channels": 4, "center_nm": 1550.0, "wavelength_min_nm": 1540.0, "wavelength_max_nm": 1560.0, "gain_dB": 20, "noise_figure_dB": 5},
        "L": {"channels": 4, "center_nm": 1590.0, "wavelength_min_nm": 1580.0, "wavelength_max_nm": 1600.0, "gain_dB": 20, "noise_figure_dB": 5},
    }
    aggregate = {"total_channels": 8, "channel_spacing_GHz": 33.0, "per_channel_symbol_rate_Gbaud": 32.0, "total_bandwidth_THz": 0.264}
    return bands, aggregate


def test_band_plan_channel_count_and_spacing():
    bands, aggregate = _cfg()
    plan = build_band_plan(bands, aggregate)
    assert plan["n_channels"] == 8
    c_band = plan["channels"]["C"]
    assert np.allclose(np.diff(c_band), 0.033)


def test_pcs_entropy_target_is_solved():
    bands, aggregate = _cfg()
    plan = build_band_plan(bands, aggregate)
    tx = generate_pcs_symbols(plan, {"entropy_target_bits": 5.5, "symbols_per_run": 256}, {"C_dBm_per_channel": 0, "L_dBm_per_channel": 0}, rng=np.random.default_rng(1))
    assert tx["field"].shape == (8, 256)
    assert abs(tx["entropy_bits"] - 5.5) < 1e-3
    assert tx["bit_labels"].shape == (8, 256, 6)
