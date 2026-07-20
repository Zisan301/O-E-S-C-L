# Day-4 Meaningful Stress Tuning Patch

Your receiver-dispersion-compensated Day-4 run passed sanity tests, but it became too easy:

- GMI = 4 everywhere
- NGMI = 1 everywhere
- BER = 0 everywhere
- rate = constant everywhere

That is not useful for an Optica-level paper because it does not separate methods.

This patch only updates:

```text
config/day4_calibrated_config.yaml
scripts/run_day4_meaningful_stress.bat
```

It keeps the receiver dispersion compensation fix and increases noise/nonlinear stress so the medium regime becomes meaningful.

## Install

Extract this ZIP directly inside:

```text
E:\VS Code\O+E+S+C+L
```

Allow replace/merge.

## Run

```powershell
python main.py --config config/day4_calibrated_config.yaml --mode day4cal
```

or:

```powershell
scripts\run_day4_meaningful_stress.bat
```

## Good target result

The new run is useful if medium-regime values look roughly like:

```text
GMI: 2.5 to 3.8 bits/symbol
NGMI: 0.62 to 0.95
BER: 1e-4 to 1e-1
GSNR: 12 to 24 dB
```

Avoid:
- all GMI = 4, NGMI = 1, BER = 0  -> too easy
- BER around 0.47, NGMI near 0      -> too hard/random

## Send back

```text
results\reports\day4_calibration_fix_report.md
results\reports\day4_calibrated_comparison_report.md
results\tables\day4_calibration_sanity.csv
results\tables\day4_calibrated_best_methods.csv
results\tables\day4_calibrated_pcs_ci.csv
```
