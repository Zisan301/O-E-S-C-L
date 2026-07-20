from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import joblib
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
import warnings

from .utils import ensure_dir


@dataclass
class NeuralNLIResult:
    corrected_symbols: np.ndarray
    model_path: Optional[Path]
    parameter_count: int
    train_time_s: float
    inference_time_s: float
    residual_mse_before: float
    residual_mse_after: float


def _features(rx_symbols: np.ndarray) -> np.ndarray:
    real = rx_symbols.real
    imag = rx_symbols.imag
    amp2 = np.abs(rx_symbols) ** 2
    amp = np.sqrt(amp2)
    return np.column_stack([real, imag, amp, amp2, real * amp2, imag * amp2])


def _target_residual(rx_symbols: np.ndarray, tx_symbols: np.ndarray) -> np.ndarray:
    residual = rx_symbols - tx_symbols
    return np.column_stack([residual.real, residual.imag])


def _parameter_count(model: MLPRegressor) -> int:
    count = 0
    for coef in model.coefs_:
        count += int(np.prod(coef.shape))
    for intercept in model.intercepts_:
        count += int(np.prod(intercept.shape))
    return count


def apply_neural_nli_mitigation(
    tx_symbols: np.ndarray,
    rx_symbols: np.ndarray,
    cfg: Dict,
    mode: str,
    model_name: str,
) -> NeuralNLIResult:
    import time

    if not bool(cfg["neural_nli"]["enabled"]):
        before = float(np.mean(np.abs(rx_symbols - tx_symbols) ** 2))
        return NeuralNLIResult(
            corrected_symbols=rx_symbols,
            model_path=None,
            parameter_count=0,
            train_time_s=0.0,
            inference_time_s=0.0,
            residual_mse_before=before,
            residual_mse_after=before,
        )

    n = len(rx_symbols)
    split = max(10, int(float(cfg["neural_nli"]["training_fraction"]) * n))

    x = _features(rx_symbols)
    y = _target_residual(rx_symbols, tx_symbols)

    x_train, y_train = x[:split], y[:split]
    x_all = x

    x_scaler = StandardScaler()
    y_scaler = StandardScaler()
    x_train_s = x_scaler.fit_transform(x_train)
    y_train_s = y_scaler.fit_transform(y_train)
    x_all_s = x_scaler.transform(x_all)

    hidden = tuple(int(v) for v in cfg["neural_nli"]["hidden_layer_sizes"])
    max_iter = (
        int(cfg["neural_nli"]["max_iter_smoke"])
        if mode == "smoke"
        else int(cfg["neural_nli"]["max_iter_full"])
    )

    model = MLPRegressor(
        hidden_layer_sizes=hidden,
        activation="relu",
        solver="adam",
        alpha=float(cfg["neural_nli"]["alpha"]),
        max_iter=max_iter,
        random_state=int(cfg["neural_nli"]["random_state"]),
        early_stopping=True,
        n_iter_no_change=15,
        validation_fraction=0.15,
    )

    start_train = time.perf_counter()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(x_train_s, y_train_s)
    train_time_s = time.perf_counter() - start_train

    start_infer = time.perf_counter()
    pred_residual_s = model.predict(x_all_s)
    pred_residual = y_scaler.inverse_transform(pred_residual_s)
    inference_time_s = time.perf_counter() - start_infer

    correction = pred_residual[:, 0] + 1j * pred_residual[:, 1]
    corrected = rx_symbols - correction

    before = float(np.mean(np.abs(rx_symbols - tx_symbols) ** 2))
    after = float(np.mean(np.abs(corrected - tx_symbols) ** 2))

    model_dir = ensure_dir(cfg["output"]["models"])
    model_path = model_dir / f"{model_name}.joblib"
    joblib.dump({"model": model, "x_scaler": x_scaler, "y_scaler": y_scaler}, model_path)

    return NeuralNLIResult(
        corrected_symbols=corrected,
        model_path=model_path,
        parameter_count=_parameter_count(model),
        train_time_s=float(train_time_s),
        inference_time_s=float(inference_time_s),
        residual_mse_before=before,
        residual_mse_after=after,
    )
