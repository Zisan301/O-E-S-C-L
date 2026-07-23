# O-E-S-C-L Day-10 Publication Validation Patch

This patch is the next step after Day-9. It focuses on the two remaining reviewer risks:

1. Symbol-count convergence was not stable enough in Day-9.
2. External GNPy/GN/EGN validation was missing.

Day-10 is intentionally conservative. It treats the C and S single-band cases as the main publication-strength validation cases. The C+S case may be included as an optional stress scenario, but it should still be described as a simplified lumped inter-band penalty case unless a full Raman/ISRS reference is added.

## Files added

```text
config/day10_validation_config.yaml
scripts/run_day10_publication_validation.py
scripts/run_day10_publication_validation.bat
validation_data/gnpy_day10_reference_template.csv
validation_data/README_day10_external_reference.md
manuscript/day10_validation_section_template.tex
docs/DAY10_README.md
```

## How to install

Extract this ZIP inside your O-E-S-C-L project root:

```text
E:\VS Code\O+E+S+C+L
```

Allow Windows to merge folders.

## Main run

```powershell
python scripts\run_day10_publication_validation.py --config config\day10_validation_config.yaml
```

or:

```powershell
scripts\run_day10_publication_validation.bat
```

## What Day-10 produces

```text
results/reports/day10_publication_validation_report.md
results/tables/day10_symbol_count_convergence.csv
results/tables/day10_symbol_count_stability_summary.csv
results/tables/day10_raw_per_seed_metrics.csv
results/tables/day10_raw_per_seed_paired_gains.csv
results/tables/day10_internal_gn_reference.csv
results/tables/day10_external_reference_check.csv
results/figures/fig_day10_symbol_count_convergence.png
results/figures/fig_day10_symbol_count_relative_error.png
results/figures/fig_day10_seed_gain_distribution.png
results/figures/fig_day10_gn_reference_comparison.png
results/reports/day10_validation_latex_snippet.tex
```

## External reference workflow

The script always creates an external reference template:

```text
validation_data/gnpy_day10_reference_template.csv
```

To add true external validation, copy it to:

```text
validation_data/gnpy_day10_reference.csv
```

Then fill the `reference_gsnr_db` column using GNPy, GN, EGN, or another clearly named external/analytical reference.

Then rerun:

```powershell
python scripts\run_day10_publication_validation.py --config config\day10_validation_config.yaml
```

If that file is missing, Day-10 will still produce internal analytical GN-style sanity plots, but the paper must not call them formal external validation.

## Pass criteria

The default Day-10 gate is:

- C and S must pass symbol-count stability.
- Stability is judged between the two largest symbol counts.
- Absolute GMI-gain drift must be <= 0.010.
- Relative GMI-gain drift must be <= 20%.
- External validation passes only if `validation_data/gnpy_day10_reference.csv` exists and GSNR RMSE is <= 1.0 dB.

You can edit thresholds inside `config/day10_validation_config.yaml`.
