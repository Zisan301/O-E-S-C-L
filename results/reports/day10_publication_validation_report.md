# Day-10 Publication Validation Report

Day-10 strengthens the single-band C and S validation evidence after Day-9.

It focuses on larger symbol-count convergence, raw per-seed paired gains, and an optional external GNPy/GN/EGN reference check.

The C+S case remains a simplified stress scenario unless enabled and externally validated.


## Generated tables

- `raw_per_seed_metrics`: `E:\VS Code\O+E+S+C+L\results\tables\day10_raw_per_seed_metrics.csv`
- `raw_per_seed_paired_gains`: `E:\VS Code\O+E+S+C+L\results\tables\day10_raw_per_seed_paired_gains.csv`
- `symbol_count_convergence`: `E:\VS Code\O+E+S+C+L\results\tables\day10_symbol_count_convergence.csv`
- `symbol_count_stability_summary`: `E:\VS Code\O+E+S+C+L\results\tables\day10_symbol_count_stability_summary.csv`
- `step_convergence_metrics`: `E:\VS Code\O+E+S+C+L\results\tables\day10_step_convergence_metrics.csv`
- `step_convergence_paired_gains`: `E:\VS Code\O+E+S+C+L\results\tables\day10_step_convergence_paired_gains.csv`
- `internal_gn_reference`: `E:\VS Code\O+E+S+C+L\results\tables\day10_internal_gn_reference.csv`
- `external_reference_check`: `E:\VS Code\O+E+S+C+L\results\tables\day10_external_reference_check.csv`

## Generated figures

- `E:\VS Code\O+E+S+C+L\results\figures\fig_day10_symbol_count_convergence.png`
- `E:\VS Code\O+E+S+C+L\results\figures\fig_day10_symbol_count_relative_error.png`
- `E:\VS Code\O+E+S+C+L\results\figures\fig_day10_seed_gain_distribution.png`
- `E:\VS Code\O+E+S+C+L\results\figures\fig_day10_gn_reference_comparison.png`

## Summary gates

- Symbol-count stability gate passed: `True`
- External reference gate passed: `False`
- Internal GN-style sanity RMSE: `4.2140 dB`

## Symbol-count stability summary

| scenario_group   |   low_symbol_count |   high_symbol_count |   low_gmi_gain |   high_gmi_gain |   gmi_gain_drift |   abs_gmi_gain_drift |   relative_gmi_gain_drift | largest_count_positive_gain   | passed_symbol_stability   | reason   |
|:-----------------|-------------------:|--------------------:|---------------:|----------------:|-----------------:|---------------------:|--------------------------:|:------------------------------|:--------------------------|:---------|
| C                |              32768 |               65536 |       0.020679 |        0.020917 |         0.000238 |             0.000238 |                  0.011375 | True                          | True                      | passed   |

## External reference check

| status                           | expected_csv_path                        | message                                                              |
|:---------------------------------|:-----------------------------------------|:---------------------------------------------------------------------|
| reference_file_present_but_empty | validation_data\gnpy_day10_reference.csv | reference_gsnr_db values were empty or no matching cases were found. |

## Correct manuscript claim after Day-10

The manuscript can state that accepted C/S PCS gains are supported by larger-symbol repeated-seed convergence. External validation is still incomplete, so the GN-style result must be described only as an internal analytical sanity check.