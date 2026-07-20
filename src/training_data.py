"""
src/training_data.py
====================
Dataset creation and persistence utilities for supervised neural NLI learning.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class DatasetSplit:
    train: np.ndarray
    val: np.ndarray
    test: np.ndarray


def make_supervised_examples(rx_dsp: dict[str, Any], tx_signal: dict[str, Any], target: str = "residual") -> dict[str, np.ndarray]:
    rx = np.asarray(rx_dsp["field"], dtype=np.complex128)
    tx = np.asarray(tx_signal["field"], dtype=np.complex128)[:, : rx.shape[1]]
    n_ch, n_samples = rx.shape
    metadata = rx_dsp.get("channel_metadata") or tx_signal.get("channel_metadata") or []

    freq = np.asarray(rx_dsp.get("freq_grid", np.arange(n_ch)), dtype=float)
    freq_norm = (freq - np.mean(freq)) / max(np.std(freq), 1e-12)
    powers = np.array([float(m.get("launch_power_dBm", 0.0)) for m in metadata], dtype=float) if metadata else np.zeros(n_ch)
    power_norm = (powers - np.mean(powers)) / max(np.std(powers), 1e-12) if powers.size else np.zeros(n_ch)
    bands = [m.get("band", "UNK") for m in metadata] if metadata else ["UNK"] * n_ch
    band_vocab = {band: i for i, band in enumerate(sorted(set(bands)))}
    band_ids = np.array([band_vocab[b] for b in bands], dtype=np.int64)
    osnr = np.asarray(rx_dsp.get("osnr_dB", np.zeros(n_ch)), dtype=float)
    osnr_norm = (osnr - np.nanmean(osnr)) / max(np.nanstd(osnr), 1e-12) if osnr.size else np.zeros(n_ch)

    x_cont = np.zeros((n_ch, n_samples, 5), dtype=np.float32)
    x_cont[..., 0] = rx.real
    x_cont[..., 1] = rx.imag
    x_cont[..., 2] = freq_norm[:, None]
    x_cont[..., 3] = power_norm[:, None]
    x_cont[..., 4] = osnr_norm[:, None]

    if target == "clean_symbol":
        y_complex = tx
    elif target == "residual":
        y_complex = rx - tx
    else:
        raise ValueError("target must be 'residual' or 'clean_symbol'")
    y = np.stack([y_complex.real, y_complex.imag], axis=-1).astype(np.float32)
    return {"x_cont": x_cont, "band_ids": band_ids, "y": y, "band_vocab": np.array(list(band_vocab.keys()), dtype=object)}


def deterministic_splits(n_channels: int, train_split: float, val_split: float, seed: int) -> DatasetSplit:
    rng = np.random.default_rng(seed)
    indices = rng.permutation(n_channels)
    n_train = int(round(n_channels * train_split))
    n_val = int(round(n_channels * val_split))
    train = indices[:n_train]
    val = indices[n_train : n_train + n_val]
    test = indices[n_train + n_val :]
    return DatasetSplit(train=train, val=val, test=test)


def save_dataset(dataset: dict[str, np.ndarray], output_dir: str | Path, metadata: dict[str, Any] | None = None) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    file_path = out / "neural_dataset.npz"
    np.savez_compressed(file_path, **dataset, metadata=np.array([metadata or {}], dtype=object))
    return file_path


def load_dataset(path: str | Path) -> dict[str, Any]:
    loaded = np.load(path, allow_pickle=True)
    return {key: loaded[key] for key in loaded.files}


try:
    import torch
    from torch.utils.data import Dataset

    class ChannelSequenceDataset(Dataset):
        def __init__(self, examples: dict[str, np.ndarray], channel_indices: np.ndarray):
            self.x_cont = examples["x_cont"][channel_indices]
            self.band_ids = examples["band_ids"][channel_indices]
            self.y = examples["y"][channel_indices]

        def __len__(self) -> int:
            return int(self.x_cont.shape[0])

        def __getitem__(self, index: int):
            return (
                torch.tensor(self.x_cont[index], dtype=torch.float32),
                torch.tensor(self.band_ids[index], dtype=torch.long),
                torch.tensor(self.y[index], dtype=torch.float32),
            )
except Exception:  # pragma: no cover
    ChannelSequenceDataset = None  # type: ignore
