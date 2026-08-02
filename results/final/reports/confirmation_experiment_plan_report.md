# Independent Confirmation Experiment Plan

Purpose: independently confirm entropy-corrected PCS gains for C, S, and C+S using frozen operating points.

## Claim rule

A band is confirmed positive only if the lower 95 percent confidence bound of the entropy-corrected BMD gain is greater than zero.

## Experiment stages

| Stage | Seeds | Symbols | Selection allowed | Purpose |
|---|---:|---:|---:|---|
| discovery | 10 | 32768 | True | Broad grid search only. |
| validation | 10 | 65536 | True | Reduced grid and final operating-point selection. |
| final_confirmation | 30 | 131072 | False | Frozen-setting independent confirmation only. |

## Frozen operating points

| Scenario | nu | Spans | Launch power dBm | Current status | Priority |
|---|---:|---:|---:|---|---|
| C | 0.36 | 10 | 2 | positive discovery-stage result; borderline at larger-symbol confirmation | high |
| S | 0.36 | 12 | -2 | strongest confirmed internal result | high |
| C+S | 0.36 | 12 | 0 | exploratory internal shaping result | highest |

## Planned run counts

- Discovery rows: 30
- Validation rows: 30
- Final confirmation rows: 90
- Total planned rows: 150

## Final confirmation requirement

For a scenario to be called confirmed positive, the final confirmation set must satisfy: lower 95 percent confidence bound greater than zero.

Current evidence boundary: S strongest, C borderline, and C+S exploratory until this confirmation plan is executed.