# Day-11 External Reference Request

Day-11 prepares the external GSNR reference input for the accepted Day-10 stability case.

Important: do not copy O-E-S-C-L GSNR into `reference_gsnr_db`. That value is printed only for orientation.

## Files generated
- `validation_data\day11_external_reference_request.csv`
- `validation_data\gnpy_day10_reference.csv`

## Reference request
| scenario_group   | band   |   spans |   span_length_km |   launch_power_dbm |   baud_rate_gbaud |   channel_spacing_ghz |   center_nm |   attenuation_db_per_km |   dispersion_ps_nm_km |   noise_figure_db |   gamma_w_inv_km | reference_model   | reference_gsnr_db   |   oescl_uniform_gsnr_db_for_orientation_only | notes                                                                        |
|:-----------------|:-------|--------:|-----------------:|-------------------:|------------------:|----------------------:|------------:|------------------------:|----------------------:|------------------:|-----------------:|:------------------|:--------------------|---------------------------------------------:|:-----------------------------------------------------------------------------|
| C                | C      |      10 |               80 |                  2 |                64 |                    75 |        1550 |                    0.19 |                  16.7 |                 5 |             1.25 | GNPy              |                     |                                      12.8631 | Mean over 10 seeds. For orientation only; do not copy as external reference. |

## Next action
Run an independent GNPy/GN/EGN model for the listed case, fill `reference_gsnr_db`, then rerun Day-10 validation.