# Entropy-Corrected C/S/C+S Band Results

This report converts the stored Day-8 demapper-score gains into entropy-corrected BMD-rate gains.

Correction used for nu = 0.36: 0.02961 bit/symbol.

| Scenario | nu | Spans | Power dBm | Stored score gain | Corrected BMD gain | 95% CI | Rate gain Gbit/s | Aggregate Gbit/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C | 0.36 | 10 | 2 | 0.0526 | 0.0230 | +/- 0.0211 | 2.45 |  |
| S | 0.36 | 12 | -2 | 0.0689 | 0.0393 | +/- 0.0140 | 4.19 |  |
| C+S | 0.36 | 12 | 0 | 0.0732 | 0.0436 | +/- 0.0148 | 4.65 | 9.31 |

Claim boundary: these are entropy-corrected discovery-stage results. Larger-symbol confirmation remains strongest for S, borderline for C, and exploratory for C+S shaping.