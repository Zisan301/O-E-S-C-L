"""
tests/test_neural_models.py
===========================
Tests that the neural model does not invent synthetic SNR gains.
"""

import numpy as np
import pytest

from src.neural_models import NeuralNLICanceller


def test_untrained_inference_is_rejected_without_explicit_baseline():
    model = NeuralNLICanceller({"save_path": "does/not/exist.pt", "sequence_length": 16})
    model.load_or_init()
    rx = {"field": np.ones((1, 16), dtype=complex), "time_step_s": 1.0, "freq_grid": np.array([193.1])}
    tx = {"field": np.ones((1, 16), dtype=complex), "constellation": np.array([1 + 0j]), "constellation_bits": np.array([[0]], dtype=np.uint8)}
    with pytest.raises(RuntimeError):
        model.infer_from_receiver(rx, tx)


def test_model_has_no_synthetic_uniform_gain_path():
    model = NeuralNLICanceller({"allow_untrained_baseline": True, "sequence_length": 16})
    source = model.infer_from_receiver.__code__.co_names
    assert "uniform" not in source
