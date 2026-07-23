# Day-12 Matched GNPy Reference Report
Day-12 regenerates external GNPy GSNR values using a matched custom spectrum.
## Matching changes
- Baud rate: `64000000000.0` Hz
- Slot width / spacing: `75000000000.0` Hz
- C center wavelength: `1550.0` nm
- S center wavelength: `1490.0` nm
- C channels: `76`
- S channels: `76`

## Extracted receiver GSNR values
| band | spans | launch power (dBm) | GSNR signal bw (dB) | freq min THz | freq max THz | status |
|---|---:|---:|---:|---:|---:|---|
| C | 10 | -2 | 12.2200 | 190.60199 | 196.22699 | ok |
| C | 10 | 0 | 14.0300 | 190.60199 | 196.22699 | ok |
| C | 10 | 2 | 15.1300 | 190.60199 | 196.22699 | ok |
| C | 10 | 4 | 15.1300 | 190.60199 | 196.22699 | ok |
| S | 12 | -2 | 11.8000 | 198.39049 | 204.01549 | ok |
| S | 12 | 0 | 13.2400 | 198.39049 | 204.01549 | ok |
| S | 12 | 2 | 13.5000 | 198.39049 | 204.01549 | ok |
| S | 12 | 4 | 13.5000 | 198.39049 | 204.01549 | ok |

## Next step
Run Day-11 again after this script updates `validation_data/gnpy_day11_reference.csv`:

```powershell
python scripts\run_day11_external_validation.py --config config\day11_external_validation_config.yaml
```
