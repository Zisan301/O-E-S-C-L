# Day-16 Full Raman/ISRS-Aware C+S Validation Report

## Reference type

- Reference type: `gnpy_full_raman_isrs`
- Interpretation: combined C+S GNPy reference with Raman/ISRS-aware simulation settings.

## Summary gate

- Full C+S Raman/ISRS calibrated held-out gate passed: `True`
- Held-out RMSE: `0.2549 dB`
- Held-out MAE: `0.2156 dB`
- Held-out max absolute error: `0.3516 dB`
- LOPO gate passed: `True`
- LOPO RMSE: `0.2988 dB`
- Overall status: `passed`

## Calibration model

```text
G_calibrated_CS_full_Raman(P) = G_OESC_CS(P) + a_CS + b_CS * P
```

- intercept a_CS: `0.5904 dB`
- slope b_CS: `1.1885 dB/dBm`
- calibration powers: `[-2, 0]`
- held-out validation powers: `[2, 4]`

## Correct manuscript claim

If this report passed, the manuscript may state calibrated C+S validation against a combined Raman/ISRS-aware GNPy reference. It should still mention calibration and should not describe the raw uncalibrated C+S result as direct agreement.
