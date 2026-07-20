# O-E-S-C-L Day-1 IEEE/Optica Upgrade Patch

This patch starts the IEEE/Optica-level upgrade work.

## Day-1 tasks included

1. Adds a real system architecture diagram.
2. Adds launch-power sweep experiments.
3. Adds 5-seed repeated runs.
4. Adds mean ± 95% confidence interval aggregation.
5. Adds log-scale BER plotting.
6. Adds cleaner complexity/performance plot.
7. Adds band-wise GSNR heatmap.
8. Generates a LaTeX snippet for the improved Results section.

## How to install

Extract this ZIP directly into your project root:

```text
E:\VS Code\O+E+S+C+L
```

Allow Windows to replace existing files if asked.

## Run Day-1 upgrade

```powershell
pip install -r requirements.txt
python main.py --config config/day1_ieee_optica_config.yaml --mode day1
```

Or:

```powershell
scripts\run_day1_ieee_optica.bat
```

## Generated outputs

```text
results/tables/day1_channel_metrics.csv
results/tables/day1_seed_level_summary.csv
results/tables/day1_launch_power_ci.csv
results/reports/day1_ieee_optica_upgrade_report.md
results/reports/day1_latex_results_snippet.tex
results/figures/fig_day1_system_architecture.png
results/figures/fig_day1_launch_power_gsnr.png
results/figures/fig_day1_launch_power_ngmi.png
results/figures/fig_day1_launch_power_rate.png
results/figures/fig_day1_launch_power_ber_log.png
results/figures/fig_day1_complexity_clean.png
results/figures/fig_day1_bandwise_gsnr_heatmap.png
```

After running, send these two files back:

```text
results/reports/day1_ieee_optica_upgrade_report.md
results/tables/day1_launch_power_ci.csv
```
