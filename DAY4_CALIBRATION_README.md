# O-E-S-C-L Day-4 Calibration/Fix Patch

The previous Day-4 run was too degraded:
- BER around 0.47
- NGMI near 0
- GSNR near 0 dB

This patch calibrates the SSFM-lite model before using it for paper results.

## Added

1. Calibrated SSFM-lite model
2. Sanity tests:
   - identity/no impairment
   - linear dispersion only
   - nonlinear only
   - calibrated easy regime
3. Easy / medium / hard regimes
4. Constellation plots:
   - TX
   - raw RX
   - linear EQ
   - neural residual compensation
5. GMI/NGMI/BER/GSNR calibrated comparison
6. PCS sanity check across shaping nu

## Install

Extract this ZIP directly inside your project root:

```text
E:\VS Code\O+E+S+C+L
```

Allow replace/merge.

## Run

```powershell
pip install -r requirements.txt
python main.py --config config/day4_calibrated_config.yaml --mode day4cal
```

Or:

```powershell
scripts\run_day4_calibration_fix.bat
```

## Send back after running

```text
results\reports\day4_calibration_fix_report.md
results\reports\day4_calibrated_comparison_report.md
results\tables\day4_calibration_sanity.csv
results\tables\day4_calibrated_best_methods.csv
results\tables\day4_calibrated_pcs_ci.csv
```

## How to judge

Use Day-4 calibrated results in the paper only if:

1. identity/no-impairment BER is 0 or near 0;
2. easy regime BER is not random;
3. medium regime gives meaningful BER/GMI differences;
4. neural or another baseline improves GMI/GSNR without destroying BER;
5. PCS is not claimed as helpful unless nonzero nu wins.
