"""
src/neural_models.py
====================
Trainable BiLSTM-Transformer neural NLI residual estimator.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .dsp import _measure_snr_evm, _normalize_for_decision
from .training_data import make_supervised_examples


class NeuralNLICanceller(nn.Module):
    def __init__(self, cfg: dict[str, Any], n_bands: int = 8, continuous_features: int = 5):
        super().__init__()
        self.cfg = dict(cfg)
        requested_device = str(cfg.get("device", "cpu"))
        if requested_device == "cuda" and not torch.cuda.is_available():
            requested_device = "cpu"
        self.device = torch.device(requested_device)
        hidden = int(cfg.get("bilstm_hidden", 64))
        layers = int(cfg.get("bilstm_layers", 1))
        transformer_dim = int(cfg.get("transformer_dim", 64))
        heads = int(cfg.get("transformer_heads", 4))
        transformer_layers = int(cfg.get("transformer_layers", 1))
        dropout = float(cfg.get("dropout", 0.1))
        band_embedding_dim = int(cfg.get("band_embedding_dim", 4))

        self.band_embedding = nn.Embedding(max(n_bands, 1), band_embedding_dim)
        self.feature_projection = nn.Linear(continuous_features + band_embedding_dim, transformer_dim)
        self.bilstm = nn.LSTM(
            input_size=transformer_dim,
            hidden_size=hidden,
            num_layers=layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if layers > 1 else 0.0,
        )
        self.input_proj = nn.Linear(hidden * 2, transformer_dim)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=transformer_dim,
            nhead=heads,
            dim_feedforward=transformer_dim * 4,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=transformer_layers)
        self.output_proj = nn.Linear(transformer_dim, 2)
        self.checkpoint_loaded = False
        self.to(self.device)

    def forward(self, x_cont: torch.Tensor | dict[str, Any], band_ids: torch.Tensor | dict[str, Any] | None = None):
        if isinstance(x_cont, dict):
            if not isinstance(band_ids, dict):
                raise ValueError("Legacy dict inference requires tx_signal as the second argument")
            return self.infer_from_receiver(x_cont, band_ids)
        if band_ids is None:
            raise ValueError("band_ids are required")
        x_cont = x_cont.to(self.device)
        band_ids = band_ids.to(self.device)
        if band_ids.ndim == 1:
            band_ids = band_ids[:, None].expand(-1, x_cont.shape[1])
        embedded = self.band_embedding(band_ids)
        x = torch.cat([x_cont, embedded], dim=-1)
        x = self.feature_projection(x)
        lstm_out, _ = self.bilstm(x)
        z = self.input_proj(lstm_out)
        z = self.transformer(z)
        return self.output_proj(z)

    def load_or_init(self) -> bool:
        path = Path(self.cfg.get("save_path", "data/trained_models/nli_canceller.pt"))
        if path.exists():
            payload = torch.load(path, map_location=self.device)
            state = payload["model_state_dict"] if isinstance(payload, dict) and "model_state_dict" in payload else payload
            self.load_state_dict(state)
            self.checkpoint_loaded = True
            return True
        self.apply(self._init_weights)
        self.checkpoint_loaded = False
        return False

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                nn.init.zeros_(module.bias)

    def infer_from_receiver(self, rx_dsp: dict[str, Any], tx_signal: dict[str, Any]) -> dict[str, Any]:
        if not self.checkpoint_loaded and not bool(self.cfg.get("allow_untrained_baseline", False)):
            raise RuntimeError("No trained neural checkpoint loaded. Train the model or enable allow_untrained_baseline explicitly.")
        examples = make_supervised_examples(rx_dsp, tx_signal, target="residual")
        x_all = np.asarray(examples["x_cont"], dtype=np.float32)
        band_all = np.asarray(examples["band_ids"], dtype=np.int64)
        n_ch, n_symbols, _ = x_all.shape
        seq_len = max(8, min(int(self.cfg.get("sequence_length", 256)), n_symbols))
        batch_size = int(self.cfg.get("inference_batch_size", 32))
        residual = np.zeros((n_ch, n_symbols, 2), dtype=np.float32)
        band_tensor_all = torch.tensor(band_all, dtype=torch.long, device=self.device)

        self.eval()
        with torch.no_grad():
            for t0 in range(0, n_symbols, seq_len):
                t1 = min(t0 + seq_len, n_symbols)
                x_window = torch.tensor(x_all[:, t0:t1, :], dtype=torch.float32, device=self.device)
                for ch0 in range(0, n_ch, batch_size):
                    ch1 = min(ch0 + batch_size, n_ch)
                    pred = self.forward(x_window[ch0:ch1], band_tensor_all[ch0:ch1]).cpu().numpy()
                    residual[ch0:ch1, t0:t1, :] = pred

        predicted_residual = residual[..., 0] + 1j * residual[..., 1]
        rx = np.asarray(rx_dsp["field"], dtype=np.complex128)
        rx_clean = rx - predicted_residual
        tx = np.asarray(tx_signal["field"], dtype=np.complex128)[:, : rx_clean.shape[1]]
        snr_pre, _ = _measure_snr_evm(_normalize_for_decision(rx), _normalize_for_decision(tx))
        snr_post, evm_post = _measure_snr_evm(_normalize_for_decision(rx_clean), _normalize_for_decision(tx))
        return {
            "field": rx_clean,
            "predicted_nli": predicted_residual,
            "time_step_s": rx_dsp["time_step_s"],
            "n_channels": rx_clean.shape[0],
            "n_samples": rx_clean.shape[1],
            "snr_pre_nli_dB": snr_pre,
            "snr_post_nli_dB": snr_post,
            "snr_gain_dB": snr_post - snr_pre,
            "evm_post_nli": evm_post,
            "freq_grid": rx_dsp.get("freq_grid"),
            "channel_metadata": rx_dsp.get("channel_metadata"),
            "constellation": tx_signal.get("constellation"),
            "constellation_bits": tx_signal.get("constellation_bits"),
            "model_checkpoint_loaded": self.checkpoint_loaded,
        }


def set_torch_deterministic(seed: int) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def config_hash(cfg: dict[str, Any]) -> str:
    raw = json.dumps(cfg, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def train_model(model: NeuralNLICanceller, train_loader: DataLoader, val_loader: DataLoader, cfg: dict[str, Any]) -> dict[str, Any]:
    seed = int(cfg.get("seed", cfg.get("torch_seed", 0)))
    set_torch_deterministic(seed)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(cfg.get("learning_rate", 1e-4)), weight_decay=float(cfg.get("weight_decay", 1e-5)))
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(int(cfg.get("epochs", 50)), 1))
    criterion = nn.MSELoss()
    epochs = int(cfg.get("epochs", 50))
    patience = int(cfg.get("early_stopping_patience", 8))
    grad_clip = float(cfg.get("gradient_clip", 1.0))
    best_val = float("inf")
    bad_epochs = 0
    history = []
    save_path = Path(cfg.get("save_path", "data/trained_models/nli_canceller.pt"))
    save_path.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, epochs + 1):
        model.train()
        train_losses = []
        for x_cont, band_ids, y in train_loader:
            optimizer.zero_grad(set_to_none=True)
            pred = model(x_cont, band_ids)
            loss = criterion(pred, y.to(model.device))
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            optimizer.step()
            train_losses.append(float(loss.detach().cpu()))
        scheduler.step()
        val_loss = _evaluate_loss(model, val_loader, criterion)
        train_loss = float(np.mean(train_losses)) if train_losses else float("nan")
        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})
        if val_loss < best_val:
            best_val = val_loss
            bad_epochs = 0
            torch.save({
                "model_state_dict": model.state_dict(),
                "cfg": cfg,
                "config_hash": config_hash(cfg),
                "best_val_loss": best_val,
                "epoch": epoch,
                "seed": seed,
            }, save_path)
        else:
            bad_epochs += 1
            if bad_epochs >= patience:
                break
    model.load_or_init()
    return {"best_val_loss": best_val, "history": history, "save_path": str(save_path)}


def _evaluate_loss(model: NeuralNLICanceller, loader: DataLoader, criterion: nn.Module) -> float:
    model.eval()
    losses = []
    with torch.no_grad():
        for x_cont, band_ids, y in loader:
            pred = model(x_cont, band_ids)
            loss = criterion(pred, y.to(model.device))
            losses.append(float(loss.detach().cpu()))
    return float(np.mean(losses)) if losses else float("nan")


def evaluate_model(model: NeuralNLICanceller, test_loader: DataLoader) -> dict[str, float]:
    criterion = nn.MSELoss()
    test_loss = _evaluate_loss(model, test_loader, criterion)
    n_params = sum(p.numel() for p in model.parameters())
    return {"test_loss": test_loss, "parameter_count": int(n_params)}


def train_neural_nli(train_loader: DataLoader, val_loader: DataLoader, cfg: dict[str, Any]) -> tuple[NeuralNLICanceller, dict[str, Any]]:
    model = NeuralNLICanceller(cfg)
    model.apply(model._init_weights)
    result = train_model(model, train_loader, val_loader, cfg)
    return model, result


def evaluate_neural_nli(model: NeuralNLICanceller, test_loader: DataLoader) -> dict[str, float]:
    return evaluate_model(model, test_loader)
