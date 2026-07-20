# O-E-S-C-L Day-6 PCS Confirmation Patch

Day-5B strict gate passed only for a PCS-centered claim:

- nonzero PCS improved exact GMI/rate in a non-saturated waveform operating region;
- memory neural did not beat DBP-like/raw/linear baselines;
- therefore Day-6 focuses only on confirming PCS.

## Locked region

```text
Band: C
Spans: 10
Launch power: 4 dBm/channel
Stress: evidence
Day-5B best PCS region: nu around 0.24
```

## What Day-6 adds

1. Focused PCS sweep around the winning region.
2. 7 seeds instead of 5.
3. 8192 symbols/seed.
4. Matched paired comparison:
   - same seed uniform raw vs PCS raw
5. Strict paired gain acceptance:
   - GMI gain must exceed threshold
   - NGMI gain must exceed threshold
   - rate gain must exceed threshold
   - gains must exceed paired 95% CI
   - BER must remain acceptable
   - operating point must be non-saturated
6. Memory neural check only at selected nu values:
   - 0.00, 0.20, 0.24, 0.28
   This confirms we are not claiming neural superiority.

## Install

Extract directly inside:

```text
E:\VS Code\O+E+S+C+L
```

Allow replace/merge.

## Run

```powershell
python main.py --config config/day6_pcs_confirmation_config.yaml --mode day6
```

or:

```powershell
scripts\run_day6_pcs_confirmation.bat
```

## Expected outputs

```text
results\reports\day6_pcs_confirmation_report.md
results\reports\day6_pcs_acceptance_gate_report.md
results\reports\day6_latex_results_snippet.tex

results\tables\day6_raw_metrics.csv
results\tables\day6_ci_metrics.csv
results\tables\day6_paired_pcs_gains.csv
results\tables\day6_acceptance_summary.csv

results\figures\fig_day6_pcs_gmi.png
results\figures\fig_day6_pcs_ngmi.png
results\figures\fig_day6_pcs_ber.png
results\figures\fig_day6_pcs_gmi_gain.png
results\figures\fig_day6_constellation_uniform_vs_pcs.png
```

## Send back after running

```text
results\reports\day6_pcs_confirmation_report.md
results\reports\day6_pcs_acceptance_gate_report.md
results\tables\day6_ci_metrics.csv
results\tables\day6_paired_pcs_gains.csv
results\tables\day6_acceptance_summary.csv
```

## How to judge

If Day-6 passes, the paper can be rewritten as a PCS-centered Optica regular-paper candidate.

Safe title direction:

```text
Waveform-Level SSFM Validation of Operating-Region Probabilistic Shaping Gains in Multi-Band O/E/S/C/L Optical Links
```

Do not claim neural superiority unless memory neural also beats the strong baselines.
