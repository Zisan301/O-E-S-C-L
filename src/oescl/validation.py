from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def validate_results(result_bundle: Dict, cfg: Dict) -> Dict:
    errors = []
    warnings = []

    scenario_df: pd.DataFrame = result_bundle["scenario_summary"]
    channel_df: pd.DataFrame = result_bundle["channel_metrics"]

    if bool(cfg["validation"]["require_finite_metrics"]):
        numeric_cols = channel_df.select_dtypes(include=["number"]).columns
        bad_cols = []
        for col in numeric_cols:
            if not np.isfinite(channel_df[col].to_numpy(dtype=float)).all():
                bad_cols.append(col)
        if bad_cols:
            errors.append(f"Non-finite numeric values found in columns: {bad_cols}")

    max_rate = float(cfg["validation"]["max_reasonable_total_rate_tbps"])
    observed_max_rate = float(scenario_df["total_net_rate_tbps"].max())
    if observed_max_rate > max_rate:
        errors.append(
            f"Total rate {observed_max_rate:.2f} Tb/s exceeds configured conference-safe limit {max_rate:.2f} Tb/s."
        )

    proposed = scenario_df[scenario_df["scenario"] == "proposed_pcs_neural"]
    if proposed.empty:
        errors.append("Missing proposed_pcs_neural scenario.")
    else:
        row = proposed.iloc[0]
        min_ngmi = float(cfg["validation"]["min_valid_ngmi"])
        max_ber = float(cfg["validation"]["max_valid_ber"])

        if float(row["mean_ngmi"]) < min_ngmi:
            warnings.append(
                f"Proposed mean NGMI {row['mean_ngmi']:.3f} is below target {min_ngmi:.3f}; position as low-margin preliminary result."
            )

        if float(row["mean_ber"]) > max_ber:
            warnings.append(
                f"Proposed mean BER {row['mean_ber']:.3e} is above target {max_ber:.3e}; avoid strong capacity claims."
            )

    baseline = scenario_df[scenario_df["scenario"] == "uniform_baseline"]
    proposed = scenario_df[scenario_df["scenario"] == "proposed_pcs_neural"]
    if not baseline.empty and not proposed.empty:
        base_rate = float(baseline.iloc[0]["total_net_rate_tbps"])
        prop_rate = float(proposed.iloc[0]["total_net_rate_tbps"])
        if prop_rate <= base_rate:
            warnings.append(
                "Proposed method did not improve total rate over uniform baseline in this run."
            )

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
