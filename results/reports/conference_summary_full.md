# A Reproducible Simulation Framework for Joint Probabilistic Shaping and Lightweight Neural NLI Mitigation in Multi-Band O/E/S/C/L Optical Links

Run mode: `full`

## Defensible summary

This run evaluates a simulation-based multi-band O/E/S/C/L optical-link framework with four ablation scenarios.
The reported rate values are GMI-inspired achievable-rate estimates and must not be presented as experimentally confirmed capacity.

## Key result

- Uniform baseline total net rate: **19.200 Tb/s**
- Proposed PCS + neural NLI total net rate: **19.164 Tb/s**
- Relative estimated rate gain: **-0.186%**
- Proposed mean BER: **0.000e+00**
- Proposed mean NGMI: **1.000**
- Proposed mean GSNR: **35.706 dB**

## Scenario table

| scenario            | display_name              |   total_net_rate_tbps |   mean_net_rate_tbps_per_channel |   mean_ber |   median_ber |   mean_ngmi |   mean_gsnr_db |   n_channels |
|:--------------------|:--------------------------|----------------------:|---------------------------------:|-----------:|-------------:|------------:|---------------:|-------------:|
| uniform_baseline    | Uniform baseline          |               19.2    |                         0.426667 |          0 |            0 |           1 |        25.1189 |           45 |
| pcs_only            | PCS only                  |               19.1642 |                         0.425871 |          0 |            0 |           1 |        24.9878 |           45 |
| neural_only         | Neural NLI only           |               19.2    |                         0.426667 |          0 |            0 |           1 |        34.5997 |           45 |
| proposed_pcs_neural | Proposed PCS + Neural NLI |               19.1642 |                         0.425871 |          0 |            0 |           1 |        35.7064 |           45 |

## Complexity table

| scenario            | display_name              |   mean_parameter_count |   total_train_time_s |   mean_inference_time_ms_per_channel |   mean_residual_mse_improvement_percent |
|:--------------------|:--------------------------|-----------------------:|---------------------:|-------------------------------------:|----------------------------------------:|
| uniform_baseline    | Uniform baseline          |                      0 |                0     |                              0       |                                  0      |
| pcs_only            | PCS only                  |                      0 |                0     |                              0       |                                  0      |
| neural_only         | Neural NLI only           |                    786 |              182.45  |                              5.54658 |                                 88.5118 |
| proposed_pcs_neural | Proposed PCS + Neural NLI |                    786 |              189.256 |                              5.46619 |                                 91.3568 |

## Generated figures

- `results\figures\fig_total_net_rate_full.png`
- `results\figures\fig_mean_ngmi_full.png`
- `results\figures\fig_mean_ber_full.png`
- `results\figures\fig_mean_gsnr_full.png`
- `results\figures\fig_bandwise_gsnr_proposed_full.png`
- `results\figures\fig_complexity_tradeoff_full.png`

## Validation

- Passed hard gates: **True**
- Warnings:
  - Proposed method did not improve total rate over uniform baseline in this run.

## Recommended wording for the paper

The results indicate that joint probabilistic shaping and lightweight neural residual mitigation can improve simulation-level achievable-rate estimates under the configured multi-band link assumptions.
Future work should replace the simplified analytical channel with split-step Fourier propagation and validate against experimental or open benchmark data.