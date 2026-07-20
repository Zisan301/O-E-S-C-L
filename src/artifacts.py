"""
src/artifacts.py
================
Run artifact persistence and provenance utilities.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import numpy as np


def config_hash(cfg: dict[str, Any]) -> str:
    raw = json.dumps(cfg, sort_keys=True, default=_json_default).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_commit_sha() -> str | None:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return None


def save_run_manifest(run_dir: str | Path, cfg: dict[str, Any], extra: dict[str, Any] | None = None) -> Path:
    out = Path(run_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "config_hash": config_hash(cfg),
        "git_commit_sha": git_commit_sha(),
        "seed": cfg.get("metadata", {}).get("random_seed", cfg.get("seed")),
        "artifact_files": sorted([str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()]),
    }
    if extra:
        manifest.update(extra)
    path = out / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, default=_json_default), encoding="utf-8")
    return path


def save_config_snapshot(run_dir: str | Path, cfg: dict[str, Any]) -> Path:
    out = Path(run_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "config_snapshot.json"
    path.write_text(json.dumps(cfg, indent=2, default=_json_default), encoding="utf-8")
    return path


def save_metrics_json(run_dir: str | Path, metrics: dict[str, Any]) -> Path:
    out = Path(run_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "metrics.json"
    path.write_text(json.dumps(metrics, indent=2, default=_json_default), encoding="utf-8")
    return path


def save_per_channel_metrics_csv(run_dir: str | Path, metrics: dict[str, Any], band_plan: dict[str, Any]) -> Path:
    out = Path(run_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "per_channel.csv"
    metadata = band_plan.get("channel_metadata", [])
    n = len(metrics["gmi_per_channel"])
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["index", "band", "frequency_THz", "wavelength_nm", "gmi", "snr_dB", "ber_pre_fec", "q_factor_dB"])
        writer.writeheader()
        for i in range(n):
            meta = metadata[i] if i < len(metadata) else {}
            writer.writerow({
                "index": i,
                "band": meta.get("band", ""),
                "frequency_THz": meta.get("frequency_THz", ""),
                "wavelength_nm": meta.get("wavelength_nm", ""),
                "gmi": float(metrics["gmi_per_channel"][i]),
                "snr_dB": float(metrics["snr_per_channel_dB"][i]),
                "ber_pre_fec": float(metrics["ber_pre_fec"][i]),
                "q_factor_dB": float(metrics["q_factor_dB"][i]),
            })
    return path


def save_monte_carlo_csv(run_dir: str | Path, rows: list[dict[str, Any]]) -> Path:
    out = Path(run_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "monte_carlo.csv"
    fieldnames = sorted(set().union(*(row.keys() for row in rows))) if rows else ["run"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def load_metrics(run_dir: str | Path) -> dict[str, Any]:
    return json.loads((Path(run_dir) / "metrics.json").read_text(encoding="utf-8"))


def load_per_channel_data(run_dir: str | Path) -> list[dict[str, str]]:
    path = Path(run_dir) / "per_channel.csv"
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_run_manifest(run_dir: str | Path) -> dict[str, Any]:
    return json.loads((Path(run_dir) / "manifest.json").read_text(encoding="utf-8"))


def load_artifacts(run_dir: str | Path) -> dict[str, Any]:
    return {
        "manifest": load_run_manifest(run_dir),
        "metrics": load_metrics(run_dir),
        "per_channel": load_per_channel_data(run_dir),
    }


def save_results(cfg: dict[str, Any], metrics: dict[str, Any], band_plan: dict[str, Any]) -> None:
    run_dir = Path(cfg.get("output", {}).get("data_dir", "data/generated"))
    save_config_snapshot(run_dir, cfg)
    save_metrics_json(run_dir, metrics)
    save_per_channel_metrics_csv(run_dir, metrics, band_plan)
    save_run_manifest(run_dir, cfg)


def _json_default(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
