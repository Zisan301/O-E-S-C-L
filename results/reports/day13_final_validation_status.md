# Day-13 Final Validation Status

## Summary

The Day-10 to Day-13 validation sequence strengthens the C-band publication evidence.

## Results

### Day-10: Larger-symbol C-band stability

- C-band stronger stability rerun passed.
- Largest symbol count: 65,536
- Seeds: 10
- High-count GMI gain: 0.0209167
- Absolute GMI-gain drift: 0.0002379
- Relative GMI-gain drift: 0.011375

### Day-11: Raw GNPy reference check

- Independent GNPy reference was generated for the C-band 10-span case.
- GNPy reference GSNR: 18.780000 dB
- O-E-S-C-L uniform GSNR: 12.863055 dB
- Raw error: -5.916945 dB
- Raw external gate did not pass.

### Day-12: Multi-span external alignment sweep

- C-band span counts tested: 6, 8, 10, 12
- Mean O-E-S-C-L minus GNPy offset: -6.152843 dB
- Offset standard deviation: 0.328463 dB
- Error-vs-span slope: 0.104764 dB/span
- Decision: mostly constant conservative offset.

### Day-13: Offset-calibration diagnostic

- Constant offset applied to O-E-S-C-L GSNR: +6.152843 dB
- Calibrated RMSE: 0.284458 dB
- Calibrated MAE: 0.240163 dB
- Calibrated max absolute error: 0.480325 dB
- Leave-one-out RMSE: 0.379277 dB
- Diagnostic offset calibration passed: True

## Correct manuscript claim

The manuscript must not claim raw absolute GNPy validation.

The correct claim is:

O-E-S-C-L C-band PCS gains are supported by repeated-seed larger-symbol convergence. An independent multi-span GNPy comparison showed that the raw O-E-S-C-L absolute GSNR scale is conservatively shifted relative to GNPy by an approximately constant offset. After applying one constant external offset, the calibrated C-band GSNR trend aligned with GNPy with sub-dB error, including a leave-one-out RMSE below 0.4 dB. Therefore, the external result is reported as a calibration diagnostic, while the main validated claim remains PCS gain stability and trend consistency.

## Submission decision

This evidence is suitable for a careful Q3/conference-style manuscript claim.

For a stronger journal claim, future work should physically tune the absolute GSNR scale so that raw GNPy validation passes without applying an offset.
