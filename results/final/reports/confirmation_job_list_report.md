# Final Confirmation Job List

This file defines the frozen final-confirmation simulation jobs.

Important: these jobs are planned only. They are not fake results.

## Job counts

| Scenario | Jobs |
|---|---:|
| C | 30 |
| C+S | 30 |
| S | 30 |

Total jobs: 90

## Output files

- Job CSV: results/final/tables/confirmation_job_list.csv
- PowerShell command list: results/final/reports/confirmation_job_commands.ps1

## Next implementation step

Connect run_single_confirmation_job.py to the real simulation engine, then run the 90 jobs and combine outputs into confirmation_raw_results.csv.