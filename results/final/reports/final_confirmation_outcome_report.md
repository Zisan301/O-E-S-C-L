# Final Confirmation Outcome Report

This report freezes the final independent confirmation result for the O-E-S-C-L project.

## Protocol

- Stage: final_confirmation
- Seeds: 21-50
- Rows: 90 total
- Scenarios: C, S, C+S
- Rows per scenario: 30
- Symbols per job: 131072
- Frozen shaping parameter: nu = 0.36

## Claim rule

A scenario is called confirmed positive only if the lower 95% confidence bound is greater than zero.

## Final claim boundary

| Scenario | n | Mean gain | 95% CI lower | 95% CI upper | Status | Manuscript action |
|---|---:|---:|---:|---:|---|---|
| C | 30 | -0.014480 | -0.017386 | -0.011574 | not_positive | Report as not positive under independent final confirmation; remove confirmed gain claim. |
| C+S | 30 | 0.001546 | -0.000687 | 0.003778 | borderline_inconclusive | Report as borderline/exploratory; do not claim confirmed positive gain. |
| S | 30 | 0.000412 | -0.001146 | 0.001969 | borderline_inconclusive | Report as borderline/inconclusive; do not claim confirmed positive gain. |

## Interpretation

No scenario should be described as having a confirmed positive entropy-corrected BMD gain under the final independent confirmation protocol.

The correct manuscript interpretation is:

- Earlier discovery-stage gains were not confirmed by the stricter 30-seed final-confirmation run.
- C-band becomes not positive under final confirmation.
- S-band remains borderline/inconclusive.
- C+S remains borderline/exploratory under the existing Day-8 two-band surrogate.
- The project contribution should be framed as a validation-aware framework that exposes non-robust discovery claims, not as a confirmed PCS gain result.

## Manuscript warning

Do not claim confirmed throughput improvement, confirmed PCS advantage, or robust C/S/C+S positive gain from the final-confirmation experiment.