# O-E-S-C-L Day-5 Optica Evidence Patch

Day-5 targets the requirements needed for a high-level Optica regular-paper claim.

## Added

1. Waveform-level SSFM starter
   - RRC pulse shaping
   - oversampled waveform propagation
   - dispersion phase
   - nonlinear phase
   - ASE/implementation noise
   - receiver chromatic-dispersion compensation
   - matched filtering and downsampling

2. Memory-aware neural equalizer
   - uses neighboring received symbols
   - default 5-tap memory window
   - MLP equalizer with 64 and 32 hidden units

3. Strong baselines
   - Raw
   - Linear EQ
   - DBP-like inverse phase
   - Polynomial NLC
   - Memory neural EQ
   - PCS raw
   - PCS + Memory neural

4. Exact bit-metric GMI/NGMI
   - AWGN-likelihood LLR-based bit-metric GMI
   - BER, GSNR, estimated rate

5. Stress selector
   - avoids too-easy GMI=4/BER=0 saturation
   - avoids too-hard BER≈0.5 random decisions
   - chooses a useful operating region automatically

6. Acceptance gate
   - says whether the results support a high-level Optica performance claim
   - rejects the claim if neural does not beat raw/linear/DBP-like/polynomial baselines
   - separately checks whether nonzero PCS wins

## Install

Extract this ZIP directly inside:

```text
E:\VS Code\O+E+S+C+L
```

Allow replace/merge.

## Run

```powershell
pip install -r requirements.txt
python main.py --config config/day5_optica_evidence_config.yaml --mode day5
```

or:

```powershell
scripts\run_day5_optica_evidence.bat
```

## Expected outputs

```text
results\reports\day5_optica_evidence_report.md
results\reports\day5_acceptance_gate_report.md
results\reports\day5_latex_results_snippet.tex

results\tables\day5_sanity_tests.csv
results\tables\day5_stress_selector.csv
results\tables\day5_raw_metrics.csv
results\tables\day5_ci_metrics.csv
results\tables\day5_best_methods.csv
results\tables\day5_acceptance_summary.csv

results\figures\fig_day5_constellations.png
results\figures\fig_day5_gmi_vs_power.png
results\figures\fig_day5_ngmi_vs_power.png
results\figures\fig_day5_ber_vs_power.png
results\figures\fig_day5_pcs_gmi_sweep.png
results\figures\fig_day5_best_tradeoff.png
```

## Send back after running

```text
results\reports\day5_optica_evidence_report.md
results\reports\day5_acceptance_gate_report.md
results\tables\day5_sanity_tests.csv
results\tables\day5_stress_selector.csv
results\tables\day5_best_methods.csv
results\tables\day5_ci_metrics.csv
results\tables\day5_acceptance_summary.csv
```

## How to judge

A real high-level Optica claim is allowed only if one happens:

1. Memory neural EQ beats Raw, Linear EQ, DBP-like, and Polynomial NLC in GMI/NGMI/rate with acceptable BER.
2. Nonzero PCS improves exact GMI/rate in the selected waveform stress region.
3. The result exposes a strong negative finding that is novel and well validated.
