"""
tests/test_dsp.py
=================
Tests for measured receiver DSP diagnostics.
"""

import numpy as np

from src.dsp import receiver_dsp
from src.modulation import build_band_plan, generate_pcs_symbols


def test_dsp_measures_snr_from_reference():
    bands = {"C": {"channels": 1, "center_nm": 1550.0, "wavelength_min_nm": 1540.0, "wavelength_max_nm": 1560.0, "gain_dB": 20, "noise_figure_dB": 5}}
    aggregate = {"total_channels": 1, "channel_spacing_GHz": 33.0, "per_channel_symbol_rate_Gbaud": 32.0, "total_bandwidth_THz": 0.033}
    plan = build_band_plan(bands, aggregate)
    rng = np.random.default_rng(4)
    tx = generate_pcs_symbols(plan, {"pcs_distribution": "uniform", "symbols_per_run": 256}, {"C_dBm_per_channel": 0}, rng=rng)
    noise = 0.0001 * (rng.standard_normal(tx["field"].shape) + 1j * rng.standard_normal(tx["field"].shape))
    rx_amp = {"field": tx["field"] + noise, "time_step_s": tx["time_step_s"], "freq_grid": tx["freq_grid"], "channel_metadata": tx["channel_metadata"], "constellation": tx["constellation"], "constellation_bits": tx["constellation_bits"]}
    out = receiver_dsp(rx_amp, {"cd_compensation": "none"}, {"length_km": 0.0}, tx_signal=tx)
    assert np.isfinite(out["snr_pre_nli_dB"]).all()
    assert out["snr_pre_nli_dB"][0] > 10
