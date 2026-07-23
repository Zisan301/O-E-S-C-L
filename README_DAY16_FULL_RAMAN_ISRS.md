# Day-16 Full Raman/ISRS-Aware C+S Validation Patch

Day-16 is different from Day-15. Day-15 used a derived separable C/S baseline. Day-16 prepares a true C+S reference workflow with a combined C+S spectrum and Raman/ISRS-aware GNPy simulation parameters.

Run from the project root:

```powershell
python scripts\run_day16_cs_full_raman_isrs_validation.py --config config\day16_cs_full_raman_isrs_config.yaml --prepare
```

Then run the generated GNPy commands:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_day16_gnpy_cs_raman_cases.ps1
```

Then parse the GNPy logs and run validation:

```powershell
python scripts\run_day16_cs_full_raman_isrs_validation.py --config config\day16_cs_full_raman_isrs_config.yaml --parse-logs
python scripts\run_day16_cs_full_raman_isrs_validation.py --config config\day16_cs_full_raman_isrs_config.yaml
```

If GNPy rejects the RamanFiber topology, switch the config key `gnpy.use_network` from `raman` to `regular_fallback` and rerun the prepare step. That fallback is not as strong as the RamanFiber topology, so mention the exact topology used in the paper.

Final claim is allowed only if the report says `reference_type = gnpy_full_raman_isrs` and the validation gates pass.
