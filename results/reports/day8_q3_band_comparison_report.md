# Day-8 Q3 C/S/C+S Band Comparison Report

This run upgrades the single C-band conference result into a comparative C, S, and C+S journal-style study. It reports entropy-aware BMD-GMI/NGMI and achievable information rate (AIR). The legacy rate columns are kept only as AIR aliases for backward compatibility; no FEC, DM, pilot, or framing overhead is modeled.

## Acceptance summary

| scenario_group   | passes_q3_band_gate   |   best_pcs_nu |   spans |   launch_power_dbm |   gmi_gain_mean |   gmi_gain_ci95 |   ngmi_gain_mean |   ngmi_gain_ci95 |   air_gain_mean |   air_gain_ci95 |   aggregate_air_gain_mean |   aggregate_air_gain_ci95 |   rate_gain_mean |   rate_gain_ci95 |   aggregate_rate_gain_mean |   aggregate_rate_gain_ci95 |   ber_delta_mean |   ber_delta_ci95 |   symbol_entropy_delta_mean |   symbol_entropy_delta_ci95 | non_saturated   |
|:-----------------|:----------------------|--------------:|--------:|-------------------:|----------------:|----------------:|-----------------:|-----------------:|----------------:|----------------:|--------------------------:|--------------------------:|-----------------:|-----------------:|---------------------------:|---------------------------:|-----------------:|-----------------:|----------------------------:|----------------------------:|:----------------|
| C                | True                  |          0.24 |      10 |                  2 |        0.035792 |        0.013807 |         0.012257 |         0.003452 |        0.004581 |        0.001767 |                  0.004581 |                  0.001767 |         0.004581 |         0.001767 |                   0.004581 |                   0.001767 |        -0.003169 |         0.001066 |                   -0.013235 |                           0 | True            |
| C+S              | True                  |          0.36 |      12 |                  0 |        0.043629 |        0.011839 |         0.018309 |         0.00296  |        0.005585 |        0.001515 |                  0.011169 |                  0.003031 |         0.005585 |         0.001515 |                   0.011169 |                   0.003031 |        -0.005266 |         0.00068  |                   -0.029608 |                           0 | True            |
| S                | True                  |          0.32 |      12 |                  2 |        0.044758 |        0.019074 |         0.017051 |         0.004768 |        0.005729 |        0.002441 |                  0.005729 |                  0.002441 |         0.005729 |         0.002441 |                   0.005729 |                   0.002441 |        -0.006134 |         0.001346 |                   -0.023445 |                           0 | True            |

## Best PCS gain by span

| scenario_group   |   spans |   best_pcs_nu |   best_launch_power_dbm |   best_gmi_gain |   best_air_gain |   best_aggregate_air_gain |   best_rate_gain |   best_aggregate_rate_gain |
|:-----------------|--------:|--------------:|------------------------:|----------------:|----------------:|--------------------------:|-----------------:|---------------------------:|
| C                |       6 |          0.24 |                       4 |        0.025744 |        0.003295 |                  0.003295 |         0.003295 |                   0.003295 |
| C                |       8 |          0.16 |                       4 |        0.025843 |        0.003308 |                  0.003308 |         0.003308 |                   0.003308 |
| C                |      10 |          0.24 |                       2 |        0.035792 |        0.004581 |                  0.004581 |         0.004581 |                   0.004581 |
| C                |      12 |          0.2  |                      -2 |        0.027134 |        0.003473 |                  0.003473 |         0.003473 |                   0.003473 |
| C+S              |       6 |          0.24 |                       4 |        0.034302 |        0.004391 |                  0.008781 |         0.004391 |                   0.008781 |
| C+S              |       8 |          0.32 |                       2 |        0.03729  |        0.004773 |                  0.009546 |         0.004773 |                   0.009546 |
| C+S              |      10 |          0.2  |                       0 |        0.037824 |        0.004842 |                  0.009683 |         0.004842 |                   0.009683 |
| C+S              |      12 |          0.36 |                       0 |        0.043629 |        0.005585 |                  0.011169 |         0.005585 |                   0.011169 |
| S                |       6 |          0.24 |                       6 |        0.037038 |        0.004741 |                  0.004741 |         0.004741 |                   0.004741 |
| S                |       8 |          0.28 |                       0 |        0.035516 |        0.004546 |                  0.004546 |         0.004546 |                   0.004546 |
| S                |      10 |          0.32 |                       0 |        0.041476 |        0.005309 |                  0.005309 |         0.005309 |                   0.005309 |
| S                |      12 |          0.32 |                       2 |        0.044758 |        0.005729 |                  0.005729 |         0.005729 |                   0.005729 |

## Figures
- `results\figures\fig_day8_gmi_vs_nu_c_s_cs.png`
- `results\figures\fig_day8_air_gain_vs_nu.png`
- `results\figures\fig_day8_ber_vs_nu_c_s_cs.png`
- `results\figures\fig_day8_gain_heatmap_scenario_span.png`
- `results\figures\fig_day8_aggregate_air_gain.png`

Important limitation: C+S uses a simplified lumped inter-band penalty, not full Raman-calibrated WDM.
