# Manuscript-Ready Final Confirmation Text

## Replacement Results Paragraph

Under the frozen independent final-confirmation protocol, each scenario was evaluated using 30 independent seeds, 131,072 symbols per job, and the fixed shaping parameter nu = 0.36. A positive PCS effect was accepted only when the lower 95% confidence bound of the entropy-corrected BMD-rate gain was greater than zero. This stricter confirmation criterion did not support a confirmed positive gain in any evaluated scenario.

For C, the mean entropy-corrected BMD-rate gain was -0.014480 bit/symbol with a 95% confidence interval of [-0.017386, -0.011574], leading to the status `not_positive`.
For S, the mean entropy-corrected BMD-rate gain was 0.000412 bit/symbol with a 95% confidence interval of [-0.001146, 0.001969], leading to the status `borderline_inconclusive`.
For C+S, the mean entropy-corrected BMD-rate gain was 0.001546 bit/symbol with a 95% confidence interval of [-0.000687, 0.003778], leading to the status `borderline_inconclusive`.

Therefore, the final manuscript should not claim a confirmed PCS throughput improvement. Instead, the main contribution should be framed as a validation-aware reproducibility framework that detects when discovery-stage shaping gains do not survive stricter independent confirmation.

## Replacement Claim Statement

The proposed validation-aware framework revealed that discovery-stage entropy-corrected PCS gains were not robust under a frozen 30-seed final-confirmation protocol. C-band was not positive, while S-band and C+S remained statistically inconclusive.

## Sentences to Remove or Avoid

- Avoid: confirmed PCS gain.
- Avoid: robust throughput improvement.
- Avoid: confirmed C/S/C+S shaping advantage.
- Avoid: final validation proves PCS benefit.

## Safer Contribution Wording

- Entropy-corrected BMD-rate accounting.
- Frozen independent confirmation protocol.
- Reproducible claim-boundary reporting.
- Demonstration that discovery-stage PCS gains may not survive stricter validation.