from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from oescl.constellation import (  # noqa: E402
    square_16qam_points,
    maxwell_boltzmann_probabilities,
    entropy_bits,
)
from oescl.gmi_exact import (  # noqa: E402
    bit_metric_bmd_awgn_details,
    bit_metric_gmi_awgn,
)


def _balanced_indices(repetitions: int = 512) -> np.ndarray:
    return np.tile(np.arange(16, dtype=int), repetitions)


def test_uniform_16qam_entropy_is_four_bits() -> None:
    priors = np.ones(16, dtype=float) / 16.0
    assert abs(entropy_bits(priors) - 4.0) < 1e-12


def test_mb_shaped_entropy_is_lower_than_uniform() -> None:
    points = square_16qam_points()
    priors = maxwell_boltzmann_probabilities(points, nu=0.36)
    assert entropy_bits(priors) < 4.0


def test_high_snr_uniform_bmd_gmi_approaches_entropy() -> None:
    points = square_16qam_points()
    indices = _balanced_indices()
    rx = points[indices]
    priors = np.ones(16, dtype=float) / 16.0

    details = bit_metric_bmd_awgn_details(indices, rx, noise_var=1e-8, priors=priors)

    assert details["symbol_entropy_bits"] == 4.0
    assert details["bmd_gmi_bits_per_symbol"] > 3.95
    assert details["ngmi"] > 0.98


def test_high_snr_shaped_bmd_gmi_approaches_shaped_entropy() -> None:
    rng = np.random.default_rng(123)
    points = square_16qam_points()
    priors = maxwell_boltzmann_probabilities(points, nu=0.36)
    indices = rng.choice(16, size=12000, p=priors)
    rx = points[indices]

    details = bit_metric_bmd_awgn_details(indices, rx, noise_var=1e-8, priors=priors)

    assert details["symbol_entropy_bits"] < 4.0
    assert details["bmd_gmi_bits_per_symbol"] > details["symbol_entropy_bits"] - 0.05
    assert details["ngmi"] > 0.98


def test_gmi_decreases_as_noise_increases() -> None:
    rng = np.random.default_rng(456)
    points = square_16qam_points()
    priors = np.ones(16, dtype=float) / 16.0
    indices = _balanced_indices()
    tx = points[indices]

    low_noise = tx + (rng.normal(size=tx.size) + 1j * rng.normal(size=tx.size)) * 0.01
    high_noise = tx + (rng.normal(size=tx.size) + 1j * rng.normal(size=tx.size)) * 0.45

    low_gmi, low_ngmi = bit_metric_gmi_awgn(indices, low_noise, noise_var=2e-4, priors=priors)
    high_gmi, high_ngmi = bit_metric_gmi_awgn(indices, high_noise, noise_var=0.405, priors=priors)

    assert low_gmi > high_gmi
    assert low_ngmi > high_ngmi
