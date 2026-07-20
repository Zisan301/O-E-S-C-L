from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_config(path: str | Path) -> Dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)

    required_sections = [
        "project",
        "simulation",
        "bands",
        "fiber",
        "pcs",
        "neural_nli",
        "validation",
        "output",
    ]
    missing = [section for section in required_sections if section not in cfg]
    if missing:
        raise ValueError(f"Missing required config sections: {missing}")

    return cfg
