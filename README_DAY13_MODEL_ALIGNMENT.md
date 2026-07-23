# Day-13 Model Alignment and Calibrated Validation

Day-13 is used **after Day-12** when the direct GNPy comparison still has a large RMSE.
It does not fake or overwrite GNPy values. Instead, it diagnoses the mismatch and evaluates a transparent calibrated-validation protocol.

## Why Day-13 is needed

Day-11/Day-12 showed that external GNPy values were loaded, but direct uncalibrated agreement remained weak. This means the raw O-E-S-C-L SSFM output and GNPy reference still use different effective assumptions, especially in launch-power/nonlinear/amplifier behavior.

## What the script does

It reads:

```text
results/tables/day11_external_validation_errors.csv
results/tables/day12_gnpy_reference_values.csv
```

Then it calculates:

1. Uncalibrated external-reference error.
2. A band-dependent launch-power correction:

```text
G_calibrated(P, band) = G_OESC(P, band) + a_band + b_band * P
```

3. Primary held-out validation:

```text
Calibration powers: -2 and 0 dBm
Held-out validation powers: +2 and +4 dBm
```

4. Leave-one-power-out cross-validation for extra stability evidence.

## Run command

From the project root:

```powershell
python scripts\run_day13_model_alignment.py --config config\day13_model_alignment_config.yaml
```

## Outputs

```text
results/reports/day13_model_alignment_report.md
results/reports/day13_latex_calibrated_validation_snippet.tex
results/tables/day13_uncalibrated_errors.csv
results/tables/day13_calibration_coefficients.csv
results/tables/day13_primary_holdout_predictions.csv
results/tables/day13_lopo_predictions.csv
results/tables/day13_protocol_summary.csv
results/figures/fig_day13_uncalibrated_vs_calibrated_errors.png
results/figures/fig_day13_correction_vs_power.png
results/figures/fig_day13_lopo_errors.png
```

## Important manuscript rule

If Day-13 passes, the paper should claim **GNPy-calibrated external agreement**, not raw uncalibrated GNPy agreement.

Correct style:

> After fitting a band-dependent launch-power correction on calibration powers, the calibrated O-E-S-C-L prediction was evaluated on held-out launch powers.

Wrong style:

> The uncalibrated O-E-S-C-L model directly matches GNPy.

The uncalibrated Day-11/Day-12 failure should still be mentioned briefly as motivation for calibration.
