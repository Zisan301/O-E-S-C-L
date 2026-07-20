"""
tests/test_reproducibility.py
=============================
Reproducibility tests for config hashing and deterministic PCS generation.
"""

import numpy as np

from src.artifacts import config_hash
from src.modulation import build_band_plan, generate_pcs_symbols


def test_config_hash_is_stable():
    cfg1 = {"b": 2, "a": 1}
    cfg2 = {"a": 1, "b": 2}
    assert config_hash(cfg1) == config_hash(cfg2)


def test_symbol_generation_is_deterministic_with_same_seed():
    bands = {"C": {"channels": 1, "center_nm": 1550.0, "wavelength_min_nm": 1540.0, "wavelength_max_nm": 1560.0, "gain_dB": 20, "noise_figure_dB": 5}}
    aggregate = {"total_channels": 1, "channel_spacing_GHz": 33.0, "per_channel_symbol_rate_Gbaud": 32.0, "total_bandwidth_THz": 0.033}
    plan = build_band_plan(bands, aggregate)
    tx1 = generate_pcs_symbols(plan, {"seed": 7, "symbols_per_run": 64}, {"C_dBm_per_channel": 0})
    tx2 = generate_pcs_symbols(plan, {"seed": 7, "symbols_per_run": 64}, {"C_dBm_per_channel": 0})
    assert np.array_equal(tx1["symbol_indices"], tx2["symbol_indices"])
