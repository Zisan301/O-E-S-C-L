# Day-10 external reference file

Day-10 can check the O-E-S-C-L SSFM-like GSNR values against an external reference file.

## Template

The script creates:

```text
validation_data/gnpy_day10_reference_template.csv
```

Copy it to:

```text
validation_data/gnpy_day10_reference.csv
```

Then fill `reference_gsnr_db`.

## Required columns

```text
scenario_group
band
spans
launch_power_dbm
reference_model
reference_gsnr_db
notes
```

## What to use as reference

Best option:
- GNPy output for the same band, span count, span length, launch power, attenuation, dispersion, and noise figure.

Acceptable fallback:
- GN or EGN analytical result, but label `reference_model` honestly as `GN` or `EGN`.

Do not label internal O-E-S-C-L sanity calculations as GNPy.

## Manuscript wording

If this file is missing:
- "An internal analytical GN-style sanity check was performed."
- Do not write "external GNPy validation."

If this file is present and RMSE is low:
- "Selected C and S operating points were compared with an external GNPy/GN/EGN reference, producing a GSNR RMSE of ... dB."
