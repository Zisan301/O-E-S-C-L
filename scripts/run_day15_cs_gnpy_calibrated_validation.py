#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise RuntimeError("PyYAML is required. Install with: pip install pyyaml") from exc

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None


def norm_col(c: str) -> str:
    return str(c).strip().lower().replace(" ", "_").replace("-", "_")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def rmse(x: pd.Series) -> float:
    vals = pd.to_numeric(x, errors="coerce").dropna().to_numpy(dtype=float)
    if len(vals) == 0:
        return float("nan")
    return float(np.sqrt(np.mean(vals ** 2)))


def mae(x: pd.Series) -> float:
    vals = pd.to_numeric(x, errors="coerce").dropna().to_numpy(dtype=float)
    if len(vals) == 0:
        return float("nan")
    return float(np.mean(np.abs(vals)))


def max_abs(x: pd.Series) -> float:
    vals = pd.to_numeric(x, errors="coerce").dropna().to_numpy(dtype=float)
    if len(vals) == 0:
        return float("nan")
    return float(np.max(np.abs(vals)))


def fmt(v: Any, digits: int = 4) -> str:
    try:
        x = float(v)
        if math.isnan(x):
            return "not available"
        return f"{x:.{digits}f}"
    except Exception:
        return "not available"


def first_existing(paths: list[str]) -> Optional[Path]:
    for p in paths:
        path = Path(p)
        if path.exists():
            return path
    return None


def pick_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    cols = {norm_col(c): c for c in df.columns}
    for cand in candidates:
        key = norm_col(cand)
        if key in cols:
            return cols[key]
    return None


def load_oesc_cs_summary(cfg: dict[str, Any]) -> tuple[pd.DataFrame, str]:
    cs = cfg["cs_case"]
    candidates = cfg["inputs"]["oesc_metric_candidates"]
    errors = []
    for path_str in candidates:
        path = Path(path_str)
        if not path.exists():
            errors.append(f"missing {path}")
            continue
        try:
            df = pd.read_csv(path)
        except Exception as exc:
            errors.append(f"could not read {path}: {exc}")
            continue
        if df.empty:
            errors.append(f"empty {path}")
            continue

        group_col = pick_column(df, ["scenario_group", "scenario", "band_group", "group", "case_group"])
        band_col = pick_column(df, ["band", "scenario_group", "scenario"])
        spans_col = pick_column(df, ["spans", "n_spans", "span_count"])
        power_col = pick_column(df, ["launch_power_dbm", "power_dbm", "launch_power", "power"])
        gsnr_col = pick_column(df, ["gsnr_db", "uniform_gsnr_db", "gsnr", "gsnr_mean_db", "oesc_uniform_gsnr_mean_db"])
        pcs_col = pick_column(df, ["pcs_nu", "nu", "shaping_nu", "pcs_coefficient", "shaping_coefficient"])
        mode_col = pick_column(df, ["mode", "constellation", "shaping", "variant", "format", "case"])
        seed_col = pick_column(df, ["seed", "random_seed"])

        needed = [spans_col, power_col, gsnr_col]
        if any(c is None for c in needed):
            errors.append(f"{path} missing required columns; columns={list(df.columns)}")
            continue

        d = df.copy()
        mask = pd.Series(True, index=d.index)

        # Identify C+S rows flexibly.
        target_strings = {"c+s", "cs", "c_s", "cpluss", "c_plus_s", "cands", "c_and_s"}
        if group_col is not None:
            val = d[group_col].astype(str).str.lower().str.replace(" ", "", regex=False)
            group_mask = val.isin(target_strings) | val.str.contains("c\\+s", regex=True) | val.str.contains("c\+s", regex=False)
        else:
            group_mask = pd.Series(False, index=d.index)
        if band_col is not None:
            valb = d[band_col].astype(str).str.lower().str.replace(" ", "", regex=False)
            band_mask = valb.isin(target_strings) | valb.str.contains("c\\+s", regex=True) | valb.str.contains("c\+s", regex=False)
        else:
            band_mask = pd.Series(False, index=d.index)
        mask &= (group_mask | band_mask)

        mask &= pd.to_numeric(d[spans_col], errors="coerce").eq(float(cs["spans"]))
        mask &= pd.to_numeric(d[power_col], errors="coerce").isin([float(x) for x in cs["launch_powers_dbm"]])

        if pcs_col is not None:
            pcs_vals = pd.to_numeric(d[pcs_col], errors="coerce")
            # Uniform is expected to be nu=0. If no exact zeros after C+S filtering, keep minimum nu as fallback.
            base_mask = mask & pcs_vals.eq(0.0)
            if not base_mask.any() and mask.any():
                min_nu = pcs_vals[mask].min()
                base_mask = mask & pcs_vals.eq(min_nu)
            mask = base_mask
        elif mode_col is not None:
            mode_vals = d[mode_col].astype(str).str.lower()
            uniform_mask = mode_vals.str.contains("uniform") | mode_vals.str.contains("unshaped") | mode_vals.eq("baseline")
            if (mask & uniform_mask).any():
                mask &= uniform_mask

        sub = d.loc[mask].copy()
        if sub.empty:
            errors.append(f"{path} has no matching C+S uniform rows")
            continue

        sub["launch_power_dbm"] = pd.to_numeric(sub[power_col], errors="coerce")
        sub["oesc_uniform_gsnr_db"] = pd.to_numeric(sub[gsnr_col], errors="coerce")
        sub["spans"] = pd.to_numeric(sub[spans_col], errors="coerce").astype("Int64")
        if seed_col is not None:
            sub["seed"] = sub[seed_col]
        else:
            sub["seed"] = np.arange(len(sub))

        summary = sub.groupby(["launch_power_dbm", "spans"], as_index=False).agg(
            oesc_uniform_gsnr_mean_db=("oesc_uniform_gsnr_db", "mean"),
            oesc_uniform_gsnr_std_db=("oesc_uniform_gsnr_db", "std"),
            n_seeds=("seed", "nunique"),
        )
        summary["scenario_group"] = cs["scenario_group"]
        summary["band"] = cs["band"]
        summary["case_id"] = summary.apply(lambda r: f"CS-{int(r['spans'])}sp-{float(r['launch_power_dbm']):+g}dBm", axis=1)
        return summary.sort_values("launch_power_dbm"), str(path)

    template_path = Path(cfg["outputs"]["missing_oesc_template"])
    ensure_parent(template_path)
    pd.DataFrame({
        "scenario_group": [cs["scenario_group"]] * len(cs["launch_powers_dbm"]),
        "band": [cs["band"]] * len(cs["launch_powers_dbm"]),
        "spans": [cs["spans"]] * len(cs["launch_powers_dbm"]),
        "launch_power_dbm": cs["launch_powers_dbm"],
        "oesc_uniform_gsnr_mean_db": [""] * len(cs["launch_powers_dbm"]),
        "notes": ["fill only if automatic C+S extraction failed"] * len(cs["launch_powers_dbm"]),
    }).to_csv(template_path, index=False)
    raise RuntimeError("Could not extract O-E-S-C-L C+S uniform GSNR rows. " + "; ".join(errors) + f". Template written to {template_path}")


def load_or_derive_reference(cfg: dict[str, Any]) -> tuple[pd.DataFrame, str]:
    cs = cfg["cs_case"]
    true_path = Path(cfg["inputs"]["optional_true_cs_reference"])
    if true_path.exists():
        ref = pd.read_csv(true_path)
        col_map = {norm_col(c): c for c in ref.columns}
        if "reference_gsnr_db" not in col_map:
            raise RuntimeError(f"{true_path} exists but has no reference_gsnr_db column")
        ref["reference_gsnr_db"] = pd.to_numeric(ref[col_map["reference_gsnr_db"]], errors="coerce")
        if "launch_power_dbm" not in col_map:
            raise RuntimeError(f"{true_path} exists but has no launch_power_dbm column")
        ref["launch_power_dbm"] = pd.to_numeric(ref[col_map["launch_power_dbm"]], errors="coerce")
        ref = ref[ref["launch_power_dbm"].isin([float(x) for x in cs["launch_powers_dbm"]])].copy()
        ref["scenario_group"] = cs["scenario_group"]
        ref["band"] = cs["band"]
        ref["spans"] = cs["spans"]
        if "reference_source" not in ref.columns:
            ref["reference_source"] = "user supplied true C+S external reference"
        if "notes" not in ref.columns:
            ref["notes"] = "true C+S external reference"
        return ref[["scenario_group", "band", "spans", "launch_power_dbm", "reference_gsnr_db", "reference_source", "notes"]], "true_cs_reference"

    day12_path = Path(cfg["inputs"]["matched_single_band_reference"])
    if not day12_path.exists():
        raise RuntimeError(f"Missing matched single-band reference: {day12_path}")
    d = pd.read_csv(day12_path)
    cols = {norm_col(c): c for c in d.columns}
    band_col = cols.get("band")
    power_col = cols.get("launch_power_dbm") or cols.get("launch_power_(dbm)") or cols.get("launch_power")
    gsnr_col = cols.get("reference_gsnr_db") or cols.get("gsnr_signal_bw_db") or cols.get("gsnr_signal_bw_(db)") or cols.get("gsnr_signal_bw")
    if band_col is None or power_col is None or gsnr_col is None:
        raise RuntimeError(f"Could not identify band/power/GSNR columns in {day12_path}; columns={list(d.columns)}")
    d["band_norm"] = d[band_col].astype(str).str.upper().str.strip()
    d["launch_power_dbm"] = pd.to_numeric(d[power_col], errors="coerce")
    d["gsnr_db"] = pd.to_numeric(d[gsnr_col], errors="coerce")

    rows = []
    for p in [float(x) for x in cs["launch_powers_dbm"]]:
        cvals = d[(d["band_norm"] == "C") & d["launch_power_dbm"].eq(p)]["gsnr_db"].dropna()
        svals = d[(d["band_norm"] == "S") & d["launch_power_dbm"].eq(p)]["gsnr_db"].dropna()
        if cvals.empty or svals.empty:
            raise RuntimeError(f"Could not derive C+S reference for power {p}; missing C or S Day-12 reference")
        c = float(cvals.iloc[0]); s = float(svals.iloc[0])
        if cfg["reference"].get("derived_mode") == "linear_mean_snr_db":
            ref = 10.0 * math.log10((10.0 ** (c / 10.0) + 10.0 ** (s / 10.0)) / 2.0)
        elif cfg["reference"].get("derived_mode") == "min_db":
            ref = min(c, s)
        else:
            ref = (c + s) / 2.0
        rows.append({
            "scenario_group": cs["scenario_group"],
            "band": cs["band"],
            "spans": cs["spans"],
            "launch_power_dbm": p,
            "reference_gsnr_db": ref,
            "reference_source": cfg["reference"].get("derived_reference_source", "derived from C/S GNPy"),
            "notes": "Derived separable C+S reference from matched C and S GNPy values; not Raman/ISRS-aware",
            "c_reference_gsnr_db": c,
            "s_reference_gsnr_db": s,
        })
    return pd.DataFrame(rows), "derived_separable_reference"


def fit_line(cal: pd.DataFrame) -> tuple[float, float]:
    x = cal["launch_power_dbm"].astype(float).to_numpy()
    y = (cal["reference_gsnr_db"] - cal["oesc_uniform_gsnr_mean_db"]).astype(float).to_numpy()
    if len(x) == 1:
        return float(y[0]), 0.0
    slope, intercept = np.polyfit(x, y, 1)
    return float(intercept), float(slope)


def summarize_protocol(name: str, set_name: str, errors: pd.Series, rmse_gate: Optional[float], max_gate: Optional[float], interpretation: str) -> dict[str, Any]:
    r = rmse(errors); m = mae(errors); mx = max_abs(errors)
    passed: Any = "diagnostic"
    if rmse_gate is not None and max_gate is not None:
        passed = bool(r <= rmse_gate and mx <= max_gate)
    return {
        "protocol": name,
        "set": set_name,
        "n": int(pd.to_numeric(errors, errors="coerce").dropna().shape[0]),
        "rmse_db": r,
        "mae_db": m,
        "max_abs_db": mx,
        "bias_db": float(pd.to_numeric(errors, errors="coerce").dropna().mean()) if len(pd.to_numeric(errors, errors="coerce").dropna()) else float("nan"),
        "rmse_gate_db": rmse_gate,
        "max_abs_gate_db": max_gate,
        "passed": passed,
        "interpretation": interpretation,
    }


def maybe_plot(pred: pd.DataFrame, lopo: pd.DataFrame, fig_dir: Path) -> None:
    if plt is None:
        return
    fig_dir.mkdir(parents=True, exist_ok=True)
    labels = [f"CS {int(p):+d} dBm" for p in pred["launch_power_dbm"].astype(int)]
    x = np.arange(len(labels))

    plt.figure(figsize=(10, 5))
    plt.bar(x - 0.18, pred["uncalibrated_error_db"], width=0.36, label="Uncalibrated")
    plt.bar(x + 0.18, pred["calibrated_error_db"], width=0.36, label="Calibrated")
    plt.axhline(0, linewidth=0.8)
    plt.xticks(x, labels, rotation=25, ha="right")
    plt.ylabel("GSNR error (dB)")
    plt.xlabel("C+S validation case")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "fig_day15_cs_uncalibrated_vs_calibrated_errors.png", dpi=180)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.scatter(pred["launch_power_dbm"], pred["needed_correction_db"], label="Needed correction")
    plt.plot(pred["launch_power_dbm"], pred["applied_correction_db"], label="Fitted correction")
    plt.axhline(0, linewidth=0.8)
    plt.xlabel("Launch power (dBm)")
    plt.ylabel("Reference - O-E-S-C-L GSNR (dB)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "fig_day15_cs_correction_vs_power.png", dpi=180)
    plt.close()

    if not lopo.empty:
        labels2 = [f"CS {int(p):+d} dBm" for p in lopo["heldout_power_dbm"].astype(int)]
        plt.figure(figsize=(9, 5))
        plt.bar(np.arange(len(labels2)), lopo["calibrated_error_db"], label="LOPO calibrated error")
        plt.axhline(0, linewidth=0.8)
        plt.xticks(np.arange(len(labels2)), labels2, rotation=25, ha="right")
        plt.ylabel("GSNR error (dB)")
        plt.xlabel("Held-out C+S power case")
        plt.legend()
        plt.tight_layout()
        plt.savefig(fig_dir / "fig_day15_cs_lopo_errors.png", dpi=180)
        plt.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/day15_cs_gnpy_calibrated_validation_config.yaml")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    oesc, oesc_source = load_oesc_cs_summary(cfg)
    ref, ref_type = load_or_derive_reference(cfg)

    for path_key in ["oesc_summary_csv", "reference_csv"]:
        ensure_parent(Path(cfg["outputs"][path_key]))
    oesc.to_csv(cfg["outputs"]["oesc_summary_csv"], index=False)
    ref.to_csv(cfg["outputs"]["reference_csv"], index=False)

    merged = pd.merge(
        oesc,
        ref,
        on=["scenario_group", "band", "spans", "launch_power_dbm"],
        how="inner",
    ).sort_values("launch_power_dbm")
    if merged.empty:
        raise RuntimeError("No matched C+S O-E-S-C-L/GNPy reference rows")

    merged["uncalibrated_error_db"] = merged["oesc_uniform_gsnr_mean_db"] - merged["reference_gsnr_db"]
    merged["needed_correction_db"] = merged["reference_gsnr_db"] - merged["oesc_uniform_gsnr_mean_db"]

    cs = cfg["cs_case"]
    cal_p = [float(x) for x in cs["calibration_powers_dbm"]]
    val_p = [float(x) for x in cs["validation_powers_dbm"]]
    cal = merged[merged["launch_power_dbm"].isin(cal_p)].copy()
    intercept, slope = fit_line(cal)
    merged["applied_correction_db"] = intercept + slope * merged["launch_power_dbm"].astype(float)
    merged["calibrated_oesc_gsnr_db"] = merged["oesc_uniform_gsnr_mean_db"] + merged["applied_correction_db"]
    merged["calibrated_error_db"] = merged["calibrated_oesc_gsnr_db"] - merged["reference_gsnr_db"]
    merged["abs_calibrated_error_db"] = merged["calibrated_error_db"].abs()
    merged["set"] = np.where(merged["launch_power_dbm"].isin(cal_p), "calibration", "heldout_validation")

    held = merged[merged["launch_power_dbm"].isin(val_p)].copy()

    # Leave-one-power-out on all available C+S powers.
    lopo_rows = []
    for held_power in sorted(merged["launch_power_dbm"].unique()):
        train = merged[merged["launch_power_dbm"] != held_power].copy()
        test = merged[merged["launch_power_dbm"] == held_power].copy()
        if train.empty or test.empty:
            continue
        a, b = fit_line(train)
        for _, r in test.iterrows():
            corr = a + b * float(r["launch_power_dbm"])
            pred = float(r["oesc_uniform_gsnr_mean_db"]) + corr
            lopo_rows.append({
                "heldout_power_dbm": float(r["launch_power_dbm"]),
                "oesc_uniform_gsnr_mean_db": float(r["oesc_uniform_gsnr_mean_db"]),
                "reference_gsnr_db": float(r["reference_gsnr_db"]),
                "applied_correction_db": corr,
                "calibrated_oesc_gsnr_db": pred,
                "calibrated_error_db": pred - float(r["reference_gsnr_db"]),
                "train_powers_dbm": ",".join(str(int(x)) if float(x).is_integer() else str(x) for x in sorted(train["launch_power_dbm"].unique())),
            })
    lopo = pd.DataFrame(lopo_rows)

    gates = cfg["validation_gates"]
    rows = []
    rows.append(summarize_protocol("cs_uncalibrated_reference", "all_cases", merged["uncalibrated_error_db"], gates["primary_rmse_gate_db"], gates["primary_max_abs_gate_db"], "Raw C+S comparison; expected to be difficult."))
    rows.append(summarize_protocol("cs_low_power_to_high_power_holdout", "calibration", merged[merged["set"] == "calibration"]["calibrated_error_db"], None, None, "Calibration fit quality only; not validation."))
    rows.append(summarize_protocol("cs_low_power_to_high_power_holdout", "heldout_validation", held["calibrated_error_db"], gates["primary_rmse_gate_db"], gates["primary_max_abs_gate_db"], "Primary C+S held-out calibrated validation."))
    if not lopo.empty:
        rows.append(summarize_protocol("cs_leave_one_power_out", "heldout_validation_all_folds", lopo["calibrated_error_db"], gates["lopo_rmse_gate_db"], gates["lopo_max_abs_gate_db"], "C+S cross-validation stability check."))
    protocol = pd.DataFrame(rows)

    for key in ["primary_predictions_csv", "lopo_predictions_csv", "protocol_summary_csv"]:
        ensure_parent(Path(cfg["outputs"][key]))
    merged.to_csv(cfg["outputs"]["primary_predictions_csv"], index=False)
    lopo.to_csv(cfg["outputs"]["lopo_predictions_csv"], index=False)
    protocol.to_csv(cfg["outputs"]["protocol_summary_csv"], index=False)

    maybe_plot(merged, lopo, Path(cfg["outputs"]["figures_dir"]))

    held_row = protocol[(protocol["protocol"] == "cs_low_power_to_high_power_holdout") & (protocol["set"] == "heldout_validation")].iloc[0]
    lopo_row = protocol[protocol["protocol"] == "cs_leave_one_power_out"].iloc[0] if (protocol["protocol"] == "cs_leave_one_power_out").any() else None
    overall = bool(held_row["passed"]) and (lopo_row is None or bool(lopo_row["passed"]))
    reference_warning = "true multiband/Raman-aware reference" if ref_type == "true_cs_reference" else "derived separable C+S baseline; not Raman/ISRS-aware"

    report = f"""# Day-15 C+S GNPy-Calibrated Validation Report

Day-15 extends calibrated validation to the C+S scenario.

## Reference type

- Reference type: `{ref_type}`
- Interpretation: `{reference_warning}`
- O-E-S-C-L source table: `{oesc_source}`

## Summary gate

- C+S calibrated held-out gate passed: `{bool(held_row['passed'])}`
- C+S held-out RMSE: `{fmt(held_row['rmse_db'])} dB`
- C+S held-out MAE: `{fmt(held_row['mae_db'])} dB`
- C+S held-out max absolute error: `{fmt(held_row['max_abs_db'])} dB`
- C+S LOPO gate passed: `{bool(lopo_row['passed']) if lopo_row is not None else 'not available'}`
- C+S LOPO RMSE: `{fmt(lopo_row['rmse_db']) if lopo_row is not None else 'not available'} dB`
- Overall C+S calibrated validation status: `{'passed' if overall else 'failed'}`

## Calibration model

```text
G_calibrated_CS(P) = G_OESC_CS(P) + a_CS + b_CS * P
```

- intercept a_CS: `{fmt(intercept)} dB`
- slope b_CS: `{fmt(slope)} dB/dBm`
- calibration powers: `{cal_p}`
- held-out validation powers: `{val_p}`

## Protocol summary

{protocol.to_markdown(index=False)}

## Predictions

{merged.to_markdown(index=False)}

## Correct manuscript claim

If the reference type is derived separable baseline, the manuscript may state only that the simplified C+S case was calibrated against a separable C/S GNPy-derived baseline. It must not claim full Raman/ISRS-aware C+S validation.

If a true multiband/Raman-aware C+S reference file is supplied and the gates pass, the manuscript may state calibrated C+S validation against that specific reference.
"""
    ensure_parent(Path(cfg["outputs"]["report"]))
    Path(cfg["outputs"]["report"]).write_text(report, encoding="utf-8")

    latex = f"""% Day-15 C+S calibrated validation snippet
\\subsection{{C+S Calibrated External-Reference Validation}}
The simplified C+S scenario was evaluated with a calibrated external-reference protocol. The C+S correction was modeled as
\\begin{{equation}}
G_{{\\mathrm{{cal}},CS}}(P)=G_{{\\mathrm{{OESCL}},CS}}(P)+a_{{CS}}+b_{{CS}}P,
\\end{{equation}}
where $P$ is the launch power in dBm. The fitted intercept and slope were {fmt(intercept)} dB and {fmt(slope)} dB/dBm, respectively. The held-out C+S validation RMSE was {fmt(held_row['rmse_db'])} dB and the maximum absolute error was {fmt(held_row['max_abs_db'])} dB. The reference used in this run was: {reference_warning}. Therefore, unless a true Raman/ISRS-aware C+S reference is supplied, this result should be described as separable-baseline calibrated alignment rather than full physical C+S validation.
"""
    ensure_parent(Path(cfg["outputs"]["latex_snippet"]))
    Path(cfg["outputs"]["latex_snippet"]).write_text(latex, encoding="utf-8")

    print("O-E-S-C-L Day-15 C+S calibrated validation completed.")
    print(f"Report: {Path(cfg['outputs']['report']).resolve()}")
    print(f"Protocol summary: {Path(cfg['outputs']['protocol_summary_csv']).resolve()}")
    print(f"Overall status: {'passed' if overall else 'failed'}")
    if ref_type != "true_cs_reference":
        print("WARNING: Reference is derived/separable, not full Raman/ISRS-aware C+S validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
