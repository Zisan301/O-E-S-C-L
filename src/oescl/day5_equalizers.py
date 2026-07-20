from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import joblib
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
import warnings

from .utils import ensure_dir


@dataclass
class EqualizerResult:
    corrected_symbols: np.ndarray
    parameter_count: int
    train_time_s: float
    inference_time_s: float
    residual_mse_before: float
    residual_mse_after: float


def linear_equalizer(tx_train: np.ndarray, rx_train: np.ndarray, rx_all: np.ndarray) -> EqualizerResult:
    h = np.vdot(rx_train, tx_train) / max(np.vdot(rx_train, rx_train), 1e-15)
    corrected = h * rx_all
    before = float(np.mean(np.abs(rx_all - tx_train[: len(rx_all)]) ** 2)) if len(tx_train) >= len(rx_all) else float(np.mean(np.abs(rx_all[: len(tx_train)] - tx_train) ** 2))
    return EqualizerResult(corrected, 2, 0.0, 0.0, before, before)


def dbp_like_equalizer(rx_all: np.ndarray, tx_ref: np.ndarray | None = None, strength: float = 0.04) -> EqualizerResult:
    phase = -strength * (np.abs(rx_all) ** 2 - np.mean(np.abs(rx_all) ** 2))
    corrected = rx_all * np.exp(1j * phase)
    before = float(np.mean(np.abs(rx_all - tx_ref) ** 2)) if tx_ref is not None else 0.0
    after = float(np.mean(np.abs(corrected - tx_ref) ** 2)) if tx_ref is not None else before
    return EqualizerResult(corrected, 1, 0.0, 0.0, before, after)


def _single_symbol_features(z: np.ndarray) -> np.ndarray:
    return np.column_stack([z.real, z.imag, np.abs(z), np.abs(z) ** 2])


def polynomial_nlc(tx_train: np.ndarray, rx_train: np.ndarray, rx_all: np.ndarray) -> EqualizerResult:
    import time

    split = len(tx_train)
    x_train = _single_symbol_features(rx_train)
    y_train = np.column_stack([tx_train.real, tx_train.imag])
    x_all = _single_symbol_features(rx_all)

    model = make_pipeline(
        StandardScaler(),
        PolynomialFeatures(degree=3, include_bias=False),
        Ridge(alpha=1e-3),
    )

    t0 = time.perf_counter()
    model.fit(x_train, y_train)
    t1 = time.perf_counter()
    pred = model.predict(x_all)
    corrected = pred[:, 0] + 1j * pred[:, 1]

    before = float(np.mean(np.abs(rx_train - tx_train) ** 2))
    after = float(np.mean(np.abs(corrected[:split] - tx_train) ** 2))
    return EqualizerResult(corrected, 60, t1 - t0, 0.0, before, after)


def memory_features(z: np.ndarray, taps: int) -> np.ndarray:
    taps = int(taps)
    if taps % 2 == 0:
        raise ValueError("memory_taps must be odd")
    half = taps // 2
    padded = np.pad(z, (half, half), mode="edge")
    windows = []
    for shift in range(taps):
        w = padded[shift : shift + len(z)]
        windows.append(w.real)
        windows.append(w.imag)
        windows.append(np.abs(w))
        windows.append(np.abs(w) ** 2)
    return np.column_stack(windows)


def memory_mlp_equalizer(
    tx_symbols: np.ndarray,
    rx_symbols: np.ndarray,
    cfg: Dict,
    model_name: str,
) -> EqualizerResult:
    import time

    day5 = cfg["day5"]
    n = len(rx_symbols)
    split = max(32, int(float(day5["training_fraction"]) * n))

    x_all = memory_features(rx_symbols, int(day5["memory_taps"]))
    y_all = np.column_stack([tx_symbols.real, tx_symbols.imag])

    x_train = x_all[:split]
    y_train = y_all[:split]

    x_scaler = StandardScaler()
    y_scaler = StandardScaler()
    x_train_s = x_scaler.fit_transform(x_train)
    y_train_s = y_scaler.fit_transform(y_train)
    x_all_s = x_scaler.transform(x_all)

    hidden = tuple(int(v) for v in day5["memory_hidden_layers"])
    model = MLPRegressor(
        hidden_layer_sizes=hidden,
        activation="relu",
        solver="adam",
        alpha=float(day5["neural_alpha"]),
        max_iter=int(day5["memory_max_iter"]),
        random_state=int(cfg["simulation"]["seed"]),
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=18,
    )

    t0 = time.perf_counter()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(x_train_s, y_train_s)
    t1 = time.perf_counter()

    t2 = time.perf_counter()
    pred_s = model.predict(x_all_s)
    pred = y_scaler.inverse_transform(pred_s)
    t3 = time.perf_counter()

    corrected = pred[:, 0] + 1j * pred[:, 1]

    count = 0
    for coef in model.coefs_:
        count += int(np.prod(coef.shape))
    for intercept in model.intercepts_:
        count += int(np.prod(intercept.shape))

    before = float(np.mean(np.abs(rx_symbols - tx_symbols) ** 2))
    after = float(np.mean(np.abs(corrected - tx_symbols) ** 2))

    model_dir = ensure_dir(cfg["output"]["models"])
    joblib.dump({"model": model, "x_scaler": x_scaler, "y_scaler": y_scaler}, model_dir / f"{model_name}.joblib")

    return EqualizerResult(corrected, count, t1 - t0, t3 - t2, before, after)
