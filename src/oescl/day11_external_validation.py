from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import shutil

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .constellation import sample_symbols
from .day5_waveform import waveform_ssfm_channel
from .utils import ensure_dir


def _complex_gsnr_db(tx: np.ndarray, rx: np.ndarray) -> float:
    err = np.asarray(rx) - np.asarray(tx)
    sig = float(np.mean(np.abs(tx) ** 2))
    noise = float(np.mean(np.abs(err) ** 2))
    return float(10.0 * np.log10(max(sig, 1e-15) / max(noise, 1e-15)))


def _stress(cfg: Dict[str, Any]) -> Dict[str, Any]:
    st = dict(cfg["day8"]["stress"])
    st["name"] = str(st.get("name", "day11_external_validation"))
    return st


def _case_id(row: Any) -> str:
    return f"{row['scenario_group']}-{row['band']}-{int(row['spans'])}sp-{float(row['launch_power_dbm']):+.1f}dBm"


def _run_uniform_case(cfg: Dict[str, Any], case: Dict[str, Any], seed: int) -> Dict[str, Any]:
    day11 = cfg["day11"]
    # Ensure Day-5 waveform settings are controlled by Day-11.
    cfg["day5"]["symbols"] = int(day11["symbols"])
    cfg["day5"]["ssfm_steps_per_span"] = int(day11["ssfm_steps_per_span"])

    scenario_group = str(case["scenario_group"])
    band = str(case["band"])
    spans = int(case["spans"])
    launch_power_dbm = float(case["launch_power_dbm"])

    rng_seed = (
        int(cfg["day8"]["seed"])
        + int(seed) * 1000003
        + spans * 1009
        + int(round((launch_power_dbm + 100.0) * 1000.0))
        + (101 if band == "S" else 17)
    )
    rng = np.random.default_rng(rng_seed)
    tx, tx_idx, priors = sample_symbols(int(day11["symbols"]), shaped=False, nu=0.0, rng=rng)
    result = waveform_ssfm_channel(
        tx_symbols=tx,
        tx_indices=tx_idx,
        priors=priors,
        cfg=cfg,
        band=band,
        spans=spans,
        launch_power_dbm=launch_power_dbm,
        stress=_stress(cfg),
        rng=rng,
    )

    gsnr_db = _complex_gsnr_db(result.tx_symbols_aligned, result.rx_symbols)
    return {
        "scenario_group": scenario_group,
        "band": band,
        "spans": spans,
        "launch_power_dbm": launch_power_dbm,
        "seed": int(seed),
        "symbols": int(day11["symbols"]),
        "ssfm_steps_per_span": int(day11["ssfm_steps_per_span"]),
        "oesc_uniform_gsnr_db": gsnr_db,
        "waveform_samples": int(result.stats.get("waveform_samples", -1)),
        "stress_noise": float(result.stats.get("stress_noise", np.nan)),
        "stress_nonlinear": float(result.stats.get("stress_nonlinear", np.nan)),
        "stress_implementation": float(result.stats.get("stress_implementation", np.nan)),
    }


def _summarize_runs(runs: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    keys = ["scenario_group", "band", "spans", "launch_power_dbm", "symbols", "ssfm_steps_per_span"]
    for key, g in runs.groupby(keys):
        row = dict(zip(keys, key))
        vals = g["oesc_uniform_gsnr_db"].astype(float).to_numpy()
        sd = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
        row["n_seeds"] = int(g["seed"].nunique())
        row["oesc_uniform_gsnr_mean_db"] = float(np.mean(vals))
        row["oesc_uniform_gsnr_std_db"] = sd
        row["oesc_uniform_gsnr_ci95_db"] = float(1.96 * sd / np.sqrt(max(len(vals), 1)))
        row["case_id"] = _case_id(row)
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["scenario_group", "spans", "launch_power_dbm"]).reset_index(drop=True)


def _copy_template_if_needed(template_path: Path) -> None:
    if template_path.exists():
        return
    ensure_dir(template_path.parent)
    rows = []
    for scenario, band, spans in [("C", "C", 10), ("S", "S", 12)]:
        for power in [-2.0, 0.0, 2.0, 4.0]:
            rows.append(
                {
                    "scenario_group": scenario,
                    "band": band,
                    "spans": spans,
                    "launch_power_dbm": power,
                    "reference_model": "GNPy",
                    "reference_source": "fill_with_version_or_script",
                    "reference_gsnr_db": "",
                    "notes": "fill real external GSNR value in dB",
                }
            )
    pd.DataFrame(rows).to_csv(template_path, index=False)


def _read_reference(cfg: Dict[str, Any], tables_dir: Path) -> tuple[pd.DataFrame | None, pd.DataFrame]:
    reference_path = Path(cfg["day11"]["reference_csv"])
    template_path = Path(cfg["day11"]["reference_template_csv"])
    _copy_template_if_needed(template_path)

    if not reference_path.exists():
        check = pd.DataFrame(
            [
                {
                    "status": "reference_file_missing",
                    "expected_csv_path": str(reference_path),
                    "message": "Copy validation_data/gnpy_day11_reference_template.csv to validation_data/gnpy_day11_reference.csv, fill reference_gsnr_db, and rerun Day-11.",
                }
            ]
        )
        return None, check

    ref = pd.read_csv(reference_path)
    required = {
        "scenario_group",
        "band",
        "spans",
        "launch_power_dbm",
        "reference_model",
        "reference_source",
        "reference_gsnr_db",
    }
    missing = sorted(required - set(ref.columns))
    if missing:
        check = pd.DataFrame(
            [
                {
                    "status": "reference_columns_missing",
                    "expected_csv_path": str(reference_path),
                    "message": "Missing required columns: " + ", ".join(missing),
                }
            ]
        )
        return None, check

    ref["reference_gsnr_db"] = pd.to_numeric(ref["reference_gsnr_db"], errors="coerce")
    missing_values = int(ref["reference_gsnr_db"].isna().sum())
    if missing_values:
        check = pd.DataFrame(
            [
                {
                    "status": "reference_values_missing",
                    "expected_csv_path": str(reference_path),
                    "message": f"{missing_values} row(s) have blank or invalid reference_gsnr_db.",
                }
            ]
        )
        return ref, check

    check = pd.DataFrame(
        [
            {
                "status": "reference_loaded",
                "expected_csv_path": str(reference_path),
                "message": f"Loaded {len(ref)} external reference rows.",
            }
        ]
    )
    return ref, check


def _validate_external(summary: pd.DataFrame, reference: pd.DataFrame | None, cfg: Dict[str, Any]) -> tuple[pd.DataFrame, Dict[str, Any]]:
    if reference is None or reference.empty or "reference_gsnr_db" not in reference.columns:
        return pd.DataFrame(), {
            "external_reference_gate_passed": False,
            "rmse_db": np.nan,
            "mae_db": np.nan,
            "max_abs_error_db": np.nan,
            "n_cases": 0,
        }

    keys = ["scenario_group", "band", "spans", "launch_power_dbm"]
    merged = summary.merge(reference, on=keys, how="inner")
    if merged.empty:
        return pd.DataFrame(), {
            "external_reference_gate_passed": False,
            "rmse_db": np.nan,
            "mae_db": np.nan,
            "max_abs_error_db": np.nan,
            "n_cases": 0,
        }

    merged["gsnr_error_db"] = merged["oesc_uniform_gsnr_mean_db"].astype(float) - merged["reference_gsnr_db"].astype(float)
    merged["abs_gsnr_error_db"] = merged["gsnr_error_db"].abs()
    err = merged["gsnr_error_db"].astype(float).to_numpy()
    rmse = float(np.sqrt(np.mean(err ** 2)))
    mae = float(np.mean(np.abs(err)))
    max_abs = float(np.max(np.abs(err)))
    passed = bool(
        rmse <= float(cfg["day11"]["external_rmse_pass_db"])
        and max_abs <= float(cfg["day11"]["external_max_abs_pass_db"])
        and len(merged) >= 2
    )
    metrics = {
        "external_reference_gate_passed": passed,
        "rmse_db": rmse,
        "mae_db": mae,
        "max_abs_error_db": max_abs,
        "n_cases": int(len(merged)),
    }
    return merged.sort_values(keys).reset_index(drop=True), metrics


def _plot_comparison(errors: pd.DataFrame, path: Path) -> Path:
    ensure_dir(path.parent)
    if errors.empty:
        fig, ax = plt.subplots(figsize=(7.0, 4.0), dpi=200)
        ax.text(0.5, 0.5, "External reference not supplied", ha="center", va="center")
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        return path

    labels = [
        f"{r.scenario_group} {int(r.spans)}sp {float(r.launch_power_dbm):+.0f} dBm"
        for r in errors.itertuples(index=False)
    ]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=200)
    ax.plot(x, errors["oesc_uniform_gsnr_mean_db"].astype(float), marker="o", label="O-E-S-C-L SSFM")
    ax.plot(x, errors["reference_gsnr_db"].astype(float), marker="s", label="External reference")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylabel("GSNR (dB)")
    ax.set_xlabel("Validation case")
    ax.legend(frameon=True)
    ax.grid(True, alpha=0.35)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def _plot_error(errors: pd.DataFrame, path: Path) -> Path:
    ensure_dir(path.parent)
    if errors.empty:
        fig, ax = plt.subplots(figsize=(7.0, 4.0), dpi=200)
        ax.text(0.5, 0.5, "External reference not supplied", ha="center", va="center")
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        return path

    labels = [
        f"{r.scenario_group} {int(r.spans)}sp {float(r.launch_power_dbm):+.0f} dBm"
        for r in errors.itertuples(index=False)
    ]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=200)
    ax.bar(x, errors["gsnr_error_db"].astype(float))
    ax.axhline(0.0, linewidth=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylabel("GSNR error (dB)")
    ax.set_xlabel("Validation case")
    ax.grid(True, axis="y", alpha=0.35)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def _write_report(
    cfg: Dict[str, Any],
    summary: pd.DataFrame,
    check: pd.DataFrame,
    errors: pd.DataFrame,
    metrics: Dict[str, Any],
    figures: List[Path],
) -> tuple[Path, Path]:
    reports_dir = ensure_dir(cfg["output"]["reports"])
    report_path = reports_dir / "day11_external_validation_report.md"
    latex_path = reports_dir / "day11_latex_external_validation_snippet.tex"

    lines = [
        "# Day-11 External Benchmark Validation Report",
        "",
        "Day-11 benchmarks O-E-S-C-L uniform-link GSNR predictions against an external GNPy/GN/EGN reference file.",
        "The validation focus is the single-band C and S cases. The C+S scenario remains a simplified stress case unless separately validated with a Raman/ISRS-aware reference.",
        "",
        "## Summary gate",
        "",
        f"- External reference gate passed: `{metrics['external_reference_gate_passed']}`",
        f"- Number of matched cases: `{metrics['n_cases']}`",
        f"- RMSE: `{metrics['rmse_db']:.4f} dB`" if np.isfinite(metrics["rmse_db"]) else "- RMSE: `not available`",
        f"- MAE: `{metrics['mae_db']:.4f} dB`" if np.isfinite(metrics["mae_db"]) else "- MAE: `not available`",
        f"- Max absolute error: `{metrics['max_abs_error_db']:.4f} dB`" if np.isfinite(metrics["max_abs_error_db"]) else "- Max absolute error: `not available`",
        "",
        "## O-E-S-C-L uniform GSNR summary",
        "",
        summary.round(6).to_markdown(index=False),
        "",
        "## External reference check",
        "",
        check.to_markdown(index=False),
        "",
    ]

    if not errors.empty:
        lines += [
            "## External validation errors",
            "",
            errors.round(6).to_markdown(index=False),
            "",
        ]

    lines += [
        "## Generated figures",
        "",
        *[f"- `{p}`" for p in figures],
        "",
        "## Correct manuscript claim",
        "",
    ]

    if metrics["external_reference_gate_passed"]:
        lines.append(
            "The manuscript can state that the selected C- and S-band O-E-S-C-L GSNR values were externally benchmarked against the supplied GNPy/GN/EGN reference, with the reported RMSE and maximum absolute error."
        )
    else:
        lines.append(
            "External benchmark validation is still incomplete or did not pass. The manuscript must not claim formal GNPy/GN/EGN validation until the reference file is supplied and the gate passes."
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if metrics["external_reference_gate_passed"]:
        latex = rf"""
\subsection{{External GSNR benchmark validation}}
The selected single-band C and S operating points were benchmarked against an external physical-layer reference.
The comparison used {metrics['n_cases']} matched C/S cases and produced an RMSE of {metrics['rmse_db']:.3f}~dB, a mean absolute error of {metrics['mae_db']:.3f}~dB, and a maximum absolute error of {metrics['max_abs_error_db']:.3f}~dB.
This benchmark supports the physical-layer consistency of the O-E-S-C-L waveform simulations used for the C/S PCS analysis.
The C+S result remains a simplified lumped-penalty stress scenario and is not interpreted as full Raman/ISRS-calibrated validation.
"""
    else:
        latex = r"""
\subsection{External GSNR benchmark validation}
External GNPy/GN/EGN benchmark validation remains pending because the required reference file was not supplied or the validation gate did not pass.
Therefore, the manuscript does not claim formal external validation at this stage.
The C/S PCS conclusions are supported by repeated-seed waveform simulations and numerical convergence checks, while C+S is retained only as a simplified stress scenario.
"""
    latex_path.write_text(latex.strip() + "\n", encoding="utf-8")

    return report_path, latex_path


def run_day11_external_validation(cfg: Dict[str, Any]) -> Dict[str, Any]:
    tables_dir = ensure_dir(cfg["output"]["tables"])
    figures_dir = ensure_dir(cfg["output"]["figures"])

    # Ensure reference template is available in project root even after partial extraction.
    template_path = Path(cfg["day11"]["reference_template_csv"])
    _copy_template_if_needed(template_path)

    rows: List[Dict[str, Any]] = []
    for case in cfg["day11"]["cases"]:
        for seed in map(int, cfg["day11"]["seeds"]):
            rows.append(_run_uniform_case(cfg, case, seed))

    runs = pd.DataFrame(rows)
    summary = _summarize_runs(runs)

    runs_csv = tables_dir / "day11_oesc_uniform_gsnr_runs.csv"
    summary_csv = tables_dir / "day11_oesc_uniform_gsnr_summary.csv"
    runs.to_csv(runs_csv, index=False)
    summary.to_csv(summary_csv, index=False)

    reference, check = _read_reference(cfg, tables_dir)
    check_csv = tables_dir / "day11_external_reference_check.csv"
    check.to_csv(check_csv, index=False)

    errors, metrics = _validate_external(summary, reference, cfg)
    errors_csv = tables_dir / "day11_external_validation_errors.csv"
    errors.to_csv(errors_csv, index=False)

    fig1 = _plot_comparison(errors, figures_dir / "fig_day11_external_gsnr_comparison.png")
    fig2 = _plot_error(errors, figures_dir / "fig_day11_external_gsnr_error.png")

    report_path, latex_path = _write_report(cfg, summary, check, errors, metrics, [fig1, fig2])

    return {
        "report_path": str(report_path),
        "latex_snippet_path": str(latex_path),
        "uniform_runs_csv": str(runs_csv),
        "uniform_summary_csv": str(summary_csv),
        "external_check_csv": str(check_csv),
        "validation_errors_csv": str(errors_csv),
        "figure_paths": [str(fig1), str(fig2)],
        **metrics,
    }
