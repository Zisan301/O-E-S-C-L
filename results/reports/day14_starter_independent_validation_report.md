# Day-14 Starter Independent Validation

This is a starter broader-validation run. It expands beyond the Day-12 C-band span-only sweep by varying band, span count, launch power, channel loading and baud rate.

## Claim policy

These results must be reported as diagnostic evidence only. Raw and calibrated errors must remain separate.

## Case summary

```text
                   case_id scenario_group band  spans  launch_power_dbm  center_nm  baud_rate_gbaud  channel_spacing_ghz  channels  symbols seeds  day13_fixed_offset_db status                                                                                                                                                failure_reason  gnpy_reference_gsnr_db  oescl_uniform_gsnr_mean_db  oescl_uniform_gsnr_std_db  oescl_n_seeds  calibrated_oescl_gsnr_db  raw_error_db  calibrated_error_db  abs_raw_error_db  abs_calibrated_error_db                                                                                 gnpy_stdout
 day14_C_6sp_m1dBm_5ch_64G              C    C      6              -1.0     1550.0             64.0                100.0         5    16384 1,2,3               6.152843     ok                                                                                                                                                                                 19.39                   14.735341                   0.038024              3                 20.888184     -4.654659             1.498184          4.654659                 1.498184   validation_data\day14\day14_C_6sp_m1dBm_5ch_64G\day14_C_6sp_m1dBm_5ch_64G_gnpy_stdout.txt
day14_C_12sp_3dBm_15ch_32G              C    C     12               3.0     1550.0             32.0                 50.0        15    16384 1,2,3               6.152843     ok                                                                                                                                                                                 11.34                   10.844955                   0.121239              3                 16.997798     -0.495045             5.657798          0.495045                 5.657798 validation_data\day14\day14_C_12sp_3dBm_15ch_32G\day14_C_12sp_3dBm_15ch_32G_gnpy_stdout.txt
  day14_S_8sp_1dBm_9ch_32G              S    S      8               1.0     1500.0             32.0                 75.0         9    16384 1,2,3               6.152843 failed    GNPy failed for day14_S_8sp_1dBm_9ch_32G. See E:\VS Code\O+E+S+C+L\validation_data\day14\day14_S_8sp_1dBm_9ch_32G\day14_S_8sp_1dBm_9ch_32G_gnpy_stdout.txt                     NaN                         NaN                        NaN              0                       NaN           NaN                  NaN               NaN                      NaN                                                                                            
 day14_S_12sp_3dBm_5ch_32G              S    S     12               3.0     1500.0             32.0                100.0         5    16384 1,2,3               6.152843 failed GNPy failed for day14_S_12sp_3dBm_5ch_32G. See E:\VS Code\O+E+S+C+L\validation_data\day14\day14_S_12sp_3dBm_5ch_32G\day14_S_12sp_3dBm_5ch_32G_gnpy_stdout.txt                     NaN                         NaN                        NaN              0                       NaN           NaN                  NaN               NaN                      NaN                                                                                            
```

## Aggregate metrics

- Raw RMSE: `3.309904 dB`
- Raw MAE: `2.574852 dB`
- Raw max abs. error: `4.654659 dB`
- Calibrated RMSE using fixed Day-13 offset: `4.138553 dB`
- Calibrated MAE using fixed Day-13 offset: `3.577991 dB`
- Calibrated max abs. error using fixed Day-13 offset: `5.657798 dB`

## Interpretation

- Successful cases: `2` of `4`.
- Failed cases: `2` of `4`.

The fixed Day-13 offset does not transfer cleanly to this broader starter matrix. In the successful C-band cases, the calibrated RMSE is larger than the raw RMSE. Therefore, these Day-14 results should be reported as limitation evidence, not as broader external validation success.

The S-band generated GNPy cases failed under the current automatic GNPy setup and are retained in the table instead of being hidden. This indicates that S-band external-reference generation needs a dedicated equipment/spectrum configuration before it can be used as validation evidence.

## Manuscript implication

Use Day-14 only to show that broader validation was attempted and that the Day-13 C-band offset is not universally transferable. Do not claim full C/S-band external validation from this starter run.
