# Day-15 S-band Starter GNPy Validation

This run tests whether a dedicated S-band GNPy setup can produce external-reference GSNR rows.
The cases intentionally begin with a small 3-channel, 32-GBd, 100-GHz grid before larger S-band validation is attempted.

## Claim policy

These rows are S-band diagnostic evidence only. They must not be reported as full S-band validation until multiple operating points pass and calibration is documented.

## Case summary

```text
                              case_id scenario_group band  spans  launch_power_dbm  center_nm  baud_rate_gbaud  channel_spacing_ghz  channels  span_length_km  symbols seeds  s_attenuation_db_per_km  s_noise_figure_db  s_edfa_f_min_hz  s_edfa_f_max_hz status failure_reason  gnpy_reference_gsnr_db  oescl_uniform_gsnr_mean_db  oescl_uniform_gsnr_std_db  oescl_n_seeds  raw_error_db  abs_raw_error_db  sband_offset_db  calibrated_oescl_gsnr_db  calibrated_error_db  abs_calibrated_error_db                                                                                                             gnpy_stdout
day15_S_smoke_1520nm_6sp_0dBm_3ch_32G              S    S      6               0.0     1520.0             32.0                100.0         3            80.0    16384 1,2,3                     0.22                5.5     1.960000e+14     2.020000e+14     ok                                  21.26                   13.836115                   0.010298              3     -7.423885          7.423885         7.348885                    21.185               -0.075                    0.075 validation_data\day15_sband\day15_S_smoke_1520nm_6sp_0dBm_3ch_32G\day15_S_smoke_1520nm_6sp_0dBm_3ch_32G_gnpy_stdout.txt
day15_S_smoke_1510nm_6sp_0dBm_3ch_32G              S    S      6               0.0     1510.0             32.0                100.0         3            80.0    16384 1,2,3                     0.22                5.5     1.960000e+14     2.020000e+14     ok                                  21.21                   13.836115                   0.010298              3     -7.373885          7.373885         7.348885                    21.185               -0.025                    0.025 validation_data\day15_sband\day15_S_smoke_1510nm_6sp_0dBm_3ch_32G\day15_S_smoke_1510nm_6sp_0dBm_3ch_32G_gnpy_stdout.txt
day15_S_smoke_1500nm_6sp_0dBm_3ch_32G              S    S      6               0.0     1500.0             32.0                100.0         3            80.0    16384 1,2,3                     0.22                5.5     1.960000e+14     2.020000e+14     ok                                  21.16                   13.836115                   0.010298              3     -7.323885          7.323885         7.348885                    21.185                0.025                    0.025 validation_data\day15_sband\day15_S_smoke_1500nm_6sp_0dBm_3ch_32G\day15_S_smoke_1500nm_6sp_0dBm_3ch_32G_gnpy_stdout.txt
day15_S_smoke_1490nm_6sp_0dBm_3ch_32G              S    S      6               0.0     1490.0             32.0                100.0         3            80.0    16384 1,2,3                     0.22                5.5     1.960000e+14     2.020000e+14     ok                                  21.11                   13.836115                   0.010298              3     -7.273885          7.273885         7.348885                    21.185                0.075                    0.075 validation_data\day15_sband\day15_S_smoke_1490nm_6sp_0dBm_3ch_32G\day15_S_smoke_1490nm_6sp_0dBm_3ch_32G_gnpy_stdout.txt
```

## Aggregate metrics for successful rows

- Successful cases: `4` of `4`.
- S-band diagnostic offset: `7.348885 dB`.
- Raw RMSE: `7.349098 dB`.
- Raw MAE: `7.348885 dB`.
- S-band offset-calibrated RMSE: `0.055902 dB`.
- S-band offset-calibrated MAE: `0.050000 dB`.

## Interpretation

At least one S-band GNPy case completed. If fewer than three operating points pass, treat this as smoke-test evidence only.
The next step is to expand around the passing wavelength with more spans, launch powers and channel counts.
