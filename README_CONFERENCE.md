# O-E-S-C-L Conference-Level Replacement Package

This package turns the project into a reproducible **conference/workshop-level simulation pipeline** for joint probabilistic constellation shaping and lightweight neural nonlinear-interference mitigation across O/E/S/C/L optical bands.

## Suggested paper title

**A Reproducible Simulation Framework for Joint Probabilistic Shaping and Lightweight Neural NLI Mitigation in Multi-Band O/E/S/C/L Optical Links**

## What this version does

- Runs a deterministic O/E/S/C/L multi-band optical-link simulation.
- Compares four publication-friendly baselines:
  1. Uniform signalling without neural mitigation
  2. Probabilistic constellation shaping only
  3. Neural NLI mitigation only
  4. Proposed PCS + neural NLI mitigation
- Reports defensible metrics:
  - GSNR in dB
  - estimated pre-FEC BER
  - GMI / NGMI approximation
  - net achievable rate in Tb/s
  - model parameter count
  - training and inference time
- Generates paper-ready CSV files and figures.
- Includes validation gates to prevent unrealistic capacity or invalid BER claims.
- Writes a concise markdown experiment summary that can be used while drafting the paper.

## Install

```bash
pip install -r requirements.txt
```

## Run full conference pipeline

```bash
python main.py --config config/conference_config.yaml --mode full
```

## Smoke test

```bash
python main.py --config config/conference_config.yaml --mode smoke
```

## Output folders

After running:

```text
results/tables/
results/figures/
results/reports/
results/models/
```

## Important conference-paper positioning

Do **not** claim this is a final Q1/Q2/Q3 journal-ready result. Present it as:

> "A reproducible simulation-based proof-of-concept framework for evaluating joint shaping and lightweight learned NLI mitigation in multi-band optical links."

Use cautious language:

- "simulation study"
- "preliminary conference/workshop result"
- "achievable-rate estimate"
- "validation-aware framework"
- "requires future validation against split-step Fourier or experimental data"

Avoid unsupported statements such as:

- "485 Tb/s confirmed capacity"
- "real-world deployment-ready"
- "experimentally validated"
- "Q2 journal-ready"
