# Day-15 C+S GNPy-Calibrated Validation Patch

Day-15 extends the calibrated-validation workflow to the simplified C+S scenario.

Important interpretation:

- If no true Raman/ISRS-aware C+S GNPy reference is supplied, the script derives a **separable C+S baseline** from the matched Day-12 single-band C and S GNPy references.
- That derived reference is useful for transparent calibrated-alignment evidence, but it is **not** a full Raman/ISRS-aware multiband C+S validation.
- A full C+S physical validation requires a true multiband/Raman/ISRS-aware reference file at `validation_data/gnpy_day15_cs_reference.csv`.

Run:

```powershell
python scripts\run_day15_cs_gnpy_calibrated_validation.py --config config\day15_cs_gnpy_calibrated_validation_config.yaml
```

If packages are missing:

```powershell
pip install pyyaml pandas numpy matplotlib
```

Send these outputs after running:

```text
results/reports/day15_cs_gnpy_calibrated_validation_report.md
results/tables/day15_cs_protocol_summary.csv
results/tables/day15_cs_primary_holdout_predictions.csv
results/tables/day15_cs_external_reference.csv
results/figures/fig_day15_cs_uncalibrated_vs_calibrated_errors.png
results/figures/fig_day15_cs_correction_vs_power.png
results/figures/fig_day15_cs_lopo_errors.png
```
