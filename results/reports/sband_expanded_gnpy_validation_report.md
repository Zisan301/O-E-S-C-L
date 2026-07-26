# Day-15 Expanded S-band GNPy Validation

This run expands the passing S-band smoke test into a small span/power-diverse diagnostic matrix.
It should still be reported as external-reference diagnostic evidence rather than experimental validation.

## Claim policy

S-band results are valid only for the generated GNPy equipment/spectrum configuration and the tested operating points.
Raw, offset-calibrated and leave-one-out calibrated errors must remain separate.

## Case summary

```text
                         case_id scenario_group band  spans  launch_power_dbm  center_nm  baud_rate_gbaud  channel_spacing_ghz  channels  span_length_km  symbols seeds  s_attenuation_db_per_km  s_noise_figure_db  s_edfa_f_min_thz  s_edfa_f_max_thz status failure_reason  gnpy_reference_gsnr_db  oescl_uniform_gsnr_mean_db  oescl_uniform_gsnr_std_db  oescl_n_seeds  raw_error_db  abs_raw_error_db                                                                                                            gnpy_stdout  sband_offset_db  calibrated_oescl_gsnr_db  calibrated_error_db  abs_calibrated_error_db  loo_offset_db  loo_calibrated_error_db  abs_loo_calibrated_error_db
day15_S_1520nm_6sp_m1dBm_3ch_32G              S    S      6              -1.0     1520.0             32.0                100.0         3            80.0    16384 1,2,3                     0.22                5.5             196.0             202.0     ok                                  20.17                   13.945515                   0.016766              3     -6.224485          6.224485 validation_data\day15_sband_expanded\day15_S_1520nm_6sp_m1dBm_3ch_32G\day15_S_1520nm_6sp_m1dBm_3ch_32G_gnpy_stdout.txt         6.054203                 19.999718            -0.170282                 0.170282       6.029877                -0.194608                     0.194608
 day15_S_1520nm_6sp_0dBm_3ch_32G              S    S      6               0.0     1520.0             32.0                100.0         3            80.0    16384 1,2,3                     0.22                5.5             196.0             202.0     ok                                  21.26                   13.836115                   0.010298              3     -7.423885          7.423885   validation_data\day15_sband_expanded\day15_S_1520nm_6sp_0dBm_3ch_32G\day15_S_1520nm_6sp_0dBm_3ch_32G_gnpy_stdout.txt         6.054203                 19.890318            -1.369682                 1.369682       5.858534                -1.565351                     1.565351
 day15_S_1520nm_6sp_1dBm_3ch_32G              S    S      6               1.0     1520.0             32.0                100.0         3            80.0    16384 1,2,3                     0.22                5.5             196.0             202.0     ok                                  21.18                   13.698755                   0.037197              3     -7.481245          7.481245   validation_data\day15_sband_expanded\day15_S_1520nm_6sp_1dBm_3ch_32G\day15_S_1520nm_6sp_1dBm_3ch_32G_gnpy_stdout.txt         6.054203                 19.752958            -1.427042                 1.427042       5.850340                -1.630906                     1.630906
 day15_S_1520nm_8sp_0dBm_3ch_32G              S    S      8               0.0     1520.0             32.0                100.0         3            80.0    16384 1,2,3                     0.22                5.5             196.0             202.0     ok                                  20.04                   13.600538                   0.035452              3     -6.439462          6.439462   validation_data\day15_sband_expanded\day15_S_1520nm_8sp_0dBm_3ch_32G\day15_S_1520nm_8sp_0dBm_3ch_32G_gnpy_stdout.txt         6.054203                 19.654741            -0.385259                 0.385259       5.999166                -0.440296                     0.440296
day15_S_1520nm_10sp_0dBm_3ch_32G              S    S     10               0.0     1520.0             32.0                100.0         3            80.0    16384 1,2,3                     0.22                5.5             196.0             202.0     ok                                  19.09                   13.291518                   0.040794              3     -5.798482          5.798482 validation_data\day15_sband_expanded\day15_S_1520nm_10sp_0dBm_3ch_32G\day15_S_1520nm_10sp_0dBm_3ch_32G_gnpy_stdout.txt         6.054203                 19.345721             0.255721                 0.255721       6.090734                 0.292252                     0.292252
day15_S_1520nm_12sp_0dBm_3ch_32G              S    S     12               0.0     1520.0             32.0                100.0         3            80.0    16384 1,2,3                     0.22                5.5             196.0             202.0     ok                                  18.31                   12.946977                   0.030990              3     -5.363023          5.363023 validation_data\day15_sband_expanded\day15_S_1520nm_12sp_0dBm_3ch_32G\day15_S_1520nm_12sp_0dBm_3ch_32G_gnpy_stdout.txt         6.054203                 19.001180             0.691180                 0.691180       6.152943                 0.789920                     0.789920
 day15_S_1520nm_8sp_2dBm_3ch_32G              S    S      8               2.0     1520.0             32.0                100.0         3            80.0    16384 1,2,3                     0.22                5.5             196.0             202.0     ok                                  18.12                   13.100230                   0.017559              3     -5.019770          5.019770   validation_data\day15_sband_expanded\day15_S_1520nm_8sp_2dBm_3ch_32G\day15_S_1520nm_8sp_2dBm_3ch_32G_gnpy_stdout.txt         6.054203                 19.154433             1.034433                 1.034433       6.201979                 1.182209                     1.182209
day15_S_1520nm_10sp_2dBm_3ch_32G              S    S     10               2.0     1520.0             32.0                100.0         3            80.0    16384 1,2,3                     0.22                5.5             196.0             202.0     ok                                  17.12                   12.436729                   0.015975              3     -4.683271          4.683271 validation_data\day15_sband_expanded\day15_S_1520nm_10sp_2dBm_3ch_32G\day15_S_1520nm_10sp_2dBm_3ch_32G_gnpy_stdout.txt         6.054203                 18.490932             1.370932                 1.370932       6.250050                 1.566779                     1.566779
```

## Aggregate metrics for successful rows

- Successful cases: `8` of `8`.
- S-band diagnostic offset: `6.054203 dB`.
- Raw RMSE: `6.131981 dB`.
- Raw MAE: `6.054203 dB`.
- Raw max abs. error: `7.481245 dB`.
- Offset-calibrated RMSE: `0.973558 dB`.
- Offset-calibrated MAE: `0.838066 dB`.
- Offset-calibrated max abs. error: `1.427042 dB`.
- Leave-one-out calibrated RMSE: `1.112638 dB`.
- Leave-one-out calibrated MAE: `0.957790 dB`.
- Leave-one-out calibrated max abs. error: `1.630906 dB`.

## Interpretation

If most or all rows pass with low offset-calibrated and leave-one-out error, this can upgrade the manuscript from 'S-band failed starter cases' to 'S-band diagnostic extension'.
If leave-one-out error is large, report the result as limited same-matrix calibration rather than transferable S-band validation.
