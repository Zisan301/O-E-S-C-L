# Day-12 Matched GNPy Reference Patch

Day-11 failed because the first GNPy reference was not fully matched to the O-E-S-C-L study. The main mismatch was that GNPy was still using its default-like channel setup: 50 GHz spacing, C-band-like frequencies, and default fiber/transceiver settings. Day-12 generates matched GNPy reference inputs.

## What this patch does

It creates and runs:

- `validation_data/gnpy_day12_matched_equipment.json`
- `validation_data/gnpy_C_10span_day12_network.json`
- `validation_data/gnpy_S_12span_day12_network.json`
- `validation_data/gnpy_C_day12_spectrum.json`
- `validation_data/gnpy_S_day12_spectrum.json`

Then it runs 8 GNPy cases:

- C band, 10 spans, -2/0/2/4 dBm
- S band, 12 spans, -2/0/2/4 dBm

It extracts receiver:

```text
Transceiver trx_B
GSNR (signal bw, dB)
```

and updates:

```text
validation_data/gnpy_day11_reference.csv
```

## Why this is needed

Your Day-11 report loaded all 8 GNPy values, but the gate still failed because RMSE was too high. That means GNPy and O-E-S-C-L were not aligned enough for a formal validation claim.

## Run

Activate the same `gnpy_env`, then run from the project root:

```powershell
cd "E:\VS Code\O+E+S+C+L"
.\gnpy_env\Scripts\activate
python scripts\run_day12_matched_gnpy_reference.py --config config\day12_matched_gnpy_reference_config.yaml
```

Then rerun Day-11:

```powershell
python scripts\run_day11_external_validation.py --config config\day11_external_validation_config.yaml
```

Send these files after rerun:

```text
results/reports/day12_matched_gnpy_reference_report.md
results/tables/day12_gnpy_reference_values.csv
results/reports/day11_external_validation_report.md
results/tables/day11_external_validation_errors.csv
results/figures/fig_day11_external_gsnr_comparison.png
results/figures/fig_day11_external_gsnr_error.png
```

## Important

If Day-12 still does not pass, do not force the values. The correct next step would be model-alignment: inspect amplifier NF, effective area, nonlinear coefficient, fiber dispersion, channel loading, and GNPy/O-E-S-C-L GSNR bandwidth conventions.
