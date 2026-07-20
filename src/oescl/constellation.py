from __future__ import annotations

import numpy as np


def square_16qam_points() -> np.ndarray:
    levels = np.array([-3.0, -1.0, 1.0, 3.0])
    points = np.array([x + 1j * y for y in levels for x in levels], dtype=np.complex128)
    points /= np.sqrt(np.mean(np.abs(points) ** 2))
    return points


def maxwell_boltzmann_probabilities(points: np.ndarray, nu: float) -> np.ndarray:
    energy = np.abs(points) ** 2
    weights = np.exp(-nu * energy)
    probs = weights / np.sum(weights)
    return probs


def entropy_bits(probs: np.ndarray) -> float:
    probs = np.asarray(probs, dtype=float)
    safe = np.clip(probs, 1e-15, 1.0)
    return float(-np.sum(safe * np.log2(safe)))


def sample_symbols(
    n_symbols: int,
    shaped: bool,
    nu: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    points = square_16qam_points()
    if shaped:
        probs = maxwell_boltzmann_probabilities(points, nu=nu)
    else:
        probs = np.ones(points.shape[0], dtype=float) / points.shape[0]

    indices = rng.choice(points.shape[0], size=n_symbols, p=probs)
    symbols = points[indices]
    return symbols, indices, probs


def decision_indices(received: np.ndarray, points: np.ndarray | None = None) -> np.ndarray:
    if points is None:
        points = square_16qam_points()
    distances = np.abs(received.reshape(-1, 1) - points.reshape(1, -1)) ** 2
    return np.argmin(distances, axis=1)


def indices_to_symbols(indices: np.ndarray, points: np.ndarray | None = None) -> np.ndarray:
    if points is None:
        points = square_16qam_points()
    return points[indices]
