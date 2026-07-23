# Day-13 Model Alignment and Calibrated Validation Report

Day-13 evaluates whether the Day-12 GNPy mismatch can be handled with a transparent band-dependent launch-power correction. It does not replace or fabricate GNPy values.

## Summary gate

- Direct uncalibrated GNPy gate passed: `False`
- Direct uncalibrated RMSE: `2.5056 dB`
- Primary calibrated held-out gate passed: `True`
- Primary held-out RMSE: `0.3386 dB`
- Primary held-out MAE: `0.3034 dB`
- Primary held-out max absolute error: `0.5381 dB`
- Leave-one-power-out gate passed: `True`
- Leave-one-power-out RMSE: `0.2355 dB`
- Leave-one-power-out max absolute error: `0.4550 dB`
- Overall calibrated validation status: `passed`

## Calibration model

The correction is fitted separately for each band:

```text
G_calibrated(P, band) = G_OESC(P, band) + a_band + b_band * P
```

where `P` is launch power in dBm. The primary protocol fits `a_band` and `b_band` using -2 and 0 dBm, then validates on held-out +2 and +4 dBm cases.

## Primary calibration coefficients

| protocol                        | band   | calibration_powers_dbm   | validation_powers_dbm   |   intercept_db |   slope_db_per_dbm |   n_calibration_cases |   n_validation_cases |
|:--------------------------------|:-------|:-------------------------|:------------------------|---------------:|-------------------:|----------------------:|---------------------:|
| low_power_to_high_power_holdout | C      | -2,0                     | 2,4                     |       0.101623 |           1.13721  |                     2 |                    2 |
| low_power_to_high_power_holdout | S      | -2,0                     | 2,4                     |       0.294926 |           0.979652 |                     2 |                    2 |

## Protocol summary

| protocol                           | set                          |   n |   rmse_db |    mae_db |   max_abs_db |    bias_db |   rmse_gate_db |   max_abs_gate_db | passed     | interpretation                                                                    |
|:-----------------------------------|:-----------------------------|----:|----------:|----------:|-------------:|-----------:|---------------:|------------------:|:-----------|:----------------------------------------------------------------------------------|
| uncalibrated_direct_gnpy_reference | all_cases                    |   8 |  2.50556  | 2.06427   |     4.35794  | -1.10498   |           1    |                 1 | False      | Direct uncalibrated reference comparison; expected to remain failed after Day-12. |
| low_power_to_high_power_holdout    | calibration                  |   4 |  0        | 0         |     0        |  0         |         nan    |               nan | diagnostic | Calibration fit quality only; not validation.                                     |
| low_power_to_high_power_holdout    | heldout_validation           |   4 |  0.338586 | 0.303447  |     0.5381   |  0.303447  |           1    |                 1 | True       | Primary held-out calibrated validation.                                           |
| leave_one_power_out                | heldout_validation_all_folds |   8 |  0.235454 | 0.18097   |     0.455032 | -0.0123701 |           0.75 |                 1 | True       | Cross-validation stability check using held-out launch powers.                    |
| all_case_band_linear_insample      | in_sample_diagnostic_only    |   8 |  0.121446 | 0.0893936 |     0.271696 |  0         |         nan    |               nan | diagnostic | All-case in-sample diagnostic; do not present as validation.                      |

## Primary held-out validation predictions

| band   |   spans |   launch_power_dbm | set                |   oesc_uniform_gsnr_mean_db |   reference_gsnr_db |   applied_correction_db |   calibrated_oesc_gsnr_db |   calibrated_error_db |   abs_calibrated_error_db |
|:-------|--------:|-------------------:|:-------------------|----------------------------:|--------------------:|------------------------:|--------------------------:|----------------------:|--------------------------:|
| C      |      10 |                 -2 | calibration        |                     14.3928 |               12.22 |               -2.17279  |                   12.22   |              0        |                  0        |
| C      |      10 |                  0 | calibration        |                     13.9284 |               14.03 |                0.101623 |                   14.03   |              0        |                  0        |
| C      |      10 |                  2 | heldout_validation |                     12.8747 |               15.13 |                2.37603  |                   15.2507 |              0.120749 |                  0.120749 |
| C      |      10 |                  4 | heldout_validation |                     10.7721 |               15.13 |                4.65045  |                   15.4225 |              0.292505 |                  0.292505 |
| S      |      12 |                 -2 | calibration        |                     13.4644 |               11.8  |               -1.66438  |                   11.8    |              0        |                  0        |
| S      |      12 |                  0 | calibration        |                     12.9451 |               13.24 |                0.294926 |                   13.24   |              0        |                  0        |
| S      |      12 |                  2 | heldout_validation |                     11.7839 |               13.5  |                2.25423  |                   14.0381 |              0.5381   |                  0.5381   |
| S      |      12 |                  4 | heldout_validation |                      9.5489 |               13.5  |                4.21354  |                   13.7624 |              0.262435 |                  0.262435 |

## Diagnostic interpretation

- The raw Day-12 GNPy comparison should not be described as direct agreement because the uncalibrated RMSE remains high.
- The errors are power-dependent, so a constant offset alone is not a sufficient physical explanation.
- The calibrated result can be used only as a calibrated-alignment claim, not as a claim that the raw simulator directly reproduces GNPy.
- The C+S scenario remains a simplified stress case unless separately validated with Raman/ISRS-aware reference data.

## Correct manuscript claim

> A band-dependent launch-power correction was fitted using low-power calibration cases and evaluated on held-out high-power cases. The calibrated O-E-S-C-L predictions agreed with the matched GNPy reference within the reported held-out error bounds.

## Generated outputs

- `results/tables/day13_uncalibrated_errors.csv`
- `results/tables/day13_calibration_coefficients.csv`
- `results/tables/day13_primary_holdout_predictions.csv`
- `results/tables/day13_lopo_predictions.csv`
- `results/tables/day13_protocol_summary.csv`
- `results/figures/fig_day13_uncalibrated_vs_calibrated_errors.png`
- `results/figures/fig_day13_correction_vs_power.png`
- `results/figures/fig_day13_lopo_errors.png`
