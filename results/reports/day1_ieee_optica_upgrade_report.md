# Day-1 IEEE/Optica Upgrade Report

## What was added

- Real system-architecture diagram for Fig. 1.
- Launch-power sweep across multiple powers.
- Five-seed repeated simulation.
- Mean, standard deviation, and 95% confidence intervals.
- BER log-scale figure.
- Cleaner complexity/performance plot.
- Band-wise GSNR heatmap.

## Key Day-1 findings

- Best proposed mean GSNR: **22.982 ± 0.037 dB** at **-6.0 dBm**.
- Best proposed mean estimated rate: **2.129 ± 0.000 Tb/s** at **-6.0 dBm**.
- Largest GSNR advantage over uniform baseline: **0.751 dB** at **4.0 dBm**.
- Rate delta at that point: **-0.0040 Tb/s**.

## Submission-safe interpretation

The Day-1 results should be framed as a sweep-based validation upgrade. The strongest claim is not universal capacity improvement; it is that the framework identifies operating regions where neural residual compensation improves GSNR and residual distortion, while PCS must be tuned carefully.

## Generated figures

- `results\figures\fig_day1_system_architecture.png`
- `results\figures\fig_day1_launch_power_gsnr.png`
- `results\figures\fig_day1_launch_power_ngmi.png`
- `results\figures\fig_day1_launch_power_rate.png`
- `results\figures\fig_day1_launch_power_ber_log.png`
- `results\figures\fig_day1_complexity_clean.png`
- `results\figures\fig_day1_bandwise_gsnr_heatmap.png`

## CI table preview

|   launch_power_dbm | display_name     |   total_net_rate_tbps_mean |   total_net_rate_tbps_ci95 |   mean_gsnr_db_mean |   mean_gsnr_db_ci95 |   mean_ber_mean |   mean_ngmi_mean |
|-------------------:|:-----------------|---------------------------:|---------------------------:|--------------------:|--------------------:|----------------:|-----------------:|
|                 -6 | Neural NLI only  |                    2.13333 |                          0 |             23.2495 |            0.028979 |        0        |                1 |
|                 -6 | PCS only         |                    2.12935 |                          0 |             22.7807 |            0.036058 |        0        |                1 |
|                 -6 | PCS + Neural NLI |                    2.12935 |                          0 |             22.9816 |            0.03697  |        0        |                1 |
|                 -6 | Uniform baseline |                    2.13333 |                          0 |             23.0598 |            0.038217 |        0        |                1 |
|                 -4 | Neural NLI only  |                    2.13333 |                          0 |             23.1302 |            0.027553 |        0        |                1 |
|                 -4 | PCS only         |                    2.12935 |                          0 |             22.6584 |            0.036163 |        0        |                1 |
|                 -4 | PCS + Neural NLI |                    2.12935 |                          0 |             22.8754 |            0.037732 |        0        |                1 |
|                 -4 | Uniform baseline |                    2.13333 |                          0 |             22.9207 |            0.038147 |        0        |                1 |
|                 -2 | Neural NLI only  |                    2.13333 |                          0 |             22.8481 |            0.026782 |        0        |                1 |
|                 -2 | PCS only         |                    2.12935 |                          0 |             22.3613 |            0.0364   |        0        |                1 |
|                 -2 | PCS + Neural NLI |                    2.12935 |                          0 |             22.6343 |            0.048465 |        0        |                1 |
|                 -2 | Uniform baseline |                    2.13333 |                          0 |             22.585  |            0.037977 |        0        |                1 |
|                  0 | Neural NLI only  |                    2.13333 |                          0 |             22.2022 |            0.026986 |        0        |                1 |
|                  0 | PCS only         |                    2.12935 |                          0 |             21.6865 |            0.036811 |        0        |                1 |
|                  0 | PCS + Neural NLI |                    2.12935 |                          0 |             22.0555 |            0.046055 |        0        |                1 |
|                  0 | Uniform baseline |                    2.13333 |                          0 |             21.8344 |            0.037732 |        0        |                1 |
|                  2 | Neural NLI only  |                    2.13333 |                          0 |             20.9164 |            0.024299 |        0        |                1 |
|                  2 | PCS only         |                    2.12935 |                          0 |             20.3562 |            0.037161 |        0        |                1 |
|                  2 | PCS + Neural NLI |                    2.12935 |                          0 |             20.8737 |            0.050984 |        0        |                1 |
|                  2 | Uniform baseline |                    2.13333 |                          0 |             20.3929 |            0.037726 |        0        |                1 |
|                  4 | Neural NLI only  |                    2.13333 |                          0 |             18.7977 |            0.019558 |        0.00029  |                1 |
|                  4 | PCS only         |                    2.12935 |                          0 |             18.1978 |            0.037072 |        0.000165 |                1 |
|                  4 | PCS + Neural NLI |                    2.12935 |                          0 |             18.8702 |            0.056388 |        0.000135 |                1 |
|                  4 | Uniform baseline |                    2.13333 |                          0 |             18.1189 |            0.037956 |        0.0003   |                1 |