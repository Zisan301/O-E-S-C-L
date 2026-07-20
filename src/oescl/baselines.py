from __future__ import annotations

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import make_pipeline


def linear_equalize(tx_train: np.ndarray, rx_train: np.ndarray, rx_all: np.ndarray) -> np.ndarray:
    h = np.vdot(rx_train, tx_train) / max(np.vdot(rx_train, rx_train), 1e-15)
    return h * rx_all


def _to_features(z: np.ndarray) -> np.ndarray:
    return np.column_stack([z.real, z.imag, np.abs(z), np.abs(z) ** 2])


def polynomial_nlc(tx_train: np.ndarray, rx_train: np.ndarray, rx_all: np.ndarray, degree: int = 3) -> np.ndarray:
    x_train = _to_features(rx_train)
    y_train = np.column_stack([tx_train.real, tx_train.imag])
    x_all = _to_features(rx_all)

    model = make_pipeline(
        StandardScaler(),
        PolynomialFeatures(degree=degree, include_bias=False),
        Ridge(alpha=1e-3),
    )
    model.fit(x_train, y_train)
    pred = model.predict(x_all)
    return pred[:, 0] + 1j * pred[:, 1]


def dbp_inspired_compensation(rx_symbols: np.ndarray, strength: float = 0.06) -> np.ndarray:
    # Low-complexity inverse nonlinear phase approximation.
    phase = -strength * (np.abs(rx_symbols) ** 2 - np.mean(np.abs(rx_symbols) ** 2))
    return rx_symbols * np.exp(1j * phase)
