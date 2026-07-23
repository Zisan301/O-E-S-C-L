# Day-11 External Benchmark Validation Report

Day-11 benchmarks O-E-S-C-L uniform-link GSNR predictions against an external GNPy/GN/EGN reference file.
The validation focus is the single-band C and S cases. The C+S scenario remains a simplified stress case unless separately validated with a Raman/ISRS-aware reference.

## Summary gate

- External reference gate passed: `False`
- Number of matched cases: `8`
- RMSE: `2.5056 dB`
- MAE: `2.0643 dB`
- Max absolute error: `4.3579 dB`

## O-E-S-C-L uniform GSNR summary

| scenario_group   | band   |   spans |   launch_power_dbm |   symbols |   ssfm_steps_per_span |   n_seeds |   oesc_uniform_gsnr_mean_db |   oesc_uniform_gsnr_std_db |   oesc_uniform_gsnr_ci95_db | case_id          |
|:-----------------|:-------|--------:|-------------------:|----------:|----------------------:|----------:|----------------------------:|---------------------------:|----------------------------:|:-----------------|
| C                | C      |      10 |                 -2 |     32768 |                     8 |         7 |                     14.3928 |                   0.028282 |                    0.020951 | C-C-10sp--2.0dBm |
| C                | C      |      10 |                  0 |     32768 |                     8 |         7 |                     13.9284 |                   0.009588 |                    0.007103 | C-C-10sp-+0.0dBm |
| C                | C      |      10 |                  2 |     32768 |                     8 |         7 |                     12.8747 |                   0.02552  |                    0.018905 | C-C-10sp-+2.0dBm |
| C                | C      |      10 |                  4 |     32768 |                     8 |         7 |                     10.7721 |                   0.058694 |                    0.043481 | C-C-10sp-+4.0dBm |
| S                | S      |      12 |                 -2 |     32768 |                     8 |         7 |                     13.4644 |                   0.021148 |                    0.015667 | S-S-12sp--2.0dBm |
| S                | S      |      12 |                  0 |     32768 |                     8 |         7 |                     12.9451 |                   0.017339 |                    0.012845 | S-S-12sp-+0.0dBm |
| S                | S      |      12 |                  2 |     32768 |                     8 |         7 |                     11.7839 |                   0.037947 |                    0.028112 | S-S-12sp-+2.0dBm |
| S                | S      |      12 |                  4 |     32768 |                     8 |         7 |                      9.5489 |                   0.035964 |                    0.026643 | S-S-12sp-+4.0dBm |

## External reference check

| status           | expected_csv_path                        | message                           |
|:-----------------|:-----------------------------------------|:----------------------------------|
| reference_loaded | validation_data\gnpy_day11_reference.csv | Loaded 8 external reference rows. |

## External validation errors

| scenario_group   | band   |   spans |   launch_power_dbm |   symbols |   ssfm_steps_per_span |   n_seeds |   oesc_uniform_gsnr_mean_db |   oesc_uniform_gsnr_std_db |   oesc_uniform_gsnr_ci95_db | case_id          | reference_model   | reference_source                       |   reference_gsnr_db | notes                                                       |   gsnr_error_db |   abs_gsnr_error_db |
|:-----------------|:-------|--------:|-------------------:|----------:|----------------------:|----------:|----------------------------:|---------------------------:|----------------------------:|:-----------------|:------------------|:---------------------------------------|--------------------:|:------------------------------------------------------------|----------------:|--------------------:|
| C                | C      |      10 |                 -2 |     32768 |                     8 |         7 |                     14.3928 |                   0.028282 |                    0.020951 | C-C-10sp--2.0dBm | GNPy              | GNPy local Day-12 matched spectrum run |               12.22 | Matched 64 Gbaud, 75 GHz spectrum; receiver GSNR(signal bw) |        2.17279  |            2.17279  |
| C                | C      |      10 |                  0 |     32768 |                     8 |         7 |                     13.9284 |                   0.009588 |                    0.007103 | C-C-10sp-+0.0dBm | GNPy              | GNPy local Day-12 matched spectrum run |               14.03 | Matched 64 Gbaud, 75 GHz spectrum; receiver GSNR(signal bw) |       -0.101623 |            0.101623 |
| C                | C      |      10 |                  2 |     32768 |                     8 |         7 |                     12.8747 |                   0.02552  |                    0.018905 | C-C-10sp-+2.0dBm | GNPy              | GNPy local Day-12 matched spectrum run |               15.13 | Matched 64 Gbaud, 75 GHz spectrum; receiver GSNR(signal bw) |       -2.25529  |            2.25529  |
| C                | C      |      10 |                  4 |     32768 |                     8 |         7 |                     10.7721 |                   0.058694 |                    0.043481 | C-C-10sp-+4.0dBm | GNPy              | GNPy local Day-12 matched spectrum run |               15.13 | Matched 64 Gbaud, 75 GHz spectrum; receiver GSNR(signal bw) |       -4.35794  |            4.35794  |
| S                | S      |      12 |                 -2 |     32768 |                     8 |         7 |                     13.4644 |                   0.021148 |                    0.015667 | S-S-12sp--2.0dBm | GNPy              | GNPy local Day-12 matched spectrum run |               11.8  | Matched 64 Gbaud, 75 GHz spectrum; receiver GSNR(signal bw) |        1.66438  |            1.66438  |
| S                | S      |      12 |                  0 |     32768 |                     8 |         7 |                     12.9451 |                   0.017339 |                    0.012845 | S-S-12sp-+0.0dBm | GNPy              | GNPy local Day-12 matched spectrum run |               13.24 | Matched 64 Gbaud, 75 GHz spectrum; receiver GSNR(signal bw) |       -0.294926 |            0.294926 |
| S                | S      |      12 |                  2 |     32768 |                     8 |         7 |                     11.7839 |                   0.037947 |                    0.028112 | S-S-12sp-+2.0dBm | GNPy              | GNPy local Day-12 matched spectrum run |               13.5  | Matched 64 Gbaud, 75 GHz spectrum; receiver GSNR(signal bw) |       -1.71613  |            1.71613  |
| S                | S      |      12 |                  4 |     32768 |                     8 |         7 |                      9.5489 |                   0.035964 |                    0.026643 | S-S-12sp-+4.0dBm | GNPy              | GNPy local Day-12 matched spectrum run |               13.5  | Matched 64 Gbaud, 75 GHz spectrum; receiver GSNR(signal bw) |       -3.9511   |            3.9511   |

## Generated figures

- `results\figures\fig_day11_external_gsnr_comparison.png`
- `results\figures\fig_day11_external_gsnr_error.png`

## Correct manuscript claim

External benchmark validation is still incomplete or did not pass. The manuscript must not claim formal GNPy/GN/EGN validation until the reference file is supplied and the gate passes.
