# Final Project Manifest Summary

## Repository

Branch: improve/milestone-1-reproducibility
Commit: 10f2ef9291938d1a09c272b66fcfe43713192d9d

## Final claim boundaries

- pcs_rate_claim: Use entropy-corrected BMD-rate differences, not old uncorrected demapper-score gains.
- c_band_claim: Positive discovery-stage entropy-corrected gain; larger-symbol confirmation is borderline and should be described cautiously.
- s_band_claim: Strongest confirmed internal entropy-corrected shaping result.
- cs_band_claim: Exploratory internal C+S shaping result unless replaced by full ISRS-aware multichannel PCS validation.
- gnpy_claim: Calibrated GNPy alignment within tested configurations; not raw digital-twin accuracy.
- raman_claim: Ordinary Fiber topology with Raman/SRS-enabled GNPy simulation settings; not pump-amplified RamanFiber validation.

## Entropy-corrected final band results

| Scenario | nu | Spans | Power dBm | Corrected BMD gain | CI95 | Rate Gbit/s | Aggregate Gbit/s |
|---|---:|---:|---:|---:|---:|---:|---:|
| C | 0.36 | 10 | 2.0 | 0.022967 | 0.0211 | 2.450 |  |
| S | 0.36 | 12 | -2.0 | 0.039293 | 0.0140 | 4.191 |  |
| C+S | 0.36 | 12 | 0.0 | 0.043628 | 0.0148 | 4.654 | 9.307 |

## Claim-to-source traceability

### PCS-C-S-CS-entropy-corrected

Claim: C, S, and C+S outputs are reported using entropy-corrected BMD-rate gains.

Boundary: Discovery-stage values; final confirmation remains strongest for S, borderline for C, exploratory for C+S.

### DAY16-CS-GNPY-topology

Claim: Day-16 C+S GNPy reference uses ordinary Fiber with Raman/SRS simulation settings, not pump-amplified RamanFiber.

Boundary: RamanFiber attempt failed because operational parameters were missing.

### DAY16-CS-calibrated-GNPY-alignment

Claim: C+S calibrated held-out GNPy alignment is supported by Day-16 protocol summary.

Boundary: Calibrated alignment only; not uncalibrated direct agreement or experimental validation.

### DAY13-single-band-calibrated-GNPY-alignment

Claim: Single-band C/S calibrated held-out GNPy alignment is supported by Day-13 report.

Boundary: Band-dependent launch-power calibration; raw direct agreement failed.

## File inventory check

| File | Exists | SHA256 |
|---|---:|---|
| src/oescl/final_outputs/entropy_corrected_bmd.py | True | fac6cf76d719dbc3325919668889426b51b4f4c20f350fdd2d16526868141eb7 |
| scripts/final_outputs/generate_entropy_corrected_band_results.py | True | c452d8f539efdf56f5ad77c052705751d62978b7f6962633855c15616c46a850 |
| scripts/final_outputs/check_entropy_corrected_outputs.py | True | 33c10e10d36f0b54a8878c1d5e47d10099b56bf70b11bc007762ab81f07eb65b |
| results/final/tables/entropy_corrected_band_results.csv | True | 6e7837e7768a50b99e1fc19deb63b637556edb63fc466ff6ab4b736abec9c468 |
| results/final/reports/entropy_corrected_band_results_report.md | True | eef2fef0fe7e4782ff53fed219faf78cf4728672e06b397522b18ddbbecdcacf |
| validation_data/gnpy_day16_cs_raman_reference.csv | True | e5f8182780fb329319f824273401756be9472748cc1bf4c8638e6c167e44193c |
| results/tables/day16_cs_full_raman_protocol_summary.csv | True | f7ada1e43348d2bd8fd93bbec3977fe26e230e01a48694605543a996ba8e7c8b |
| results/reports/day16_cs_full_raman_isrs_validation_report.md | True | cc0fc46d5b3bdf93928d53f9d5579a0bf11fba2d8f549a22e71daec515ea004e |
| results/reports/day13_model_alignment_report.md | True | 6ee33d32833a893533621fb8ef8de399329ee4a3f5f5f416a2b3642df2753a88 |
| results/reports/day10_publication_validation_report.md | True | f0f6f14b74dffd074dccb9742c2c8bddd0071e9a02664bf50c2b48a36a6466ca |
| results/reports/day8_q3_acceptance_report.md | True | f90332af91f0e56a550a02dd6d91658496947cc800a07d6fc47306327fe53310 |
| results/topology_verify/reports/day16_topology_decision.md | True | 0c74a564490f9c3e0cab30c8936920c0091069e99489a90dc4af1e5d291c110d |
| results/topology_verify/reports/day16_ramanfiber_failed_attempt.md | True | 340a06ae5b496a3af0043786476217baff3b5e0fe759e145a0a143b7215cbd76 |
| results/topology_verify/tables/day16_original_reference_topology_rows.csv | True | cf2e2cba6d554cbcabbe0604678030ee4e5ef673ebe79b3c2ed3edb5cc06189c |
