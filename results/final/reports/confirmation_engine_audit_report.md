# Confirmation Engine Integration Audit

Purpose: identify existing project functions that can be safely reused for final-confirmation jobs.

## src.oescl.experiments

- `_scenario_grid() -> 'List[Dict]'`
- `_symbols_per_channel(cfg: 'Dict', mode: 'str') -> 'int'`
- `run_experiment(cfg: 'Dict', mode: 'str') -> 'Dict'`

## src.oescl.day8_q3_band_comparison

- `_accept(ci, gain, cfg)`
- `_air_rate(bmd_gmi: 'float', cfg: 'Dict') -> 'float'`
- `_best_span(gain)`
- `_ci(df, keys)`
- `_metrics(tx, tx_idx, rx, priors, cfg)`
- `_non_sat(row, cfg)`
- `_paired(seed_df)`
- `_run_grid(cfg)`
- `_run_one(seed, scenario, band, spans, power, nu, cfg)`
- `_scenario_bands(s)`
- `_scenario_seed(raw)`
- `_selected(ci, acc)`
- `_stress(cfg, scenario)`
- `_write(cfg, ci, gain, acc, best_span, figs)`
- `run_day8_q3_band_comparison(cfg: 'Dict') -> 'Dict'`

## src.oescl.day6

- `_acceptance(ci_df: 'pd.DataFrame', gain_df: 'pd.DataFrame', cfg: 'Dict') -> 'Dict'`
- `_ci(df: 'pd.DataFrame', keys: 'List[str]') -> 'pd.DataFrame'`
- `_compute_paired_gains(raw_df: 'pd.DataFrame') -> 'pd.DataFrame'`
- `_metrics(tx: 'np.ndarray', tx_idx: 'np.ndarray', rx: 'np.ndarray', priors: 'np.ndarray', cfg: 'Dict') -> 'Dict[str, float]'`
- `_net_rate(gmi: 'float', cfg: 'Dict') -> 'float'`
- `_non_saturated(row: 'pd.Series', cfg: 'Dict') -> 'bool'`
- `_run_one(seed: 'int', nu: 'float', cfg: 'Dict', shaped: 'bool', memory_check: 'bool') -> 'List[Dict]'`
- `_write_reports(cfg, raw_df, ci_df, gain_df, acceptance, figure_paths) -> 'Tuple[Path, Path, Path]'`
- `run_day6_pcs_confirmation(cfg: 'Dict') -> 'Dict'`

## src.oescl.day5_waveform

- `_align_gain(rx: 'np.ndarray', tx: 'np.ndarray') -> 'np.ndarray'`
- `_complex_awgn(shape, variance: 'float', rng: 'np.random.Generator') -> 'np.ndarray'`
- `matched_filter_and_downsample(waveform: 'np.ndarray', h: 'np.ndarray', sps: 'int', n_symbols: 'int') -> 'np.ndarray'`
- `pulse_shape(symbols: 'np.ndarray', h: 'np.ndarray', sps: 'int') -> 'np.ndarray'`
- `rrc_filter(beta: 'float', sps: 'int', span_symbols: 'int') -> 'np.ndarray'`
- `waveform_ssfm_channel(tx_symbols: 'np.ndarray', tx_indices: 'np.ndarray', priors: 'np.ndarray', cfg: 'Dict', band: 'str', spans: 'int', launch_power_dbm: 'float', stress: 'Dict', rng: 'np.random.Generator', disable_noise: 'bool' = False, disable_nonlinearity: 'bool' = False, disable_dispersion: 'bool' = False) -> 'WaveformResult'`

## src.oescl.gmi_exact

- `_logsumexp(a: 'np.ndarray', axis: 'int' = 1) -> 'np.ndarray'`
- `_normalise_priors(priors: 'np.ndarray | None', n_points: 'int') -> 'np.ndarray'`
- `ber_from_decision(tx_indices: 'np.ndarray', rx_symbols: 'np.ndarray') -> 'float'`
- `bit_metric_bmd_awgn_details(tx_indices: 'np.ndarray', rx_symbols: 'np.ndarray', noise_var: 'float', priors: 'np.ndarray | None' = None, max_samples: 'int | None' = None) -> 'dict[str, float]'`
- `bit_metric_gmi_awgn(tx_indices: 'np.ndarray', rx_symbols: 'np.ndarray', noise_var: 'float', priors: 'np.ndarray | None' = None, max_samples: 'int | None' = None) -> 'tuple[float, float]'`
- `estimate_noise_variance_from_decisions(rx_symbols: 'np.ndarray', tx_symbols: 'np.ndarray') -> 'float'`
- `gray_labels_16qam() -> 'np.ndarray'`
- `indices_to_bits(indices: 'np.ndarray') -> 'np.ndarray'`

## src.oescl.rate_metrics

- `achievable_rate_gain_tbps(pcs_bmd_gmi_bits_per_symbol: 'Number', uniform_bmd_gmi_bits_per_symbol: 'Number', baud_rate_gbaud: 'Number', polarizations: 'int' = 2) -> 'float'`
- `achievable_rate_tbps(bmd_gmi_bits_per_symbol: 'Number | None' = None, baud_rate_gbaud: 'Number | None' = None, polarizations: 'int' = 2, **aliases) -> 'float'`

## src.oescl.metrics

- `compute_channel_metrics(tx_symbols: 'np.ndarray', tx_indices: 'np.ndarray', rx_symbols: 'np.ndarray', probs: 'np.ndarray', cfg: 'Dict') -> 'Dict[str, float]'`
- `estimate_ber_from_ser(ser: 'float', bits_per_symbol: 'float') -> 'float'`
- `estimate_gmi_ngmi(gsnr_db: 'float', probs: 'np.ndarray', modulation_order: 'int' = 16) -> 'tuple[float, float]'`
- `estimate_gsnr_db(tx_symbols: 'np.ndarray', rx_symbols: 'np.ndarray') -> 'float'`
- `estimate_symbol_error_rate(tx_indices: 'np.ndarray', rx_symbols: 'np.ndarray') -> 'float'`
- `net_rate_tbps(gmi_bits_per_symbol: 'float', baud_rate_gbaud: 'float', n_channels: 'int', polarization_modes: 'int', fec_overhead: 'float' = 0.2) -> 'float'`

## src.oescl.constellation

- `decision_indices(received: 'np.ndarray', points: 'np.ndarray | None' = None) -> 'np.ndarray'`
- `entropy_bits(probs: 'np.ndarray') -> 'float'`
- `indices_to_symbols(indices: 'np.ndarray', points: 'np.ndarray | None' = None) -> 'np.ndarray'`
- `maxwell_boltzmann_probabilities(points: 'np.ndarray', nu: 'float') -> 'np.ndarray'`
- `sample_symbols(n_symbols: 'int', shaped: 'bool', nu: 'float', rng: 'np.random.Generator') -> 'tuple[np.ndarray, np.ndarray, np.ndarray]'`
- `square_16qam_points() -> 'np.ndarray'`

## src.oescl.channel

- `apply_optical_channel(tx_symbols: 'np.ndarray', noise_stats: 'Dict[str, float]', rng: 'np.random.Generator') -> 'tuple[np.ndarray, np.ndarray]'`
- `estimate_noise_variances(channel: 'ChannelSpec', cfg: 'Dict', shaped: 'bool', neural_mitigation: 'bool') -> 'Dict[str, float]'`
- `make_channel_plan(cfg: 'Dict', mode: 'str') -> 'List[ChannelSpec]'`

## Integration decision rule

The confirmation runner should only be connected to a function if it can output:

- scenario
- stage
- seed
- symbols
- nu
- spans
- launch_power_dbm
- uniform_bmd_rate_bit_per_symbol
- pcs_stored_score_bit_per_symbol
- entropy_correction_bit_per_symbol
- pcs_corrected_bmd_rate_bit_per_symbol
- delta_corrected_bmd_gain_bit_per_symbol
- ber_uniform
- ber_pcs
- gsnr_uniform_db
- gsnr_pcs_db

If no existing function provides these safely, create a dedicated final_confirmation engine adapter instead of modifying old Day-X code.