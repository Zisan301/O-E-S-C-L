from __future__ import annotations

from typing import Dict

import numpy as np

from .constellation import entropy_bits, maxwell_boltzmann_probabilities, square_16qam_points


def pcs_summary(cfg: Dict) -> Dict[str, float]:
    points = square_16qam_points()
    nu = float(cfg["pcs"]["shaping_nu"])
    probs = maxwell_boltzmann_probabilities(points, nu=nu)
    entropy = entropy_bits(probs)
    mean_energy = float(np.sum(probs * np.abs(points) ** 2))

    return {
        "nu": nu,
        "entropy_bits_per_symbol": entropy,
        "mean_symbol_energy": mean_energy,
        "max_probability": float(np.max(probs)),
        "min_probability": float(np.min(probs)),
    }
