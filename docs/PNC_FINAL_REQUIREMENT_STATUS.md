# PNC Final Requirement Status

This document summarizes which submission-readiness requirements are closed, partial or still open.

## Closed requirements

| Requirement | Status | Evidence |
|---|---|---|
| Repository cleanup | Closed | Tracked environments, pycache files and generated Joblib model artifacts removed from Git tracking. |
| Root README | Closed | README.md added with calibrated-surrogate claim control. |
| .gitignore | Closed | Generated environments, pycache files, model artifacts and temporary outputs ignored. |
| Exact dependency lock | Closed | requirements-lock.txt added. |
| Smoke test | Closed | scripts/smoke_test_reproducibility.py verifies curated Day-13 diagnostic evidence. |
| Claim-control checker | Closed | scripts/check_pnc_submission_readiness.py checks public README and manuscript for risky positive claims. |
| Manuscript skeleton | Closed | manuscript/main.tex created in Springer Nature style. |
| Safe paper identity | Closed | Manuscript frames the work as a calibrated surrogate framework. |
| Physical-model clarification | Closed | docs/PHYSICAL_MODEL_CLARIFICATION.md added and manuscript wording patched. |
| Baseline framing | Closed | Baseline section separates uniform, PCS-only, neural-only, combined, raw GNPy and calibrated diagnostic comparisons. |
| Verified initial references | Closed | manuscript/references.bib includes initial verified references for PCS, GN/EGN, GNPy, DBP and ML-aided optical communication. |
| Generated manuscript table | Closed | scripts/generate_manuscript_artifacts.py creates manuscript/tables/validation_summary_table.tex and related CSV/MD files. |

## Partially satisfied requirements

| Requirement | Status | Remaining work |
|---|---|---|
| One-command reproduction | Partial | Current script regenerates manuscript artifacts from curated validated outputs. A heavier script should regenerate every final figure/table from raw simulation commands. |
| Broader independent validation | Partial | Day-14 starter validation was executed. Two broader C-band cases completed, two generated S-band GNPy cases failed, and the Day-13 fixed offset did not transfer cleanly. This is limitation evidence, not full broader validation success. |
| Stronger baseline comparison | Partial | Baseline structure exists, but final tables must be filled with available or newly generated data. |
| C/S/C+S integration | Partial | Existing evidence must be integrated carefully without overclaiming raw physical validation. |
| Springer submission formatting | Partial | main.tex exists, but final compilation, author metadata, figure placement and page-limit check are still needed. |

## Still open requirements before submission

| Requirement | Status | Action needed |
|---|---|---|
| Execute Day-14 broader validation | Open | Run feasible independent validation across span count, power, channel loading and possibly baud rate. |
| Add final figures | Open | Generate final manuscript figures from reproducible scripts. |
| Add final result tables | Open | Include baseline and validation tables in the manuscript. |
| Compile final Springer PDF | Open | Compile main.tex with Springer class files and fix LaTeX issues. |
| Versioned release | Open | Create a GitHub release after manuscript freeze. |
| DOI archive | Open | Upload release to Zenodo, OSF or Figshare and add DOI. |
| Final submission package | Open | Prepare source files, PDF, cover letter, highlights if needed and data/code availability statement. |

## Current honest conclusion

The project is now much closer to submission readiness than before. Repository hygiene, claim control, manuscript skeleton, physical-model clarification, baseline framing and generated validation-table workflow are in place.

However, the project should still not be submitted unchanged. The main remaining scientific gap is broader independent validation and final manuscript completion.

## Safe current paper label

A calibrated surrogate framework for probabilistic constellation shaping trend evaluation in coherent optical link scenarios.

## Unsafe labels to avoid

- fully physical Manakov/NLSE simulator;
- raw GNPy-validated simulator;
- experimentally validated optical transmission system;
- universal multiband absolute-GSNR predictor.


## Scope-freeze update

After Day-14, the submission scope is frozen as a calibrated surrogate PCS trend-evaluation framework with C-band calibrated diagnostic evidence and broader Day-14 limitation/stress-test evidence. The manuscript must not claim full C/S-band external validation.

See `docs/PNC_SUBMISSION_SCOPE_FREEZE.md`.
