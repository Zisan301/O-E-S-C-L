"""
tests/test_metrics.py
=====================
Tests that metrics are measured, not target-forced.
"""

import numpy as np

from src.metrics import compute_metrics
from src.modulation import build_band_plan, generate_pcs_symbols


def _tx_rx(noise_scale=0.05):
    bands = {"C": {"channels": 2, "center_nm": 1550.0, "wavelength_min_nm": 1540.0, "wavelength_max_nm": 1560.0, "gain_dB": 20, "noise_figure_dB": 5}}
    aggregate = {"total_channels": 2, "channel_spacing_GHz": 33.0, "per_channel_symbol_rate_Gbaud": 32.0, "total_bandwidth_THz": 0.066}
    plan = build_band_plan(bands, aggregate)
    rng = np.random.default_rng(3)
    tx = generate_pcs_symbols(plan, {"pcs_distribution": "uniform", "symbols_per_run": 512}, {"C_dBm_per_channel": 0}, rng=rng)
    noise = noise_scale * (rng.standard_normal(tx["field"].shape) + 1j * rng.standard_normal(tx["field"].shape))
    rx = {"field": tx["field"] + noise, "constellation": tx["constellation"], "constellation_bits": tx["constellation_bits"]}
    return tx, rx, plan


def test_capacity_not_hardcoded_to_485():
    tx, rx, plan = _tx_rx()
    metrics = compute_metrics(rx, tx, plan, {"target_capacity_Tbs": 485.0, "ber_target_pre_fec": 0.1}, {"polarization_count": 2})
    assert metrics["aggregate_capacity_Tbs"] != 485.0
    assert metrics["pass_fail_flags"]["no_target_forcing_detected"] is True


def test_worse_noise_reduces_capacity():
    tx1, rx1, plan1 = _tx_rx(noise_scale=0.01)
    tx2, rx2, plan2 = _tx_rx(noise_scale=0.5)
    m1 = compute_metrics(rx1, tx1, plan1, {"ber_target_pre_fec": 0.1}, {"polarization_count": 2})
    m2 = compute_metrics(rx2, tx2, plan2, {"ber_target_pre_fec": 0.1}, {"polarization_count": 2})
    assert m1["aggregate_capacity_Tbs"] > m2["aggregate_capacity_Tbs"]
