# Novelty, Baselines and Validation Plan for PNC Submission

This document closes three major reviewer-facing gaps:

1. clarify the novelty;
2. define the baseline comparisons;
3. define the broader independent validation matrix.

## 1. Final paper identity

The manuscript should be framed as:

A calibrated surrogate framework for probabilistic constellation shaping trend evaluation in coherent optical link scenarios.

The manuscript should not be framed as:

- a fully physical Manakov/NLSE split-step Fourier simulator;
- a raw GNPy-validated transmission simulator;
- an experimentally validated optical transmission system;
- a final field-ready deployment model.

## 2. Core novelty

The novelty is not merely combining PCS, neural mitigation and multiband simulation.

The safer novelty is:

1. A reproducible calibrated surrogate workflow for PCS trend evaluation.
2. Explicit separation between raw absolute GSNR mismatch and calibrated diagnostic agreement.
3. Repeated-seed and symbol-count stability checks for PCS gain trends.
4. External GNPy-based calibration diagnostic showing that the C-band raw GSNR mismatch is mostly a conservative near-constant offset.
5. Claim-controlled reporting that prevents raw-validation overstatement.
6. A transparent workflow that can be extended to broader C/S/C+S and multiband studies.

## 3. Baseline comparison plan

The manuscript should compare the proposed workflow against the following baselines where data are available.

### Required baselines

| Baseline | Purpose |
|---|---|
| Uniform modulation | Shows the unshaped reference case |
| PCS-only | Separates shaping gain from learned mitigation |
| Neural-only mitigation | Separates learned mitigation from shaping |
| PCS plus neural mitigation | Main combined method if this remains part of the paper |
| Raw GNPy reference | Shows uncalibrated external mismatch |
| Offset-calibrated GNPy diagnostic | Shows calibrated trend agreement |
| Computational cost | Shows accuracy-cost tradeoff |

## 4. Validation claims currently allowed

Allowed:

- repeated-seed stability supports selected PCS trend results;
- larger-symbol stability reduces the chance of short-sequence artifacts;
- raw C-band GNPy agreement does not pass;
- C-band GNPy mismatch is mostly explained by a conservative near-constant offset across span count;
- offset-calibrated C-band diagnostic agreement is sub-dB;
- current results support calibrated trend evaluation, not direct absolute physical validation.

Not allowed:

- raw absolute GNPy validation;
- experimental validation;
- fully physical Manakov/NLSE simulator claim;
- universal multiband physical accuracy claim;
- C+S Raman/SRS physical validation without careful topology description.

## 5. Broader independent validation plan

The next validation expansion should test independence across:

| Dimension | Current status | Needed expansion |
|---|---|---|
| Span count | Partly tested in Day-12 C-band | Add more span counts if runtime permits |
| Launch power | Partial | Include powers not used for calibration |
| Channel loading | Limited | Add sparse/medium/dense channel loading |
| Baud rate | Not enough | Add at least one lower and one higher baud rate |
| Fiber parameters | Not enough | Add fiber loss/dispersion/nonlinearity variation |
| Band configuration | Partial | Clearly separate C, S, and C+S claims |
| External reference | GNPy diagnostic | Add public benchmark or experimental dataset if available |

## 6. Proposed Day-14 validation objective

Day-14 should be an independent validation expansion, not another cleanup step.

Recommended Day-14 target:

- C-band and S-band;
- span counts: 6, 8, 10, 12;
- launch powers: -1, 1, 3 dBm;
- at least two channel-loading settings;
- at least two baud-rate settings if feasible;
- report raw error, calibrated error, leave-one-condition-out RMSE and maximum absolute error.

## 7. Manuscript wording to use

Use:

The proposed framework is a calibrated surrogate workflow for PCS trend evaluation. External GNPy comparison is used as a calibration diagnostic. Raw absolute GSNR differs from GNPy by a conservative near-constant offset, while offset-calibrated span trends agree within sub-dB error for the validated C-band diagnostic.

Avoid:

The simulator is fully validated against GNPy.

Avoid:

The proposed method accurately predicts raw absolute GSNR.

Avoid:

The proposed model is experimentally validated.

## 8. Remaining before submission

Before Photonic Network Communications submission:

1. Add verified references.
2. Add final baseline tables.
3. Add broader independent validation if possible.
4. Compile Springer-format manuscript PDF.
5. Add one-command reproduction for all final manuscript tables and figures.
6. Create a versioned GitHub release.
7. Archive release on Zenodo or another repository and add DOI.
