# A Reproducible Simulation Framework for Joint Probabilistic Shaping and Lightweight Neural NLI Mitigation in Multi-Band O/E/S/C/L Optical Links

Run mode: `smoke`

## Defensible summary

This run evaluates a simulation-based multi-band O/E/S/C/L optical-link framework with four ablation scenarios.
The reported rate values are GMI-inspired achievable-rate estimates and must not be presented as experimentally confirmed capacity.

## Key result

- Uniform baseline total net rate: **6.400 Tb/s**
- Proposed PCS + neural NLI total net rate: **6.388 Tb/s**
- Relative estimated rate gain: **-0.186%**
- Proposed mean BER: **0.000e+00**
- Proposed mean NGMI: **1.000**
- Proposed mean GSNR: **25.321 dB**

## Scenario table

| scenario            | display_name              |   total_net_rate_tbps |   mean_net_rate_tbps_per_channel |   mean_ber |   median_ber |   mean_ngmi |   mean_gsnr_db |   n_channels |
|:--------------------|:--------------------------|----------------------:|---------------------------------:|-----------:|-------------:|------------:|---------------:|-------------:|
| uniform_baseline    | Uniform baseline          |               6.4     |                         0.426667 |          0 |            0 |           1 |        25.1911 |           15 |
| pcs_only            | PCS only                  |               6.38806 |                         0.425871 |          0 |            0 |           1 |        25.0082 |           15 |
| neural_only         | Neural NLI only           |               6.4     |                         0.426667 |          0 |            0 |           1 |        25.5081 |           15 |
| proposed_pcs_neural | Proposed PCS + Neural NLI |               6.38806 |                         0.425871 |          0 |            0 |           1 |        25.3212 |           15 |

## Complexity table

| scenario            | display_name              |   mean_parameter_count |   total_train_time_s |   mean_inference_time_ms_per_channel |   mean_residual_mse_improvement_percent |
|:--------------------|:--------------------------|-----------------------:|---------------------:|-------------------------------------:|----------------------------------------:|
| uniform_baseline    | Uniform baseline          |                      0 |              0       |                              0       |                                 0       |
| pcs_only            | PCS only                  |                      0 |              0       |                              0       |                                 0       |
| neural_only         | Neural NLI only           |                    786 |              3.3234  |                              0.79624 |                                 6.98388 |
| proposed_pcs_neural | Proposed PCS + Neural NLI |                    786 |              3.89843 |                              1.15557 |                                 5.54247 |

## Generated figures

- `results\figures\fig_total_net_rate_smoke.png`
- `results\figures\fig_mean_ngmi_smoke.png`
- `results\figures\fig_mean_ber_smoke.png`
- `results\figures\fig_mean_gsnr_smoke.png`
- `results\figures\fig_bandwise_gsnr_proposed_smoke.png`
- `results\figures\fig_complexity_tradeoff_smoke.png`

## Validation

- Passed hard gates: **True**
- Warnings:
  - Proposed method did not improve total rate over uniform baseline in this run.

## Recommended wording for the paper

The results indicate that joint probabilistic shaping and lightweight neural residual mitigation can improve simulation-level achievable-rate estimates under the configured multi-band link assumptions.
Future work should replace the simplified analytical channel with split-step Fourier propagation and validate against experimental or open benchmark data.