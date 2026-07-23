# Filling the Day-11 GNPy/GN/EGN reference file

The file `gnpy_day11_reference_template.csv` contains the cases that Day-11 will compare.

## Required columns

- `scenario_group`: use `C` or `S`
- `band`: use `C` or `S`
- `spans`: number of 80 km spans
- `launch_power_dbm`: launch power per channel
- `reference_model`: write `GNPy`, `GN`, `EGN`, or another trusted source
- `reference_source`: write the simulator/version, script name, paper, or supervisor-provided source
- `reference_gsnr_db`: the external reference GSNR in dB
- `notes`: optional comment

## Why PCS is not required in the external reference

GNPy/GN/EGN reference validation normally checks physical-layer quality such as GSNR for a uniform channel. PCS gain is then evaluated inside O-E-S-C-L through paired uniform-vs-PCS waveform simulations. This is acceptable if written carefully:

1. External reference validates the physical-channel quality scale.
2. O-E-S-C-L paired simulations validate PCS gain under that channel model.
3. C+S remains a simplified stress scenario unless a full Raman/ISRS reference is supplied.

## Do not fake values

If you do not have real GNPy/GN/EGN values, leave `reference_gsnr_db` blank. The script will fail honestly, which is better than publishing unsupported validation.
