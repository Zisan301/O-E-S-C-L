# Day-15 C+S GNPy-Calibrated Validation Report

Day-15 extends calibrated validation to the C+S scenario.

## Reference type

- Reference type: `derived_separable_reference`
- Interpretation: `derived separable C+S baseline; not Raman/ISRS-aware`
- O-E-S-C-L source table: `results\tables\day8_raw_band_metrics.csv`

## Summary gate

- C+S calibrated held-out gate passed: `True`
- C+S held-out RMSE: `0.2288 dB`
- C+S held-out MAE: `0.2004 dB`
- C+S held-out max absolute error: `0.3107 dB`
- C+S LOPO gate passed: `True`
- C+S LOPO RMSE: `0.2802 dB`
- Overall C+S calibrated validation status: `passed`

## Calibration model

```text
G_calibrated_CS(P) = G_OESC_CS(P) + a_CS + b_CS * P
```

- intercept a_CS: `1.3334 dB`
- slope b_CS: `1.1974 dB/dBm`
- calibration powers: `[-2.0, 0.0]`
- held-out validation powers: `[2.0, 4.0]`

## Protocol summary

| protocol                           | set                          |   n |   rmse_db |   mae_db |   max_abs_db |    bias_db |   rmse_gate_db |   max_abs_gate_db | passed     | interpretation                                |
|:-----------------------------------|:-----------------------------|----:|----------:|---------:|-------------:|-----------:|---------------:|------------------:|:-----------|:----------------------------------------------|
| cs_uncalibrated_reference          | all_cases                    |   4 |  3.79254  | 3.11666  |     6.43377  | -2.58593   |           1    |                 1 | False      | Raw C+S comparison; expected to be difficult. |
| cs_low_power_to_high_power_holdout | calibration                  |   2 |  0        | 0        |     0        |  0         |         nan    |               nan | diagnostic | Calibration fit quality only; not validation. |
| cs_low_power_to_high_power_holdout | heldout_validation           |   2 |  0.228785 | 0.200448 |     0.310734 | -0.110287  |           1    |                 1 | True       | Primary C+S held-out calibrated validation.   |
| cs_leave_one_power_out             | heldout_validation_all_folds |   4 |  0.280182 | 0.238628 |     0.430949 | -0.0954512 |           0.75 |                 1 | True       | C+S cross-validation stability check.         |

## Predictions

|   launch_power_dbm |   spans |   oesc_uniform_gsnr_mean_db |   oesc_uniform_gsnr_std_db |   n_seeds | scenario_group   | band   | case_id       |   reference_gsnr_db | reference_source                                                                                          | notes                                                                                  |   c_reference_gsnr_db |   s_reference_gsnr_db |   uncalibrated_error_db |   needed_correction_db |   applied_correction_db |   calibrated_oesc_gsnr_db |   calibrated_error_db |   abs_calibrated_error_db | set                |
|-------------------:|--------:|----------------------------:|---------------------------:|----------:|:-----------------|:-------|:--------------|--------------------:|:----------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------|----------------------:|----------------------:|------------------------:|-----------------------:|------------------------:|--------------------------:|----------------------:|--------------------------:|:-------------------|
|                 -2 |      12 |                    13.0766  |                  0.34152   |         7 | C+S              | C+S    | CS-12sp--2dBm |             12.0151 | derived from Day-12 matched single-band GNPy C and S references; separable baseline, not Raman/ISRS-aware | Derived separable C+S reference from matched C and S GNPy values; not Raman/ISRS-aware |                 12.22 |                 11.8  |                 1.06148 |               -1.06148 |                -1.06148 |                   12.0151 |             0         |                 0         | calibration        |
|                  0 |      12 |                    12.3196  |                  0.230275  |         7 | C+S              | C+S    | CS-12sp-+0dBm |             13.6529 | derived from Day-12 matched single-band GNPy C and S references; separable baseline, not Raman/ISRS-aware | Derived separable C+S reference from matched C and S GNPy values; not Raman/ISRS-aware |                 14.03 |                 13.24 |                -1.33336 |                1.33336 |                 1.33336 |                   13.6529 |             0         |                 0         | calibration        |
|                  2 |      12 |                    10.753   |                  0.0678175 |         7 | C+S              | C+S    | CS-12sp-+2dBm |             14.391  | derived from Day-12 matched single-band GNPy C and S references; separable baseline, not Raman/ISRS-aware | Derived separable C+S reference from matched C and S GNPy values; not Raman/ISRS-aware |                 15.13 |                 13.5  |                -3.63804 |                3.63804 |                 3.7282  |                   14.4812 |             0.0901609 |                 0.0901609 | heldout_validation |
|                  4 |      12 |                     7.95725 |                  0.184491  |         7 | C+S              | C+S    | CS-12sp-+4dBm |             14.391  | derived from Day-12 matched single-band GNPy C and S references; separable baseline, not Raman/ISRS-aware | Derived separable C+S reference from matched C and S GNPy values; not Raman/ISRS-aware |                 15.13 |                 13.5  |                -6.43377 |                6.43377 |                 6.12304 |                   14.0803 |            -0.310734  |                 0.310734  | heldout_validation |

## Correct manuscript claim

If the reference type is derived separable baseline, the manuscript may state only that the simplified C+S case was calibrated against a separable C/S GNPy-derived baseline. It must not claim full Raman/ISRS-aware C+S validation.

If a true multiband/Raman-aware C+S reference file is supplied and the gates pass, the manuscript may state calibrated C+S validation against that specific reference.
