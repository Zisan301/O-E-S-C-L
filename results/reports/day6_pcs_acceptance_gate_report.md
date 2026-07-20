# Day-6 PCS Acceptance Gate Report

**Passes Day-6 PCS confirmation:** True

**Recommended claim:** Day-6 confirmed nonzero PCS gain at the focused waveform operating point. Claim PCS-centered operating-region improvement, not neural superiority.

**Best PCS nu:** 0.32

## Details

### best_gain

|   pcs_nu |   n_pairs |   gmi_gain_mean |   gmi_gain_std |   gmi_gain_ci95 |   ngmi_gain_mean |   ngmi_gain_std |   ngmi_gain_ci95 |   rate_gain_mean |   rate_gain_std |   rate_gain_ci95 |   ber_delta_mean |   ber_delta_ci95 |   gsnr_delta_mean |   gsnr_delta_ci95 |
|---------:|----------:|----------------:|---------------:|----------------:|-----------------:|----------------:|-----------------:|-----------------:|----------------:|-----------------:|-----------------:|-----------------:|------------------:|------------------:|
|     0.32 |         7 |        0.028366 |       0.023343 |        0.017293 |         0.007091 |        0.005836 |         0.004323 |         0.003026 |         0.00249 |         0.001845 |        -0.002934 |          0.00115 |         -0.355673 |          0.093289 |

### best_pcs

|   pcs_nu | shaped   | display_name   | scenario   | band   |   spans |   launch_power_dbm | stress_name   |   n_seeds |   gmi_mean |   gmi_std |   gmi_ci95 |   ngmi_mean |   ngmi_std |   ngmi_ci95 |   ber_mean |   ber_std |   ber_ci95 |   gsnr_db_mean |   gsnr_db_std |   gsnr_db_ci95 |   rate_tbps_mean |   rate_tbps_std |   rate_tbps_ci95 |   train_time_s_mean |   train_time_s_std |   train_time_s_ci95 |   inference_time_s_mean |   inference_time_s_std |   inference_time_s_ci95 |   parameter_count_mean |   parameter_count_std |   parameter_count_ci95 |
|---------:|:---------|:---------------|:-----------|:-------|--------:|-------------------:|:--------------|----------:|-----------:|----------:|-----------:|------------:|-----------:|------------:|-----------:|----------:|-----------:|---------------:|--------------:|---------------:|-----------------:|----------------:|-----------------:|--------------------:|-------------------:|--------------------:|------------------------:|-----------------------:|------------------------:|-----------------------:|----------------------:|-----------------------:|
|     0.32 | True     | PCS raw        | pcs_raw    | C      |      10 |                  4 | evidence      |         7 |    3.21126 |  0.019775 |   0.014649 |    0.802815 |   0.004944 |    0.003662 |   0.045694 |  0.001191 |   0.000882 |        10.3894 |      0.075501 |       0.055932 |         0.342534 |        0.002109 |         0.001563 |                   0 |                  0 |                   0 |                       0 |                      0 |                       0 |                      0 |                     0 |                      0 |

### uniform_reference

|   pcs_nu | shaped   | display_name   | scenario    | band   |   spans |   launch_power_dbm | stress_name   |   n_seeds |   gmi_mean |   gmi_std |   gmi_ci95 |   ngmi_mean |   ngmi_std |   ngmi_ci95 |   ber_mean |   ber_std |   ber_ci95 |   gsnr_db_mean |   gsnr_db_std |   gsnr_db_ci95 |   rate_tbps_mean |   rate_tbps_std |   rate_tbps_ci95 |   train_time_s_mean |   train_time_s_std |   train_time_s_ci95 |   inference_time_s_mean |   inference_time_s_std |   inference_time_s_ci95 |   parameter_count_mean |   parameter_count_std |   parameter_count_ci95 |
|---------:|:---------|:---------------|:------------|:-------|--------:|-------------------:|:--------------|----------:|-----------:|----------:|-----------:|------------:|-----------:|------------:|-----------:|----------:|-----------:|---------------:|--------------:|---------------:|-----------------:|----------------:|-----------------:|--------------------:|-------------------:|--------------------:|------------------------:|-----------------------:|------------------------:|-----------------------:|----------------------:|-----------------------:|
|        0 | False    | Uniform raw    | uniform_raw | C      |      10 |                  4 | evidence      |         7 |    3.18289 |  0.018777 |   0.013911 |    0.795723 |   0.004694 |    0.003478 |   0.048628 |  0.001636 |   0.001212 |        10.7451 |      0.068722 |        0.05091 |         0.339509 |        0.002003 |         0.001484 |                   0 |                  0 |                   0 |                       0 |                      0 |                       0 |                      0 |                     0 |                      0 |

### non_saturated

True
