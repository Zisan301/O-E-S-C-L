# Confirmation Statistical Summary

This report analyzes real final-confirmation rows only.

Claim rule: confirmed positive only if the lower 95% confidence bound is greater than zero.

| Scenario | n | Mean gain | 95% CI lower | 95% CI upper | Status |
|---|---:|---:|---:|---:|---|
| C | 30 | -0.014480 | -0.017386 | -0.011574 | not_positive |
| C+S | 30 | 0.001546 | -0.000687 | 0.003778 | borderline_inconclusive |
| S | 30 | 0.000412 | -0.001146 | 0.001969 | borderline_inconclusive |

No scenario should be called confirmed positive unless its status is confirmed_positive.