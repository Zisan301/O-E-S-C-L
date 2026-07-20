from __future__ import annotations

import random
from pathlib import Path

import numpy as np


def set_global_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def db_to_linear(value_db: float) -> float:
    return 10.0 ** (value_db / 10.0)


def linear_to_db(value: float, floor: float = 1e-30) -> float:
    return 10.0 * np.log10(max(float(value), floor))


def dbm_to_watts(value_dbm: float) -> float:
    return 1e-3 * 10.0 ** (value_dbm / 10.0)


def watts_to_dbm(value_w: float, floor: float = 1e-18) -> float:
    return 10.0 * np.log10(max(float(value_w), floor) / 1e-3)
