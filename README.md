# O-E-S-C-L

Publication-oriented modelling code for evaluating probabilistic constellation shaping (PCS) trends in multiband coherent optical link scenarios.

## Current manuscript identity

This repository should be described as a calibrated surrogate simulation and validation framework, not as a fully physical Manakov/NLSE transmission simulator.

The manuscript must not claim raw absolute GNPy validation.

## Current validated claim

PCS gain trends are supported by repeated-seed, larger-symbol convergence. External GNPy comparison shows that the raw O-E-S-C-L absolute GSNR scale is conservatively shifted relative to GNPy by an approximately constant offset. After applying one constant external offset, the C-band GSNR span trend aligns with GNPy with sub-dB error.

## Key validation evidence

### Day-10: C-band larger-symbol stability

- Largest symbol count: 65,536
- Seeds: 10
- High-count GMI gain: 0.0209167
- Absolute GMI-gain drift: 0.0002379
- Relative GMI-gain drift: 0.011375
- Result: passed

### Day-11: raw GNPy reference check

- GNPy reference GSNR: 18.780000 dB
- O-E-S-C-L uniform GSNR: 12.863055 dB
- Raw error: -5.916945 dB
- Result: raw external gate did not pass

### Day-12: external alignment sweep

- Span counts: 6, 8, 10, 12
- Mean O-E-S-C-L minus GNPy offset: -6.152843 dB
- Offset standard deviation: 0.328463 dB
- Error-vs-span slope: 0.104764 dB/span
- Result: mostly constant conservative offset

### Day-13: offset-calibration diagnostic

- Constant offset applied to O-E-S-C-L GSNR: +6.152843 dB
- Calibrated RMSE: 0.284458 dB
- Leave-one-out RMSE: 0.379277 dB
- Result: diagnostic offset calibration passed

## Repository structure

- config/: YAML configuration files
- scripts/: reproducibility and validation scripts
- src/oescl/: core source code
- validation_data/: curated validation reference inputs
- results/tables/: curated manuscript-supporting CSV outputs
- results/reports/: curated manuscript-supporting reports and LaTeX snippets

## Installation

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

## Reproduce current evidence

Run smoke test:

python scripts\smoke_test_reproducibility.py

Run full validation sequence:

powershell -ExecutionPolicy Bypass -File scripts\run_reproduce_publication_evidence.ps1

## Correct manuscript wording

Use: external GNPy-based calibration diagnostic.

Do not claim: fully GNPy validated.

Do not claim: raw GSNR directly matches GNPy.

Do not claim: direct physical Manakov/NLSE SSFM simulator.

<!-- OESCL_FINAL_CONFIRMATION_START -->
## Final confirmation claim boundary

The final independent confirmation run used 90 jobs: 30 seeds per scenario for C, S, and C+S.

Final status:

- C: not_positive (mean gain -0.014480, 95% CI [-0.017386, -0.011574])
- C+S: borderline_inconclusive (mean gain 0.001546, 95% CI [-0.000687, 0.003778])
- S: borderline_inconclusive (mean gain 0.000412, 95% CI [-0.001146, 0.001969])

No scenario is confirmed positive under the final 95% confidence-bound rule. The project should be cited as a validation-aware framework for detecting non-robust discovery-stage PCS gains, not as a confirmed PCS-gain result.

See: `docs/reproducibility/FINAL_CONFIRMATION_CLAIM_BOUNDARY.md`
<!-- OESCL_FINAL_CONFIRMATION_END -->
