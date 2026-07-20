from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

from .utils import ensure_dir


def _fmt(value: float, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def write_summary_report(
    result_bundle: Dict,
    validation: Dict,
    cfg: Dict,
    mode: str,
) -> Path:
    reports_dir = ensure_dir(cfg["output"]["reports"])
    path = reports_dir / f"conference_summary_{mode}.md"

    scenario_df: pd.DataFrame = result_bundle["scenario_summary"]
    complexity_df: pd.DataFrame = result_bundle["complexity_summary"]

    proposed = scenario_df[scenario_df["scenario"] == "proposed_pcs_neural"].iloc[0]
    baseline = scenario_df[scenario_df["scenario"] == "uniform_baseline"].iloc[0]

    rate_gain = (
        100.0
        * (
            float(proposed["total_net_rate_tbps"])
            - float(baseline["total_net_rate_tbps"])
        )
        / max(float(baseline["total_net_rate_tbps"]), 1e-15)
    )

    lines = []
    lines.append(f"# {cfg['project']['paper_title']}")
    lines.append("")
    lines.append(f"Run mode: `{mode}`")
    lines.append("")
    lines.append("## Defensible summary")
    lines.append("")
    lines.append(
        "This run evaluates a simulation-based multi-band O/E/S/C/L optical-link framework with four ablation scenarios."
    )
    lines.append(
        "The reported rate values are GMI-inspired achievable-rate estimates and must not be presented as experimentally confirmed capacity."
    )
    lines.append("")
    lines.append("## Key result")
    lines.append("")
    lines.append(
        f"- Uniform baseline total net rate: **{_fmt(baseline['total_net_rate_tbps'])} Tb/s**"
    )
    lines.append(
        f"- Proposed PCS + neural NLI total net rate: **{_fmt(proposed['total_net_rate_tbps'])} Tb/s**"
    )
    lines.append(f"- Relative estimated rate gain: **{_fmt(rate_gain)}%**")
    lines.append(f"- Proposed mean BER: **{proposed['mean_ber']:.3e}**")
    lines.append(f"- Proposed mean NGMI: **{_fmt(proposed['mean_ngmi'])}**")
    lines.append(f"- Proposed mean GSNR: **{_fmt(proposed['mean_gsnr_db'])} dB**")
    lines.append("")
    lines.append("## Scenario table")
    lines.append("")
    lines.append(scenario_df.to_markdown(index=False))
    lines.append("")
    lines.append("## Complexity table")
    lines.append("")
    lines.append(complexity_df.to_markdown(index=False))
    lines.append("")
    lines.append("## Generated figures")
    lines.append("")
    for figure in result_bundle["figure_paths"]:
        lines.append(f"- `{figure}`")
    lines.append("")
    lines.append("## Validation")
    lines.append("")
    lines.append(f"- Passed hard gates: **{validation['passed']}**")
    if validation["errors"]:
        lines.append("- Errors:")
        for error in validation["errors"]:
            lines.append(f"  - {error}")
    if validation["warnings"]:
        lines.append("- Warnings:")
        for warning in validation["warnings"]:
            lines.append(f"  - {warning}")
    if not validation["errors"] and not validation["warnings"]:
        lines.append("- No validation warnings.")
    lines.append("")
    lines.append("## Recommended wording for the paper")
    lines.append("")
    lines.append(
        "The results indicate that joint probabilistic shaping and lightweight neural residual mitigation can improve simulation-level achievable-rate estimates under the configured multi-band link assumptions."
    )
    lines.append(
        "Future work should replace the simplified analytical channel with split-step Fourier propagation and validate against experimental or open benchmark data."
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
