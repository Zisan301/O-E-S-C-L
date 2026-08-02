# Final Confirmation Claim Boundary

This document freezes the final independent confirmation result for the O-E-S-C-L project.

## Final protocol

- Stage: final_confirmation
- Seeds: 21-50
- Total jobs: 90
- Jobs per scenario: 30
- Symbols per job: 131072
- Frozen shaping parameter: nu = 0.36

## Acceptance rule

A scenario is called `confirmed_positive` only when the lower 95% confidence bound of the entropy-corrected BMD gain is greater than zero.

## Final result

| Scenario | n | Mean gain | 95% CI lower | 95% CI upper | Status |
|---|---:|---:|---:|---:|---|
| C | 30 | -0.014480 | -0.017386 | -0.011574 | not_positive |
| C+S | 30 | 0.001546 | -0.000687 | 0.003778 | borderline_inconclusive |
| S | 30 | 0.000412 | -0.001146 | 0.001969 | borderline_inconclusive |

## Claim boundary

No scenario is confirmed positive under the final independent confirmation rule.

The manuscript must not claim confirmed PCS throughput improvement or robust positive PCS gain.

The correct project framing is:

> A validation-aware framework that shows discovery-stage entropy-corrected PCS gains did not survive stricter independent final confirmation.

## Scenario interpretation

- C: not positive under independent final confirmation.
- S: borderline/inconclusive.
- C+S: borderline/exploratory under the existing Day-8 two-band surrogate.