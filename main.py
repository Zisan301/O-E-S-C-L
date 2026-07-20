"""
main.py
=======
Experiment orchestrator for the O+E+S+C+L optical transmission project.

Modes:
- smoke
- validate-physics
- train-neural
- evaluate
- monte-carlo
- figures
- full
"""

from __future__ import annotations

import argparse
import copy
import logging
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from src import (
    NeuralNLICanceller,
    apply_amplifiers,
    build_band_plan,
    compute_metrics,
    generate_figures,
    generate_figures_from_artifacts,
    generate_pcs_symbols,
    receiver_dsp,
    run_monte_carlo,
    run_ssfm,
    save_results,
    validate_physics,
)
from src.artifacts import save_config_snapshot, save_metrics_json, save_monte_carlo_csv, save_run_manifest
from src.training_data import ChannelSequenceDataset, deterministic_splits, make_supervised_examples, save_dataset
from src.neural_models import evaluate_neural_nli, train_neural_nli


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    validate_config(cfg)
    return cfg


def validate_config(cfg: dict[str, Any]) -> None:
    required = ["metadata", "fiber", "ssfm", "bands", "aggregate", "modulation", "launch_power", "metrics", "output"]
    missing = [key for key in required if key not in cfg]
    if missing:
        raise ValueError(f"Missing config sections: {missing}")
    n_ch = sum(int(b["channels"]) for b in cfg["bands"].values())
    expected = int(cfg["aggregate"].get("total_channels", n_ch))
    if n_ch != expected:
        raise ValueError(f"Band channel count {n_ch} does not match aggregate.total_channels {expected}")
    if cfg["metrics"].get("target_capacity_Tbs") == 485.0 and cfg["metrics"].get("allow_target_capacity_for_validation", False):
        raise ValueError("Do not use target capacity as validation output. It may be stored only as a target.")


def set_seeds(cfg: dict[str, Any], seed: int | None = None) -> np.random.Generator:
    resolved = int(seed if seed is not None else cfg.get("metadata", {}).get("random_seed", 0))
    random.seed(resolved)
    np.random.seed(resolved)
    os.environ["PYTHONHASHSEED"] = str(resolved)
    try:
        import torch

        torch.manual_seed(resolved)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(resolved)
        torch.backends.cudnn.deterministic = bool(cfg.get("reproducibility", {}).get("cuda_deterministic", True))
        torch.backends.cudnn.benchmark = False
    except Exception:
        pass
    return np.random.default_rng(resolved)



def window_supervised_examples(examples: dict[str, np.ndarray], seq_len: int, max_windows: int | None, seed: int) -> dict[str, np.ndarray]:
    """Convert channel-long examples into short time windows for Transformer-safe training.

    The original tensors are shaped as (n_channels, n_symbols, features). A Transformer
    should not be trained on the full symbol stream at once because attention memory grows
    quadratically with sequence length. This function creates many short windows, each with
    one channel id and seq_len symbols.
    """
    x = np.asarray(examples["x_cont"], dtype=np.float32)
    y = np.asarray(examples["y"], dtype=np.float32)
    band_ids = np.asarray(examples["band_ids"], dtype=np.int64)
    if x.ndim != 3 or y.ndim != 3:
        raise ValueError("Expected x_cont and y with shape (channels, symbols, features)")
    n_ch, n_symbols, _ = x.shape
    seq_len = max(8, min(int(seq_len), n_symbols))
    starts = list(range(0, n_symbols - seq_len + 1, seq_len))
    if not starts:
        starts = [0]

    window_index: list[tuple[int, int]] = [(ch, start) for ch in range(n_ch) for start in starts]
    if max_windows is not None and max_windows > 0 and len(window_index) > max_windows:
        rng = np.random.default_rng(seed)
        selected = rng.choice(len(window_index), size=int(max_windows), replace=False)
        window_index = [window_index[int(i)] for i in selected]

    x_windows = np.empty((len(window_index), seq_len, x.shape[-1]), dtype=np.float32)
    y_windows = np.empty((len(window_index), seq_len, y.shape[-1]), dtype=np.float32)
    band_windows = np.empty((len(window_index),), dtype=np.int64)
    for row, (ch, start) in enumerate(window_index):
        end = start + seq_len
        x_windows[row] = x[ch, start:end]
        y_windows[row] = y[ch, start:end]
        band_windows[row] = band_ids[ch]

    return {
        "x_cont": x_windows,
        "band_ids": band_windows,
        "y": y_windows,
        "band_vocab": examples.get("band_vocab", np.array([], dtype=object)),
        "source_window_count": np.array([len(window_index)], dtype=np.int64),
        "sequence_length": np.array([seq_len], dtype=np.int64),
    }


def run_physical_chain(cfg: dict[str, Any], seed: int | None = None, include_neural: bool = True) -> dict[str, Any]:
    rng = set_seeds(cfg, seed)
    band_plan = build_band_plan(cfg["bands"], {**cfg["aggregate"], "channel_spacing_GHz": cfg["metadata"].get("channel_spacing_GHz", cfg["aggregate"].get("channel_spacing_GHz", 33.0))})
    tx = generate_pcs_symbols(band_plan, cfg["modulation"], cfg.get("launch_power"), samples=cfg["modulation"].get("symbols_per_run"), rng=rng)
    rx_raw = run_ssfm(tx, cfg["fiber"], cfg["ssfm"])
    rx_amp = apply_amplifiers(rx_raw, cfg["bands"], rng=rng)
    rx_dsp = receiver_dsp(rx_amp, cfg["dsp"], cfg["fiber"], tx_signal=tx)

    if include_neural:
        model = NeuralNLICanceller(cfg["neural_model"])
        model.load_or_init()
        rx_clean = model.infer_from_receiver(rx_dsp, tx)
    else:
        rx_clean = {
            **rx_dsp,
            "snr_post_nli_dB": rx_dsp["snr_pre_nli_dB"],
            "snr_gain_dB": np.zeros(rx_dsp["n_channels"], dtype=float),
        }
    rx_clean["diagnostics"] = rx_raw.get("diagnostics", {})
    metrics_cfg = {**cfg["metrics"], **cfg.get("metadata", {})}
    metrics = compute_metrics(rx_clean, tx, band_plan, metrics_cfg, aggregate_cfg={**cfg["aggregate"], "coding_overhead": cfg["modulation"].get("coding_overhead", 0.0)})
    return {"band_plan": band_plan, "tx": tx, "rx_raw": rx_raw, "rx_amp": rx_amp, "rx_dsp": rx_dsp, "rx_clean": rx_clean, "metrics": metrics}


def mode_smoke(cfg: dict[str, Any]) -> dict[str, Any]:
    smoke_cfg = copy.deepcopy(cfg)
    smoke_cfg["modulation"]["symbols_per_run"] = int(smoke_cfg.get("smoke", {}).get("symbols_per_run", 512))
    smoke_cfg["ssfm"]["spatial_step_m"] = float(smoke_cfg.get("smoke", {}).get("spatial_step_m", 20_000.0))
    smoke_cfg["neural_model"]["allow_untrained_baseline"] = True
    return run_physical_chain(smoke_cfg, include_neural=True)


def mode_validate_physics(cfg: dict[str, Any]) -> dict[str, Any]:
    rng = set_seeds(cfg)
    band_plan = build_band_plan(cfg["bands"], {**cfg["aggregate"], "channel_spacing_GHz": cfg["metadata"].get("channel_spacing_GHz", cfg["aggregate"].get("channel_spacing_GHz", 33.0))})
    small_mod = dict(cfg["modulation"], symbols_per_run=min(int(cfg["modulation"].get("symbols_per_run", 2048)), 2048))
    tx = generate_pcs_symbols(band_plan, small_mod, cfg.get("launch_power"), samples=small_mod["symbols_per_run"], rng=rng)
    result = validate_physics(tx, cfg["fiber"], cfg["ssfm"])
    if not result["passed"]:
        raise RuntimeError(f"Physics validation failed: {result}")
    return {"physics_validation": result}


def mode_train_neural(cfg: dict[str, Any]) -> dict[str, Any]:
    base = run_physical_chain(cfg, include_neural=False)
    examples = make_supervised_examples(base["rx_dsp"], base["tx"], target="residual")
    seed = int(cfg.get("metadata", {}).get("random_seed", 0))
    seq_len = int(cfg.get("neural_model", {}).get("sequence_length", 256))
    max_windows = int(cfg.get("training", {}).get("max_training_windows", cfg.get("neural_model", {}).get("max_training_windows", 4096)))
    examples = window_supervised_examples(examples, seq_len=seq_len, max_windows=max_windows, seed=seed)
    data_dir = Path(cfg["output"].get("data_dir", "data/generated"))
    save_dataset(
        examples,
        data_dir / "training",
        metadata={
            "config_seed": seed,
            "windowed_training": True,
            "sequence_length": seq_len,
            "max_training_windows": max_windows,
        },
    )
    if ChannelSequenceDataset is None:
        raise RuntimeError("PyTorch dataset support is unavailable")
    from torch.utils.data import DataLoader

    split = deterministic_splits(
        examples["x_cont"].shape[0],
        cfg["training"].get("train_split", 0.8),
        cfg["training"].get("val_split", 0.1),
        seed,
    )
    train_ds = ChannelSequenceDataset(examples, split.train)
    val_ds = ChannelSequenceDataset(examples, split.val)
    train_loader = DataLoader(train_ds, batch_size=int(cfg["neural_model"].get("batch_size", 16)), shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=int(cfg["neural_model"].get("batch_size", 16)), shuffle=False)
    model, training_summary = train_neural_nli(train_loader, val_loader, cfg["neural_model"])
    training_summary["windowed_training"] = True
    training_summary["training_windows"] = int(examples["x_cont"].shape[0])
    training_summary["sequence_length"] = seq_len
    return {"training_summary": training_summary}


def mode_evaluate(cfg: dict[str, Any]) -> dict[str, Any]:
    result = run_physical_chain(cfg, include_neural=True)
    save_outputs(cfg, result)
    validate_result_for_publication(result["metrics"], require_target=False)
    return result


def mode_monte_carlo(cfg: dict[str, Any]) -> dict[str, Any]:
    def once(run_cfg: dict[str, Any], seed: int) -> dict[str, Any]:
        run_cfg["neural_model"].setdefault("allow_untrained_baseline", False)
        return run_physical_chain(run_cfg, seed=seed, include_neural=True)["metrics"]

    mc = run_monte_carlo(cfg, once, n_runs=cfg.get("robustness", {}).get("runs_per_case"))
    data_dir = Path(cfg["output"].get("data_dir", "data/generated"))
    save_monte_carlo_csv(data_dir, mc["runs"])
    return mc


def mode_figures(cfg: dict[str, Any]) -> dict[str, Any]:
    artifact_dir = Path(cfg["output"].get("data_dir", "data/generated"))
    generate_figures_from_artifacts(artifact_dir, Path(cfg["output"].get("figures_final", "figures/final")).parent)
    return {"figures_from_artifacts": str(artifact_dir)}


def mode_full(cfg: dict[str, Any]) -> dict[str, Any]:
    mode_validate_physics(cfg)
    if not Path(cfg["neural_model"].get("save_path", "data/trained_models/nli_canceller.pt")).exists():
        mode_train_neural(cfg)
    result = mode_evaluate(cfg)
    generate_figures(cfg, result["metrics"], result["rx_clean"], result["band_plan"], result["tx"])
    validate_result_for_publication(result["metrics"], require_target=True)
    return result


def validate_result_for_publication(metrics: dict[str, Any], require_target: bool = False) -> None:
    flags = metrics.get("pass_fail_flags", {})
    if flags.get("ber_below_fec_threshold") is False:
        raise RuntimeError("Publication validation failed: BER is above the configured FEC threshold")
    if require_target and flags.get("capacity_meets_target") is False:
        raise RuntimeError("Publication validation failed: measured capacity does not meet target")
    if not flags.get("no_target_forcing_detected", False):
        raise RuntimeError("Publication validation failed: target forcing was detected")


def save_outputs(cfg: dict[str, Any], result: dict[str, Any]) -> None:
    data_dir = Path(cfg["output"].get("data_dir", "data/generated"))
    data_dir.mkdir(parents=True, exist_ok=True)
    save_config_snapshot(data_dir, cfg)
    save_metrics_json(data_dir, result["metrics"])
    save_results(cfg, result["metrics"], result["band_plan"])
    save_run_manifest(data_dir, cfg, extra={"mode_outputs": sorted(result.keys())})


def configure_logging(level: str, log_file: str) -> None:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_file, mode="w", encoding="utf-8")],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="O+E+S+C+L reproducible experiment runner")
    parser.add_argument("--config", default="config/simulation_params.yaml")
    parser.add_argument("--mode", default="full", choices=["smoke", "validate-physics", "train-neural", "evaluate", "monte-carlo", "figures", "full"])
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    configure_logging(args.log_level, cfg["output"].get("log_file", "logs/run.log"))
    start = time.time()
    logging.info("Starting mode=%s", args.mode)
    if args.mode == "smoke":
        result = mode_smoke(cfg)
    elif args.mode == "validate-physics":
        result = mode_validate_physics(cfg)
    elif args.mode == "train-neural":
        result = mode_train_neural(cfg)
    elif args.mode == "evaluate":
        result = mode_evaluate(cfg)
    elif args.mode == "monte-carlo":
        result = mode_monte_carlo(cfg)
    elif args.mode == "figures":
        result = mode_figures(cfg)
    else:
        result = mode_full(cfg)
    logging.info("Completed mode=%s in %.2f s", args.mode, time.time() - start)
    if isinstance(result, dict) and "metrics" in result:
        metrics = result["metrics"]
        logging.info("Measured capacity: %.4f Tb/s", metrics["aggregate_capacity_Tbs"])
        logging.info("Measured SE: %.4f b/s/Hz", metrics["spectral_efficiency_bpsHz"])
        logging.info("Mean pre-FEC BER: %.4e", metrics["ber_pre_fec_mean"])


if __name__ == "__main__":
    main()
