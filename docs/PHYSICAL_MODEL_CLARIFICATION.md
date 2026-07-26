# Physical Model Clarification

## Current model identity

The current O-E-S-C-L workflow should be described as a calibrated surrogate framework, not as a fully physical Manakov/NLSE split-step Fourier method simulator.

## Why this clarification is necessary

The waveform-level and SSFM-like portions of the current implementation use normalized or effective modelling choices. These include surrogate scaling of dispersion, nonlinearity, waveform normalization and heuristic/effective noise scaling.

Because of these choices, the model should not be presented as a direct physical transmission simulator.

## Correct claim

Use:

The framework is a calibrated surrogate workflow for PCS trend evaluation in coherent optical link scenarios. It supports trend-level PCS analysis, repeated-seed stability checks and calibrated external diagnostic comparison against GNPy.

## Incorrect claims

Do not claim:

- direct physical Manakov/NLSE simulation;
- raw absolute GNPy validation;
- experimental or field validation;
- physically complete Raman/SRS propagation validation;
- universal multiband absolute-GSNR prediction.

## How GNPy is used

GNPy is used as an external calibration diagnostic. The current C-band diagnostic shows that raw O-E-S-C-L GSNR is conservatively offset from GNPy. A mostly constant offset explains the mismatch across the validated span-count sweep. After applying one transparent offset, the calibrated diagnostic shows sub-dB agreement.

## Manuscript rule

Every validation result must preserve this distinction:

1. raw external agreement;
2. calibrated diagnostic agreement;
3. PCS trend stability.

The manuscript must never merge these into a single unsupported statement.
