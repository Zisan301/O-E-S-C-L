# O-E-S-C-L Day-5B Strict Optica Evidence Patch

Day-5 v1 produced a "pass", but it was too weak for a real high-level Optica claim:

- memory neural did not beat raw/linear/DBP-like/polynomial baselines;
- the best PCS gain was very small;
- the selected stress point was not inside the target non-saturated region;
- many results were still close to GMI saturation.

This Day-5B patch makes the evidence gate stricter.

## What changes

1. Stronger stress grid to avoid saturation.
2. Strict target region:
   - GMI 2.60 to 3.80
   - NGMI 0.65 to 0.96
   - BER 1e-4 to 8e-2
3. More seeds:
   - 5 seeds instead of 3
4. Larger memory neural equalizer:
   - 7 memory taps
   - 96 and 48 hidden units
5. Strict acceptance gate:
   - improvement must exceed configured threshold
   - improvement must exceed combined 95% CI
   - operating point must be non-saturated
   - matched PCS-vs-uniform comparison is used where possible

## Install

Extract directly inside:

```text
E:\VS Code\O+E+S+C+L
```

Allow replace/merge.

## Run

```powershell
python main.py --config config/day5_optica_evidence_config.yaml --mode day5
```

or:

```powershell
scripts\run_day5b_strict_optica_evidence.bat
```

## Important runtime note

This is heavier than Day-5 v1. If it is too slow, edit:

```yaml
seeds: [1, 2, 3]
symbols: 4096
memory_hidden_layers: [64, 32]
memory_max_iter: 160
```

## Send back

```text
results/reports/day5_optica_evidence_report.md
results/reports/day5_acceptance_gate_report.md
results/tables/day5_sanity_tests.csv
results/tables/day5_stress_selector.csv
results/tables/day5_best_methods.csv
results/tables/day5_ci_metrics.csv
results/tables/day5_acceptance_summary.csv
```

## How to judge

Only rewrite the Optica regular paper if the strict gate passes.
If the strict gate fails, the honest high-level direction becomes a validation/negative-result paper, not a performance-superiority paper.
