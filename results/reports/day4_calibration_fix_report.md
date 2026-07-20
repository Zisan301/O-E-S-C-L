# Day-4 Calibration/Fix Report

## Purpose

The previous Day-4 SSFM-lite run over-degraded the signal, producing BER near 0.47 and NGMI near zero. This calibration run verifies basic channel behavior before using SSFM-lite results in the paper.

## Sanity tests

| test                   |   gmi |   ngmi |   ber |   gsnr_db |   rate_tbps |
|:-----------------------|------:|-------:|------:|----------:|------------:|
| identity_no_impairment |     4 |      1 |     0 |   47.9065 |    0.426667 |
| linear_dispersion_only |     4 |      1 |     0 |   47.9065 |    0.426667 |
| nonlinear_only         |     4 |      1 |     0 |   44.3625 |    0.426667 |
| calibrated_easy        |     4 |      1 |     0 |   26.9802 |    0.426667 |

## Pass/fail guidance

- Identity/no-impairment sanity test: **PASS**
- Easy-regime calibration: **PASS**

## Generated figures
- `results\figures\fig_day4_cal_constellations.png`
- `results\figures\fig_day4_cal_sanity_ber.png`
- `results\figures\fig_day4_cal_gmi_vs_power.png`
- `results\figures\fig_day4_cal_ngmi_vs_power.png`
- `results\figures\fig_day4_cal_ber_vs_power.png`
- `results\figures\fig_day4_cal_best_tradeoff.png`