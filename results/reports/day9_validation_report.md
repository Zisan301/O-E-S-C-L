# Day-9 Publication-Strength Validation Report

This run adds the minimum reviewer-facing validation outputs requested after the first Springer PNC draft review.
It does not replace a full Raman/ISRS-calibrated C+S validation. It strengthens the current manuscript by adding raw per-seed evidence, SSFM step-size convergence, symbol-count convergence, and an internal GN-style GSNR sanity benchmark.

## Generated tables
- `raw_band`: `results\tables\day9_raw_band_metrics_selected.csv`
- `seed_level`: `results\tables\day9_raw_per_seed_selected.csv`
- `paired_gain`: `results\tables\day9_raw_per_seed_paired_gains.csv`
- `ssfm_convergence`: `results\tables\day9_ssfm_step_convergence.csv`
- `symbol_convergence`: `results\tables\day9_symbol_count_convergence.csv`
- `gn_style_benchmark`: `results\tables\day9_gn_style_gsnr_benchmark.csv`
- `gn_style_raw`: `results\tables\day9_gn_style_raw_uniform_runs.csv`
- `external_reference_template`: `results\tables\day9_external_reference_template.csv`
- `external_reference_check`: `results\tables\day9_external_reference_check.csv`

## Generated figures
- `results\figures\fig_day9_ssfm_step_convergence.png`
- `results\figures\fig_day9_symbol_count_convergence.png`
- `results\figures\fig_day9_gn_style_gsnr_comparison.png`
- `results\figures\fig_day9_seed_gain_distribution.png`

## Summary gates
- SSFM step convergence gate passed: `True`
- Symbol-count convergence gate passed: `False`
- Internal GN-style benchmark RMSE over grid: `2.5812 dB`

## Raw accepted-point paired gains
| scenario_group   |   spans |   launch_power_dbm |   pcs_nu |   n_pairs |   gmi_gain_mean |   gmi_gain_std |   gmi_gain_ci95 |   ngmi_gain_mean |   ngmi_gain_std |   ngmi_gain_ci95 |   ber_delta_mean |   ber_delta_std |   ber_delta_ci95 |   gsnr_delta_mean |   gsnr_delta_std |   gsnr_delta_ci95 |   aggregate_rate_gain_mean |   aggregate_rate_gain_std |   aggregate_rate_gain_ci95 |   rate_gain_mean |   rate_gain_std |   rate_gain_ci95 |
|:-----------------|--------:|-------------------:|---------:|----------:|----------------:|---------------:|----------------:|-----------------:|----------------:|-----------------:|-----------------:|----------------:|-----------------:|------------------:|-----------------:|------------------:|---------------------------:|--------------------------:|---------------------------:|-----------------:|----------------:|-----------------:|
| C                |      10 |                  2 |     0.36 |         7 |        0.052577 |       0.02284  |        0.01692  |         0.013144 |        0.00571  |         0.00423  |        -0.003322 |        0.001643 |         0.001217 |         -0.220331 |         0.093701 |          0.069415 |                   0.005608 |                  0.002436 |                   0.001805 |         0.005608 |        0.002436 |         0.001805 |
| C+S              |      12 |                  0 |     0.36 |         7 |        0.073238 |       0.015981 |        0.011839 |         0.018309 |        0.003995 |         0.00296  |        -0.005266 |        0.000918 |         0.00068  |         -0.142034 |         0.067422 |          0.049947 |                   0.015624 |                  0.003409 |                   0.002526 |         0.007812 |        0.001705 |         0.001263 |
| S                |      12 |                 -2 |     0.36 |         7 |        0.068903 |       0.015136 |        0.011213 |         0.017226 |        0.003784 |         0.002803 |        -0.00456  |        0.000912 |         0.000676 |         -0.029002 |         0.082807 |          0.061344 |                   0.00735  |                  0.001614 |                   0.001196 |         0.00735  |        0.001614 |         0.001196 |

## External reference check
| status                 | expected_csv_path                       | message                                                                         |
|:-----------------------|:----------------------------------------|:--------------------------------------------------------------------------------|
| reference_file_missing | validation_data\gnpy_day9_reference.csv | Fill the template with GNPy/GN/EGN reference GSNR values and rerun this script. |

## Correct manuscript claim after Day-9
The manuscript can now state that the accepted C/S PCS gains are supported by repeated-seed paired comparisons and basic numerical convergence checks. If the optional GNPy/GN/EGN reference file is supplied, the paper can additionally report an external GSNR benchmark RMSE. Until then, the GN-style table must be described only as an internal analytical sanity check, not as a formal GNPy validation.