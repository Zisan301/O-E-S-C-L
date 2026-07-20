from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from .utils import db_to_linear, linear_to_db, dbm_to_watts


@dataclass(frozen=True)
class ChannelSpec:
    band: str
    channel_id: int
    frequency_offset_ghz: float
    wavelength_nm: float
    launch_power_dbm: float


def make_channel_plan(cfg: Dict, mode: str) -> List[ChannelSpec]:
    sim = cfg["simulation"]
    bands = cfg["bands"]
    n_channels = (
        int(sim["n_channels_per_band_smoke"])
        if mode == "smoke"
        else int(sim["n_channels_per_band_full"])
    )
    spacing = float(sim["channel_spacing_ghz"])
    launch_power_dbm = float(sim["default_launch_power_dbm"])

    plan: List[ChannelSpec] = []
    for band_name, band_cfg in bands.items():
        center_nm = float(band_cfg["center_nm"])
        offsets = (np.arange(n_channels) - (n_channels - 1) / 2.0) * spacing
        for idx, offset in enumerate(offsets):
            wavelength_nm = center_nm - offset * 0.008
            plan.append(
                ChannelSpec(
                    band=band_name,
                    channel_id=idx,
                    frequency_offset_ghz=float(offset),
                    wavelength_nm=float(wavelength_nm),
                    launch_power_dbm=launch_power_dbm,
                )
            )
    return plan


def estimate_noise_variances(
    channel: ChannelSpec,
    cfg: Dict,
    shaped: bool,
    neural_mitigation: bool,
) -> Dict[str, float]:
    band_cfg = cfg["bands"][channel.band]
    fiber = cfg["fiber"]
    sim = cfg["simulation"]

    spans = int(sim["spans"])
    span_length_km = float(sim["span_length_km"])
    total_length_km = spans * span_length_km

    p_w = dbm_to_watts(channel.launch_power_dbm)

    attenuation = float(band_cfg["attenuation_db_per_km"])
    noise_figure_db = float(band_cfg["noise_figure_db"])
    dispersion = abs(float(band_cfg["dispersion_ps_nm_km"]))

    ase_base = 8.0e-5
    ase_var = (
        ase_base
        * spans
        * db_to_linear(noise_figure_db - 5.0)
        * db_to_linear((attenuation - 0.19) * span_length_km / 10.0)
    )

    eta_base = float(fiber["nonlinear_eta_base"])
    gamma = float(fiber["gamma_w_inv_km"])
    dispersion_factor = 1.0 / (1.0 + dispersion / 16.0)
    band_edge_factor = 1.0 + abs(channel.frequency_offset_ghz) / 1200.0

    nli_var = (
        eta_base
        * (gamma / 1.25)
        * (total_length_km / 480.0)
        * (p_w / 1e-3) ** 2
        * dispersion_factor
        * band_edge_factor
    )

    if shaped:
        # PCS reduces effective high-energy symbol probability in this simplified model.
        nli_var *= 0.88

    if neural_mitigation:
        # The model is trained later. This is only a conservative expected residual target.
        nli_var *= 0.72

    margin = db_to_linear(float(fiber["implementation_margin_db"]) / 10.0)
    implementation_var = 1.8e-3 * margin

    total_var = ase_var + nli_var + implementation_var
    gsnr_linear = 1.0 / max(total_var, 1e-12)

    return {
        "ase_var": float(ase_var),
        "nli_var": float(nli_var),
        "implementation_var": float(implementation_var),
        "total_noise_var": float(total_var),
        "gsnr_db": float(linear_to_db(gsnr_linear)),
    }


def apply_optical_channel(
    tx_symbols: np.ndarray,
    noise_stats: Dict[str, float],
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    total_var = float(noise_stats["total_noise_var"])
    nli_var = float(noise_stats["nli_var"])

    nonlinear_phase = 0.045 * nli_var / max(total_var, 1e-12)
    nonlinear_distortion = (
        nonlinear_phase * (np.abs(tx_symbols) ** 2 - np.mean(np.abs(tx_symbols) ** 2)) * tx_symbols
    )

    sigma = np.sqrt(max(total_var - nli_var * 0.35, 1e-12) / 2.0)
    awgn = sigma * (rng.normal(size=tx_symbols.shape) + 1j * rng.normal(size=tx_symbols.shape))

    residual = nonlinear_distortion + awgn
    rx_symbols = tx_symbols + residual
    return rx_symbols, residual
