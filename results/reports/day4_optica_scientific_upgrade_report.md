# Day-4 Optica Scientific Upgrade Report

## What Day-4 adds

- SSFM-lite split-step propagation instead of only analytical noise screening.
- Bit-metric AWGN-likelihood GMI/NGMI estimate instead of Shannon-like proxy.
- Stronger baselines: Linear EQ, Polynomial NLC, DBP-like compensation, Neural residual compensation.
- Multi-seed confidence intervals.

## Best overall operating point

- Scenario: **PCS + Neural**
- Spans: **6**
- Launch power: **2.0 dBm/channel**
- Band: **C**
- PCS nu: **0.24**
- GMI: **0.003 ± 0.001 bits/symbol**
- NGMI: **0.001 ± 0.000**
- BER: **4.668e-01**
- GSNR: **0.006 ± 0.013 dB**
- Estimated rate: **0.0003 ± 0.0001 Tb/s per evaluated channel**

## Best point by scenario

|   spans |   launch_power_dbm | band   |   pcs_nu | scenario        | display_name    |   n_seeds |   gmi_mean |   gmi_std |   gmi_ci95 |   ngmi_mean |   ngmi_std |   ngmi_ci95 |   ber_mean |   ber_std |   ber_ci95 |   gsnr_db_mean |   gsnr_db_std |   gsnr_db_ci95 |   rate_tbps_mean |   rate_tbps_std |   rate_tbps_ci95 |   score_mean |   score_std |   score_ci95 |
|--------:|-------------------:|:-------|---------:|:----------------|:----------------|----------:|-----------:|----------:|-----------:|------------:|-----------:|------------:|-----------:|----------:|-----------:|---------------:|--------------:|---------------:|-----------------:|----------------:|-----------------:|-------------:|------------:|-------------:|
|       6 |                  2 | C      |     0.24 | pcs_neural      | PCS + Neural    |         3 |   0.003257 |  0.000987 |   0.001116 |    0.000814 |   0.000247 |    0.000279 |   0.466838 |  0.001587 |   0.001796 |       0.005789 |      0.011558 |       0.01308  |         0.000347 |        0.000105 |         0.000119 |     -9.33611 |    0.031553 |     0.035706 |
|       6 |                  2 | C      |     0.24 | pcs_raw         | PCS raw         |         3 |   0.019317 |  0.004257 |   0.004818 |    0.004829 |   0.001064 |    0.001204 |   0.462118 |  0.002766 |   0.00313  |      -3.16223  |      0.041872 |       0.047383 |         0.00206  |        0.000454 |         0.000514 |     -9.3984  |    0.056965 |     0.064462 |
|       6 |                  2 | C      |     0    | uniform_raw     | Uniform raw     |         3 |   0.004139 |  0.002152 |   0.002436 |    0.001035 |   0.000538 |    0.000609 |   0.467712 |  0.004059 |   0.004593 |      -2.97377  |      0.036997 |       0.041867 |         0.000441 |        0.00023  |         0.00026  |     -9.50249 |    0.083215 |     0.094167 |
|       6 |                  2 | C      |     0    | dbp_like        | DBP-like        |         3 |   0.003952 |  0.001982 |   0.002243 |    0.000988 |   0.000496 |    0.000561 |   0.468974 |  0.003673 |   0.004157 |      -2.97351  |      0.035986 |       0.040722 |         0.000422 |        0.000211 |         0.000239 |     -9.52773 |    0.075311 |     0.085223 |
|       8 |                  2 | S      |     0    | poly_nlc        | Polynomial NLC  |         3 |   0.003515 |  0.00194  |   0.002196 |    0.000879 |   0.000485 |    0.000549 |   0.489054 |  0.0026   |   0.002942 |       0.005566 |      0.009024 |       0.010211 |         0.000375 |        0.000207 |         0.000234 |     -9.78043 |    0.05264  |     0.059568 |
|       6 |                  4 | L      |     0    | neural_residual | Neural residual |         3 |   0.003434 |  0.002917 |   0.003301 |    0.000858 |   0.000729 |    0.000825 |   0.492839 |  0.000672 |   0.000761 |       0.000887 |      0.023495 |       0.026587 |         0.000366 |        0.000311 |         0.000352 |     -9.85636 |    0.012014 |     0.013595 |
|       8 |                  4 | S      |     0    | linear_eq       | Linear EQ       |         3 |   0.000328 |  0.000323 |   0.000365 |    8.2e-05  |   8.1e-05  |    9.1e-05  |   0.498332 |  0.000813 |   0.00092  |       0.000561 |      0.001888 |       0.002136 |         3.5e-05  |        3.4e-05  |         3.9e-05  |     -9.96657 |    0.016135 |     0.018258 |

## Generated figures

- `results\figures\fig_day4_gmi_vs_power.png`
- `results\figures\fig_day4_ngmi_vs_power.png`
- `results\figures\fig_day4_ber_vs_power.png`
- `results\figures\fig_day4_gsnr_vs_power.png`
- `results\figures\fig_day4_rate_vs_power.png`
- `results\figures\fig_day4_best_tradeoff.png`

## Honest Optica-readiness interpretation

If Neural residual or DBP-like compensation improves exact bit-metric GMI or NGMI over raw/linear baselines, the paper can be reframed around nonlinear-residual compensation. If PCS still selects nu=0 or loses rate, do not claim PCS gain. A high-level Optica regular submission still benefits from a fuller SSFM implementation with pulse shaping, WDM coupling, more seeds, and larger symbol counts.