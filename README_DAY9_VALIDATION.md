# O-E-S-C-L Day-9 Publication Validation Patch

This patch starts **Step 2** for strengthening the Springer/PNC manuscript.
It adds reviewer-facing validation outputs, not manuscript rewriting.

## What this patch adds

1. Raw per-seed accepted-point metrics.
2. Paired PCS-minus-uniform gains at the accepted C, S, and C+S points.
3. SSFM step-size convergence for the C and S accepted operating points.
4. Symbol-count convergence for the C and S accepted operating points.
5. Internal GN-style GSNR sanity benchmark for selected C and S powers.
6. External-reference template for later GNPy/GN/EGN comparison.
7. New validation figures and a LaTeX snippet for the paper.

## Important honesty note

The GN-style benchmark in this patch is **not GNPy**. It is an internal analytical sanity check.
For formal external validation, fill this generated file after running the script:

```text
results/tables/day9_external_reference_template.csv
```

with actual GNPy/GN/EGN reference values, save it as:

```text
validation_data/gnpy_day9_reference.csv
```

then rerun the Day-9 script.

## Install

Extract this ZIP into your project root:

```text
E:\VS Code\O+E+S+C+L
```

Allow merge/replace if Windows asks.

## Run

From the project root:

```powershell
python scripts\run_day9_publication_validation.py --config config\day9_validation_config.yaml
```

or double-click/run:

```powershell
scripts\run_day9_publication_validation.bat
```

## Expected outputs

After running, send these files back for manuscript integration:

```text
results/reports/day9_validation_report.md
results/reports/day9_latex_validation_snippet.tex
results/reports/day9_reviewer_evidence_checklist.md
results/tables/day9_raw_per_seed_selected.csv
results/tables/day9_raw_per_seed_paired_gains.csv
results/tables/day9_ssfm_step_convergence.csv
results/tables/day9_symbol_count_convergence.csv
results/tables/day9_gn_style_gsnr_benchmark.csv
results/tables/day9_external_reference_check.csv
results/figures/fig_day9_ssfm_step_convergence.png
results/figures/fig_day9_symbol_count_convergence.png
results/figures/fig_day9_gn_style_gsnr_comparison.png
results/figures/fig_day9_seed_gain_distribution.png
```

## How this improves the paper

The current manuscript already reports Day-8 C/S/C+S accepted gains, but reviewers can still ask whether the result depends on one numerical resolution or one random-seed average. Day-9 addresses this by exporting convergence and raw per-seed evidence.

Use the outputs to add a new paper subsection called:

```text
Additional Numerical Validation
```

Do not remove the C+S limitation. Keep saying that the C+S case is a simplified lumped inter-band penalty model until you add full Raman/ISRS validation.
