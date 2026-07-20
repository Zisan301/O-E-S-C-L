# O-E-S-C-L Day-4 Optica Scientific Upgrade Patch

Day-4 adds the scientific components needed to move toward high-level Optica competitiveness.

## Added

1. SSFM-lite split-step propagation:
   - dispersion phase
   - nonlinear phase
   - attenuation/lumped gain
   - ASE-like noise

2. Bit-metric AWGN-likelihood GMI/NGMI:
   - replaces the earlier Shannon-like proxy
   - computes bit-wise mutual information from LLRs

3. Stronger baselines:
   - raw received signal
   - linear equalizer
   - polynomial nonlinear compensator
   - DBP-like inverse nonlinear phase
   - neural residual compensation
   - PCS raw
   - PCS + neural

4. Multi-seed confidence intervals.

## Install

Extract this ZIP directly into your project root:

```text
E:\VS Code\O+E+S+C+L
```

Allow replace/merge.

## Run

```powershell
pip install -r requirements.txt
python main.py --config config/day4_optica_scientific_config.yaml --mode day4
```

Or:

```powershell
scripts\run_day4_optica_scientific.bat
```

## Expected outputs

```text
results/reports/day4_optica_scientific_upgrade_report.md
results/reports/day4_latex_results_snippet.tex
results/tables/day4_raw_metrics.csv
results/tables/day4_ci_metrics.csv
results/tables/day4_best_points.csv
results/figures/fig_day4_gmi_vs_power.png
results/figures/fig_day4_ngmi_vs_power.png
results/figures/fig_day4_ber_vs_power.png
results/figures/fig_day4_gsnr_vs_power.png
results/figures/fig_day4_rate_vs_power.png
results/figures/fig_day4_best_tradeoff.png
```

## After running

Send these files back:

```text
results/reports/day4_optica_scientific_upgrade_report.md
results/tables/day4_best_points.csv
results/tables/day4_ci_metrics.csv
```

Then the Optica paper can be rewritten around exact GMI/NGMI and stronger baselines.
