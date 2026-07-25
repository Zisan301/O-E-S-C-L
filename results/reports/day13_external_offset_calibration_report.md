# Day-13 External Offset-Calibration Diagnostic

Day-13 evaluates whether the Day-12 O-E-S-C-L vs GNPy mismatch can be explained by one constant conservative GSNR offset.

This is not reported as raw absolute GNPy validation. It is a calibration diagnostic for the absolute GSNR scale.

## Raw Day-12 alignment
- Raw RMSE: `6.159415 dB`
- Raw mean error, O-E-S-C-L minus GNPy: `-6.152843 dB`
- Raw offset standard deviation: `0.328463 dB`

## Constant offset
- Offset applied to O-E-S-C-L GSNR: `+6.152843 dB`

## Offset-calibrated alignment
- Calibrated RMSE: `0.284458 dB`
- Calibrated MAE: `0.240163 dB`
- Calibrated max absolute error: `0.480325 dB`

## Leave-one-out offset diagnostic
- LOO RMSE: `0.379277 dB`
- LOO MAE: `0.320217 dB`
- LOO max absolute error: `0.640434 dB`

## Calibrated sweep table
| scenario_group   | band   |   spans |   span_length_km |   total_length_km |   launch_power_dbm |   gnpy_reference_gsnr_db |   oescl_uniform_gsnr_mean_db |   oescl_uniform_gsnr_std_db |   oescl_n_seeds |   gsnr_error_db |   abs_gsnr_error_db | gnpy_stdout                                    |   constant_offset_db |   oescl_offset_calibrated_gsnr_db |   calibrated_error_db |   abs_calibrated_error_db |
|:-----------------|:-------|--------:|-----------------:|------------------:|-------------------:|-------------------------:|-----------------------------:|----------------------------:|----------------:|----------------:|--------------------:|:-----------------------------------------------|---------------------:|----------------------------------:|----------------------:|--------------------------:|
| C                | C      |       6 |               80 |               480 |                  2 |                    20.92 |                      14.2868 |                    0.024952 |               5 |        -6.63317 |             6.63317 | validation_data\day12_gnpy_c_6span_stdout.txt  |              6.15284 |                           20.4397 |             -0.480325 |                  0.480325 |
| C                | C      |       8 |               80 |               640 |                  2 |                    19.72 |                      13.6386 |                    0.04551  |               5 |        -6.08144 |             6.08144 | validation_data\day12_gnpy_c_8span_stdout.txt  |              6.15284 |                           19.7914 |              0.071401 |                  0.071401 |
| C                | C      |      10 |               80 |               800 |                  2 |                    18.78 |                      12.8777 |                    0.019213 |               5 |        -5.90231 |             5.90231 | validation_data\day12_gnpy_c_10span_stdout.txt |              6.15284 |                           19.0305 |              0.25053  |                  0.25053  |
| C                | C      |      12 |               80 |               960 |                  2 |                    18    |                      12.0056 |                    0.03139  |               5 |        -5.99445 |             5.99445 | validation_data\day12_gnpy_c_12span_stdout.txt |              6.15284 |                           18.1584 |              0.158394 |                  0.158394 |

## Leave-one-out table
|   spans |   loo_offset_db |   loo_predicted_gsnr_db |   gnpy_reference_gsnr_db |   loo_error_db |   abs_loo_error_db |
|--------:|----------------:|------------------------:|-------------------------:|---------------:|-------------------:|
|       6 |         5.99273 |                 20.2796 |                    20.92 |      -0.640434 |           0.640434 |
|       8 |         6.17664 |                 19.8152 |                    19.72 |       0.095201 |           0.095201 |
|      10 |         6.23635 |                 19.114  |                    18.78 |       0.33404  |           0.33404  |
|      12 |         6.20564 |                 18.2112 |                    18    |       0.211193 |           0.211193 |

## Decision
- Diagnostic offset calibration passed: `True`

## Correct interpretation
The raw absolute GSNR scale of O-E-S-C-L is conservatively shifted relative to GNPy, but the mismatch is well explained by a nearly constant offset across span count. The manuscript may use this as an external calibration diagnostic while keeping the main validated claim focused on PCS gain trends and repeated-seed convergence.