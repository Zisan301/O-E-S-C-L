"""
src/monte_carlo.py
==================
Monte Carlo experiment runner and confidence interval summaries.
"""

from __future__ import annotations

import copy
from typing import Any, Callable

import numpy as np

from .physics import confidence_interval_95


MetricFunction = Callable[[dict[str, Any], int], dict[str, Any]]


def run_monte_carlo(base_cfg: dict[str, Any], run_once: MetricFunction, n_runs: int | None = None) -> dict[str, Any]:
    n = int(n_runs or base_cfg.get("metadata", {}).get("monte_carlo_runs", 10))
    seed0 = int(base_cfg.get("metadata", {}).get("random_seed", base_cfg.get("seed", 0)))
    rows: list[dict[str, Any]] = []
    metrics_runs: list[dict[str, Any]] = []
    for run in range(n):
        cfg = copy.deepcopy(base_cfg)
        seed = seed0 + run
        cfg.setdefault("metadata", {})["random_seed"] = seed
        _apply_perturbations(cfg, seed)
        metrics = run_once(cfg, seed)
        metrics_runs.append(metrics)
        rows.append({
            "run": run,
            "seed": seed,
            "aggregate_capacity_Tbs": float(metrics.get("aggregate_capacity_Tbs", np.nan)),
            "spectral_efficiency_bpsHz": float(metrics.get("spectral_efficiency_bpsHz", np.nan)),
            "gmi_mean": float(metrics.get("gmi_mean", np.nan)),
            "snr_mean_dB": float(metrics.get("snr_mean_dB", np.nan)),
            "ber_pre_fec_mean": float(metrics.get("ber_pre_fec_mean", np.nan)),
        })
    return {"runs": rows, "summary": _summarize_rows(rows), "raw_metrics": metrics_runs}


def _apply_perturbations(cfg: dict[str, Any], seed: int) -> None:
    rng = np.random.default_rng(seed)
    robustness = cfg.get("robustness", {})
    loss_range = robustness.get("fiber_loss_variation_dB_per_km")
    if loss_range and "fiber" in cfg:
        cfg["fiber"]["attenuation_dB_per_km"] = float(cfg["fiber"].get("attenuation_dB_per_km", 0.18)) + rng.uniform(float(loss_range[0]), float(loss_range[1]))
    nf_range = robustness.get("amplifier_NF_variation_dB")
    if nf_range and "bands" in cfg:
        for band in cfg["bands"].values():
            band["noise_figure_dB"] = float(band.get("noise_figure_dB", 5.0)) + rng.uniform(float(nf_range[0]), float(nf_range[1]))
    power_range = robustness.get("launch_power_variation_dB")
    if power_range and "launch_power" in cfg:
        for key in cfg["launch_power"]:
            cfg["launch_power"][key] = float(cfg["launch_power"][key]) + rng.uniform(float(power_range[0]), float(power_range[1]))


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    keys = [key for key in rows[0] if key not in {"run", "seed"}]
    summary = {}
    for key in keys:
        values = np.asarray([row[key] for row in rows], dtype=float)
        mean, lo, hi = confidence_interval_95(values, axis=0)
        summary[key] = {"mean": float(mean), "ci95_low": float(lo), "ci95_high": float(hi), "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0}
    return summary
