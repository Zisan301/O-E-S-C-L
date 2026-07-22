# O-E-S-C-L Day-8 Q3 Journal Upgrade Patch

This patch upgrades the single C-band conference result into a Q3-style comparative study:

- C band only
- S band only
- combined C+S

It runs PCS sweeps across spans, launch powers, seeds, and shaping coefficients, then writes journal-ready CSV tables, figures, acceptance reports, and a LaTeX results snippet.

## Important C+S modeling note

The C+S case uses a simplified lumped inter-band penalty. It is not a full Raman-calibrated WDM/ISRS model. In the Q3 paper, state this honestly.

## Install

Extract this ZIP directly inside:

```text
E:\VS Code\O+E+S+C+L
```

Allow replace/merge.

## Run

```powershell
python main.py --config config/day8_q3_band_comparison_config.yaml --mode day8
```

or:

```powershell
scripts\run_day8_q3_band_comparison.bat
```

## Send back after running

```text
results/reports/day8_q3_band_comparison_report.md
results/reports/day8_q3_acceptance_report.md
results/tables/day8_acceptance_summary.csv
results/tables/day8_paired_pcs_gains.csv
results/tables/day8_ci_metrics.csv
results/tables/day8_best_gain_by_span.csv
```

## How to judge

For Q3 journal readiness, at least two of three scenarios should pass:

```text
C
S
C+S
```

If only one passes, the paper can still be written as band-dependent evidence, but not as a broad C/S/C+S improvement claim.
