# Day-4 receiver dispersion compensation fix

Your calibrated run showed:

- identity/no-impairment: PASS
- nonlinear-only: PASS
- linear-dispersion-only: BER around 0.074

That means the transmitter/channel is okay, but the receiver was not compensating chromatic dispersion.
This patch adds receiver-side dispersion compensation to `ssfm_calibrated.py`.

## Install

Extract this ZIP directly inside:

```text
E:\VS Code\O+E+S+C+L
```

Allow replace/merge.

## Run again

```powershell
python main.py --config config/day4_calibrated_config.yaml --mode day4cal
```

## Send back

```text
results\reports\day4_calibration_fix_report.md
results\reports\day4_calibrated_comparison_report.md
results\tables\day4_calibration_sanity.csv
results\tables\day4_calibrated_best_methods.csv
results\tables\day4_calibrated_pcs_ci.csv
```

## Expected improvement

The `linear_dispersion_only` sanity test should improve strongly.
If it does, then we can finally use calibrated Day-4 results for the Optica paper rewrite.
