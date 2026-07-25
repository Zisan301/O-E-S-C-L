# Day-12 External GNPy Alignment Sweep

Day-12 compares O-E-S-C-L uniform GSNR against independent GNPy center-channel GSNR across multiple C-band span counts.

## Sweep summary
| scenario_group   | band   |   spans |   span_length_km |   total_length_km |   launch_power_dbm |   gnpy_reference_gsnr_db |   oescl_uniform_gsnr_mean_db |   oescl_uniform_gsnr_std_db |   oescl_n_seeds |   gsnr_error_db |   abs_gsnr_error_db | gnpy_stdout                                    |
|:-----------------|:-------|--------:|-----------------:|------------------:|-------------------:|-------------------------:|-----------------------------:|----------------------------:|----------------:|----------------:|--------------------:|:-----------------------------------------------|
| C                | C      |       6 |               80 |               480 |                  2 |                    20.92 |                      14.2868 |                    0.024952 |               5 |        -6.63317 |             6.63317 | validation_data\day12_gnpy_c_6span_stdout.txt  |
| C                | C      |       8 |               80 |               640 |                  2 |                    19.72 |                      13.6386 |                    0.04551  |               5 |        -6.08144 |             6.08144 | validation_data\day12_gnpy_c_8span_stdout.txt  |
| C                | C      |      10 |               80 |               800 |                  2 |                    18.78 |                      12.8777 |                    0.019213 |               5 |        -5.90231 |             5.90231 | validation_data\day12_gnpy_c_10span_stdout.txt |
| C                | C      |      12 |               80 |               960 |                  2 |                    18    |                      12.0056 |                    0.03139  |               5 |        -5.99445 |             5.99445 | validation_data\day12_gnpy_c_12span_stdout.txt |

## Aggregate alignment metrics
- RMSE: `6.159415 dB`
- Mean error / offset: `-6.152843 dB`
- Offset standard deviation: `0.328463 dB`
- Error range: `0.730855 dB`
- Error-vs-span slope: `0.104764 dB/span`

## Decision
- `mostly_constant_offset`

## Interpretation
The O-E-S-C-L absolute GSNR scale appears conservatively offset from GNPy, but the offset is relatively stable across span count.

## Manuscript implication
Do not claim formal absolute GNPy validation yet. It may be acceptable to report the GNPy comparison as an external calibration diagnostic and to focus manuscript claims on PCS gain trends after explaining the conservative GSNR offset.