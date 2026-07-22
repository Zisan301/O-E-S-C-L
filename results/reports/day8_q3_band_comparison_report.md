# Day-8 Q3 C/S/C+S Band Comparison Report

This run upgrades the single C-band conference result into a comparative C, S, and C+S journal-style study.

## Acceptance summary

| scenario_group   | passes_q3_band_gate   |   best_pcs_nu |   spans |   launch_power_dbm |   gmi_gain_mean |   gmi_gain_ci95 |   ngmi_gain_mean |   ngmi_gain_ci95 |   rate_gain_mean |   rate_gain_ci95 |   aggregate_rate_gain_mean |   aggregate_rate_gain_ci95 |   ber_delta_mean |   ber_delta_ci95 | non_saturated   |
|:-----------------|:----------------------|--------------:|--------:|-------------------:|----------------:|----------------:|-----------------:|-----------------:|-----------------:|-----------------:|---------------------------:|---------------------------:|-----------------:|-----------------:|:----------------|
| C                | True                  |          0.36 |      10 |                  2 |        0.052577 |        0.01692  |         0.013144 |         0.00423  |         0.005608 |         0.001805 |                   0.005608 |                   0.001805 |        -0.003322 |         0.001217 | True            |
| C+S              | True                  |          0.36 |      12 |                  0 |        0.073238 |        0.011839 |         0.018309 |         0.00296  |         0.007812 |         0.001263 |                   0.015624 |                   0.002526 |        -0.005266 |         0.00068  | True            |
| S                | True                  |          0.36 |      12 |                 -2 |        0.068903 |        0.011213 |         0.017226 |         0.002803 |         0.00735  |         0.001196 |                   0.00735  |                   0.001196 |        -0.00456  |         0.000676 | True            |

## Best PCS gain by span

| scenario_group   |   spans |   best_pcs_nu |   best_launch_power_dbm |   best_gmi_gain |   best_rate_gain |   best_aggregate_rate_gain |
|:-----------------|--------:|--------------:|------------------------:|----------------:|-----------------:|---------------------------:|
| C                |       6 |          0.36 |                       4 |        0.046179 |         0.004926 |                   0.004926 |
| C                |       8 |          0.36 |                       2 |        0.047587 |         0.005076 |                   0.005076 |
| C                |      10 |          0.36 |                       2 |        0.052577 |         0.005608 |                   0.005608 |
| C                |      12 |          0.36 |                      -2 |        0.042717 |         0.004557 |                   0.004557 |
| C+S              |       6 |          0.36 |                       2 |        0.056188 |         0.005993 |                   0.011987 |
| C+S              |       8 |          0.32 |                       2 |        0.060734 |         0.006478 |                   0.012957 |
| C+S              |      10 |          0.32 |                       0 |        0.060742 |         0.006479 |                   0.012958 |
| C+S              |      12 |          0.36 |                       0 |        0.073238 |         0.007812 |                   0.015624 |
| S                |       6 |          0.32 |                       4 |        0.057728 |         0.006158 |                   0.006158 |
| S                |       8 |          0.36 |                       0 |        0.055667 |         0.005938 |                   0.005938 |
| S                |      10 |          0.32 |                       0 |        0.064921 |         0.006925 |                   0.006925 |
| S                |      12 |          0.36 |                      -2 |        0.068903 |         0.00735  |                   0.00735  |

## Figures
- `results\figures\fig_day8_gmi_vs_nu_c_s_cs.png`
- `results\figures\fig_day8_rate_gain_vs_nu.png`
- `results\figures\fig_day8_ber_vs_nu_c_s_cs.png`
- `results\figures\fig_day8_gain_heatmap_scenario_span.png`
- `results\figures\fig_day8_aggregate_rate_gain.png`

Important limitation: C+S uses a simplified lumped inter-band penalty, not full Raman-calibrated WDM.
