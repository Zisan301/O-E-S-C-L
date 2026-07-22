# Day-8 Q3 Acceptance Report

Passed scenarios: 3/3

Recommended claim: PCS gains are band- and operating-region-dependent; accepted scenarios can be used for a Q3 journal claim.

| scenario_group   | passes_q3_band_gate   |   best_pcs_nu |   spans |   launch_power_dbm |   gmi_gain_mean |   gmi_gain_ci95 |   ngmi_gain_mean |   ngmi_gain_ci95 |   rate_gain_mean |   rate_gain_ci95 |   aggregate_rate_gain_mean |   aggregate_rate_gain_ci95 |   ber_delta_mean |   ber_delta_ci95 | non_saturated   |
|:-----------------|:----------------------|--------------:|--------:|-------------------:|----------------:|----------------:|-----------------:|-----------------:|-----------------:|-----------------:|---------------------------:|---------------------------:|-----------------:|-----------------:|:----------------|
| C                | True                  |          0.36 |      10 |                  2 |        0.052577 |        0.01692  |         0.013144 |         0.00423  |         0.005608 |         0.001805 |                   0.005608 |                   0.001805 |        -0.003322 |         0.001217 | True            |
| C+S              | True                  |          0.36 |      12 |                  0 |        0.073238 |        0.011839 |         0.018309 |         0.00296  |         0.007812 |         0.001263 |                   0.015624 |                   0.002526 |        -0.005266 |         0.00068  | True            |
| S                | True                  |          0.36 |      12 |                 -2 |        0.068903 |        0.011213 |         0.017226 |         0.002803 |         0.00735  |         0.001196 |                   0.00735  |                   0.001196 |        -0.00456  |         0.000676 | True            |
