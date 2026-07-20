# Day-2 IEEE/Optica Upgrade Report

## What Day-2 adds

- PCS shaping-coefficient sweep.
- Span-count sweep.
- Stronger nonlinear/low-SNR stress conditions.
- Best-operating-point finder.
- Candidate neural-compensation evaluation at promising operating points.
- Paper-ready figures for rate, BER, span/power surface, and PCS tuning.

## Key Day-2 findings

- Best proposed operating point by score: spans=6, launch power=-2.0 dBm, PCS nu=0.00.
- Proposed rate there: **6.4000 ± 0.0000 Tb/s**.
- Proposed GSNR there: **21.823 ± 0.081 dB**.
- Proposed BER there: **7.937e-06**.
- Best proposed rate point: **6.4000 ± 0.0000 Tb/s**, spans=6, power=-2.0 dBm, nu=0.00.

## Best operating points table

| scenario            | display_name     | selection   |   spans |   launch_power_dbm |   pcs_nu |   rate_mean_tbps |   rate_ci95_tbps |   gsnr_mean_db |   gsnr_ci95_db |   ber_mean |   ngmi_mean |   score_mean |
|:--------------------|:-----------------|:------------|--------:|-------------------:|---------:|-----------------:|-----------------:|---------------:|---------------:|-----------:|------------:|-------------:|
| neural_only         | Neural NLI only  | best_rate   |       6 |                 -2 |        0 |              6.4 |                0 |        21.7424 |       0.078701 |      1e-05 |           1 |      1.29622 |
| neural_only         | Neural NLI only  | best_gsnr   |       6 |                 -2 |        0 |              6.4 |                0 |        21.7424 |       0.078701 |      1e-05 |           1 |      1.29622 |
| neural_only         | Neural NLI only  | best_score  |       6 |                 -2 |        0 |              6.4 |                0 |        21.7424 |       0.078701 |      1e-05 |           1 |      1.29622 |
| pcs_only            | PCS only         | best_rate   |       6 |                 -2 |        0 |              6.4 |                0 |        19.9836 |       0.003559 |      2e-06 |           1 |      1.22599 |
| pcs_only            | PCS only         | best_gsnr   |       6 |                 -2 |        0 |              6.4 |                0 |        19.9836 |       0.003559 |      2e-06 |           1 |      1.22599 |
| pcs_only            | PCS only         | best_score  |       6 |                 -2 |        0 |              6.4 |                0 |        19.9836 |       0.003559 |      2e-06 |           1 |      1.22599 |
| proposed_pcs_neural | PCS + Neural NLI | best_rate   |       6 |                 -2 |        0 |              6.4 |                0 |        21.8235 |       0.080521 |      8e-06 |           1 |      1.29949 |
| proposed_pcs_neural | PCS + Neural NLI | best_gsnr   |       6 |                 -2 |        0 |              6.4 |                0 |        21.8235 |       0.080521 |      8e-06 |           1 |      1.29949 |
| proposed_pcs_neural | PCS + Neural NLI | best_score  |       6 |                 -2 |        0 |              6.4 |                0 |        21.8235 |       0.080521 |      8e-06 |           1 |      1.29949 |
| uniform_baseline    | Uniform baseline | best_rate   |       6 |                 -2 |        0 |              6.4 |                0 |        19.8893 |       0.003563 |      3e-06 |           1 |      1.22219 |
| uniform_baseline    | Uniform baseline | best_gsnr   |       6 |                 -2 |        0 |              6.4 |                0 |        19.8893 |       0.003563 |      3e-06 |           1 |      1.22219 |
| uniform_baseline    | Uniform baseline | best_score  |       6 |                 -2 |        0 |              6.4 |                0 |        19.8893 |       0.003563 |      3e-06 |           1 |      1.22219 |

## Submission-safe interpretation

Day-2 should be used to decide whether the paper can claim a genuine operating-region advantage. If PCS + Neural NLI still does not improve rate, the manuscript should be reframed as an ablation-driven validation study showing where PCS hurts, where neural compensation helps, and why tuning is necessary.

## Generated figures

- `results\figures\fig_day2_pcs_nu_rate.png`
- `results\figures\fig_day2_pcs_nu_ber.png`
- `results\figures\fig_day2_best_nu_heatmap.png`
- `results\figures\fig_day2_span_power_rate_surface.png`
- `results\figures\fig_day2_neural_candidate_comparison.png`
- `results\figures\fig_day2_final_tradeoff.png`

## Files to send back for paper rewrite

- `results/reports/day2_ieee_optica_upgrade_report.md`
- `results/tables/day2_best_operating_points.csv`
- `results/tables/day2_all_ci.csv`