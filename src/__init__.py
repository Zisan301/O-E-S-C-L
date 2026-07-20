"""
src package initialization for the O+E+S+C+L simulation pipeline.
"""

from .amplifiers import apply_amplifiers
from .artifacts import load_artifacts, save_results
from .dsp import receiver_dsp
from .fiber_channel import run_ssfm, run_step_size_convergence, validate_physics
from .metrics import compute_metrics
from .modulation import build_band_plan, generate_pcs_symbols
from .monte_carlo import run_monte_carlo
from .neural_models import NeuralNLICanceller, evaluate_neural_nli, train_neural_nli
from .utils import generate_figures, generate_figures_from_artifacts

__all__ = [
    "build_band_plan",
    "generate_pcs_symbols",
    "run_ssfm",
    "run_step_size_convergence",
    "validate_physics",
    "apply_amplifiers",
    "receiver_dsp",
    "NeuralNLICanceller",
    "train_neural_nli",
    "evaluate_neural_nli",
    "compute_metrics",
    "run_monte_carlo",
    "generate_figures",
    "generate_figures_from_artifacts",
    "save_results",
    "load_artifacts",
]
