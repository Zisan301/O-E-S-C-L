# O-E-S-C-L Day-2 IEEE/Optica Upgrade Patch

Day-2 is focused on finding a real operating region where the method becomes scientifically defendable.

## Added in Day-2

1. PCS shaping coefficient sweep:
   `nu = 0.00, 0.06, 0.12, 0.18, 0.24, 0.30`

2. Span-count sweep:
   `spans = 6, 8, 10, 12`

3. Launch-power stress sweep:
   `power = -2, 0, 2, 4, 6 dBm`

4. Three-seed repeated runs:
   `seeds = 1, 2, 3`

5. Best-operating-point finder:
   Finds the best span/power/nu point by combined rate, GSNR, and BER score.

6. Candidate neural-compensation test:
   Evaluates Neural-only and PCS+Neural at the best candidate points.

## Install

Extract this ZIP directly into your project root:

```text
E:\VS Code\O+E+S+C+L
```

Allow replace/merge when Windows asks.

## Run

```powershell
pip install -r requirements.txt
python main.py --config config/day2_ieee_optica_config.yaml --mode day2
```

Or:

```powershell
scripts\run_day2_ieee_optica.bat
```

## Expected output files

```text
results/reports/day2_ieee_optica_upgrade_report.md
results/reports/day2_latex_results_snippet.tex

results/tables/day2_best_operating_points.csv
results/tables/day2_all_ci.csv
results/tables/day2_pcs_sweep_ci.csv
results/tables/day2_neural_candidate_ci.csv

results/figures/fig_day2_pcs_nu_rate.png
results/figures/fig_day2_pcs_nu_ber.png
results/figures/fig_day2_best_nu_heatmap.png
results/figures/fig_day2_span_power_rate_surface.png
results/figures/fig_day2_neural_candidate_comparison.png
results/figures/fig_day2_final_tradeoff.png
```

## After running

Send these files back:

```text
results/reports/day2_ieee_optica_upgrade_report.md
results/tables/day2_best_operating_points.csv
results/tables/day2_all_ci.csv
```

Then the paper can be upgraded with a stronger Day-2 Results section.
