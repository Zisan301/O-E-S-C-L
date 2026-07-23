#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, re, subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
import pandas as pd
import numpy as np

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

C_LIGHT = 299792458.0


def ensure(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def f_center_from_nm(nm: float) -> float:
    return C_LIGHT / (nm * 1e-9)


def spectrum_band(center_nm: float, n_channels: int, slot_hz: float, baud_hz: float, tx_osnr: float = 40.0) -> Dict[str, Any]:
    fc = f_center_from_nm(center_nm)
    width = n_channels * slot_hz
    return {
        "f_min": fc - width / 2,
        "f_max": fc + width / 2,
        "baud_rate": baud_hz,
        "slot_width": slot_hz,
        "roll_off": 0.15,
        "tx_osnr": tx_osnr
    }


def loc(city: str, x: float) -> Dict[str, Any]:
    return {"location": {"city": city, "region": "", "latitude": float(x), "longitude": 0.0}}


def make_network(path: Path, spans: int, span_len: float, c_loss: float, s_loss: float, raman: bool = True) -> None:
    elems, conns = [], []
    tx, rx = "trx_A", "trx_B"
    elems.append({"uid": tx, "type": "Transceiver", "metadata": loc("Site_A", 0)})
    prev = tx
    # Use a frequency-dependent loss profile across S+C. 198-204 THz is S near 1490 nm; 190-196 THz is C near 1550 nm.
    loss_profile = {"value": [s_loss, s_loss, c_loss, c_loss], "frequency": [198e12, 204e12, 190e12, 196e12]}
    avg_loss = (c_loss + s_loss) / 2
    for i in range(1, spans + 1):
        fuid, euid = f"fiber_CS_{i}", f"edfa_CS_{i}"
        if raman:
            fiber = {
                "uid": fuid,
                "type": "RamanFiber",
                "type_variety": "SSMF",
                "params": {"length": span_len, "length_units": "km", "loss_coef": loss_profile, "con_in": 0, "con_out": 0},
                "metadata": loc(f"CS_RamanFiber_{i}", i)
            }
        else:
            fiber = {
                "uid": fuid,
                "type": "Fiber",
                "type_variety": "SSMF",
                "params": {"length": span_len, "length_units": "km", "loss_coef": avg_loss, "con_in": 0, "con_out": 0},
                "metadata": loc(f"CS_Fiber_{i}", i)
            }
        elems.append(fiber)
        # Target average span loss; true per-band tilt is left to Raman/ISRS-aware sim params.
        elems.append({
            "uid": euid,
            "type": "Edfa",
            "type_variety": "std_medium_gain",
            "operational": {"gain_target": avg_loss * span_len, "tilt_target": 0, "out_voa": 0},
            "metadata": loc(f"CS_EDFA_{i}", i + 0.1)
        })
        conns.append({"from_node": prev, "to_node": fuid})
        conns.append({"from_node": fuid, "to_node": euid})
        prev = euid
    elems.append({"uid": rx, "type": "Transceiver", "metadata": loc("Site_B", spans + 1)})
    conns.append({"from_node": prev, "to_node": rx})
    net = {"network_name": "O-E-S-C-L Day16 full C+S Raman/ISRS-aware validation", "elements": elems, "connections": conns}
    ensure(path); path.write_text(json.dumps(net, indent=2), encoding="utf-8")


def make_inputs(cfg: Dict[str, Any]) -> None:
    g = cfg["gnpy"]
    spectrum = {"spectrum": [
        spectrum_band(g["s_center_nm"], int(g["channels_per_band"]), float(g["slot_width_hz"]), float(g["baud_rate_hz"])),
        spectrum_band(g["c_center_nm"], int(g["channels_per_band"]), float(g["slot_width_hz"]), float(g["baud_rate_hz"])),
    ]}
    spath = Path(g["spectrum"]); ensure(spath); spath.write_text(json.dumps(spectrum, indent=2), encoding="utf-8")
    sim = {
        "raman_params": {"flag": True, "method": "perturbative", "order": 2, "result_spatial_resolution": 10000.0, "solver_spatial_resolution": 10000.0},
        "nli_params": {"method": "ggn_spectrally_separated"}
    }
    simpath = Path(g["sim_params"]); ensure(simpath); simpath.write_text(json.dumps(sim, indent=2), encoding="utf-8")
    make_network(Path(g["network_raman"]), int(g["spans"]), float(g["span_length_km"]), float(g["c_loss_db_per_km"]), float(g["s_loss_db_per_km"]), True)
    make_network(Path(g["network_regular_fallback"]), int(g["spans"]), float(g["span_length_km"]), float(g["c_loss_db_per_km"]), float(g["s_loss_db_per_km"]), False)

    logs = Path(g["log_dir"]); logs.mkdir(parents=True, exist_ok=True)
    network = g["network_raman"] if g.get("use_network", "raman") == "raman" else g["network_regular_fallback"]
    lines = ["$ErrorActionPreference = 'Stop'", ""]
    for p in g["powers_dbm"]:
        safe = str(p).replace("-", "m").replace(".", "p")
        log = f"{g['log_dir']}\\CS_{safe}dBm.txt"
        cmd = f"gnpy-transmission-example {network} -e {cfg['inputs']['gnpy_equipment']} --sim-params {g['sim_params']} --spectrum {g['spectrum']} --show-channels -po {p}"
        lines.append(f"Write-Host 'Running C+S Raman/ISRS case: {p} dBm'")
        lines.append(f"{cmd} *> {log}")
    pspath = Path("scripts/run_day16_gnpy_cs_raman_cases.ps1")
    ensure(pspath); pspath.write_text("\n".join(lines) + "\n", encoding="utf-8")

    template = Path(cfg["inputs"]["raman_reference_template_csv"])
    ensure(template)
    rows = []
    for p in g["powers_dbm"]:
        rows.append({"scenario_group": "C+S", "band": "C+S", "spans": g["spans"], "launch_power_dbm": p,
                     "reference_model": "GNPy Raman/ISRS", "reference_source": "GNPy full C+S Raman/ISRS-aware run",
                     "reference_gsnr_db": "", "reference_type": "gnpy_full_raman_isrs",
                     "notes": "Fill from receiver GSNR(signal bw) of combined C+S Raman/ISRS run"})
    pd.DataFrame(rows).to_csv(template, index=False)


def extract_gsnr_from_log(text: str) -> Optional[float]:
    # Prefer receiver summary after Transceiver trx_B.
    m = re.search(r"Transceiver\s+trx_B[\s\S]*?GSNR \(signal bw, dB\):\s*([+-]?\d+(?:\.\d+)?)", text)
    if m:
        return float(m.group(1))
    # Fallback: take final channel table central channel approximate average.
    vals = [float(x) for x in re.findall(r"\s\d+\s+\d+\.\d+\s+[+-]?\d+\.\d+\s+[+-]?\d+\.\d+\s+[+-]?\d+\.\d+\s+([+-]?\d+\.\d+)\s*$", text, flags=re.M)]
    if vals:
        return float(np.mean(vals))
    return None


def parse_logs(cfg: Dict[str, Any]) -> None:
    g = cfg["gnpy"]
    rows = []
    for p in g["powers_dbm"]:
        safe = str(p).replace("-", "m").replace(".", "p")
        log = Path(g["log_dir"]) / f"CS_{safe}dBm.txt"
        val = None; status="missing_log"
        if log.exists():
            text = log.read_text(errors="ignore", encoding="utf-8")
            val = extract_gsnr_from_log(text)
            status = "ok" if val is not None else "missing_gsnr_in_log"
        rows.append({"scenario_group": "C+S", "band": "C+S", "spans": g["spans"], "launch_power_dbm": p,
                     "reference_model": "GNPy Raman/ISRS", "reference_source": "GNPy full C+S Raman/ISRS-aware run",
                     "reference_gsnr_db": val, "reference_type": "gnpy_full_raman_isrs", "status": status,
                     "notes": "Receiver GSNR(signal bw) from combined C+S Raman/ISRS run"})
    out = Path(cfg["inputs"]["raman_reference_csv"]); ensure(out); pd.DataFrame(rows).to_csv(out, index=False)


def find_col(df: pd.DataFrame, names: List[str]) -> Optional[str]:
    lower = {c.lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    return None


def load_oesc_cs(cfg: Dict[str, Any]) -> pd.DataFrame:
    path = Path(cfg["inputs"]["oesc_cs_source_table"])
    if not path.exists():
        path = Path(cfg["inputs"]["fallback_oesc_cs_table"])
    if not path.exists():
        raise FileNotFoundError("Could not find C+S O-E-S-C-L source table. Run Day-8 or Day-15 first.")
    df = pd.read_csv(path)
    # day15 table has exactly needed values under oesc_uniform_gsnr_mean_db
    if "oesc_uniform_gsnr_mean_db" in df.columns and "launch_power_dbm" in df.columns:
        out = df.copy()
    else:
        group_col = find_col(df, ["scenario_group", "scenario", "band"])
        power_col = find_col(df, ["launch_power_dbm", "launch_power", "power_dbm"])
        gsnr_col = find_col(df, ["gsnr_db", "uniform_gsnr_db", "oesc_uniform_gsnr_mean_db", "gsnr_mean_db"])
        spans_col = find_col(df, ["spans", "n_spans"])
        seed_col = find_col(df, ["seed"])
        if group_col is None or power_col is None or gsnr_col is None:
            raise RuntimeError("Could not infer required columns from O-E-S-C-L C+S table.")
        temp = df[df[group_col].astype(str).str.lower().str.contains("c\+s|cs", regex=True)].copy()
        if temp.empty:
            temp = df.copy()
        gb = [power_col]
        if spans_col: gb.append(spans_col)
        agg = temp.groupby(gb)[gsnr_col].agg(["mean", "std", "count"]).reset_index()
        agg = agg.rename(columns={power_col:"launch_power_dbm", "mean":"oesc_uniform_gsnr_mean_db", "std":"oesc_uniform_gsnr_std_db", "count":"n_seeds"})
        if spans_col and spans_col != "spans": agg = agg.rename(columns={spans_col:"spans"})
        if "spans" not in agg.columns: agg["spans"] = cfg["gnpy"]["spans"]
        out = agg
    out = out[out["launch_power_dbm"].isin(cfg["gnpy"]["powers_dbm"])].copy()
    if "scenario_group" not in out.columns: out["scenario_group"] = "C+S"
    if "band" not in out.columns: out["band"] = "C+S"
    if "n_seeds" not in out.columns: out["n_seeds"] = np.nan
    return out[["launch_power_dbm","spans","oesc_uniform_gsnr_mean_db","oesc_uniform_gsnr_std_db","n_seeds","scenario_group","band"]].drop_duplicates("launch_power_dbm")


def fit_linear(x: np.ndarray, y: np.ndarray):
    # y = a + b*x
    b, a = np.polyfit(x, y, 1)
    return float(a), float(b)


def metrics(err: np.ndarray) -> Dict[str, float]:
    return {"n": len(err), "rmse_db": float(np.sqrt(np.mean(err**2))), "mae_db": float(np.mean(np.abs(err))), "max_abs_db": float(np.max(np.abs(err))), "bias_db": float(np.mean(err))}


def run_validation(cfg: Dict[str, Any]) -> int:
    report_path = Path(cfg["outputs"]["report"]); ensure(report_path)
    ref_path = Path(cfg["inputs"]["raman_reference_csv"])
    if not ref_path.exists():
        report_path.write_text("# Day-16 Full Raman/ISRS C+S Validation Report\n\nStatus: pending. Run --prepare, execute generated GNPy commands, then run --parse-logs.\n", encoding="utf-8")
        print("Day-16 pending: Raman/ISRS reference CSV is missing. Run with --prepare first.")
        return 2
    ref = pd.read_csv(ref_path)
    if "reference_gsnr_db" not in ref.columns or ref["reference_gsnr_db"].isna().any():
        report_path.write_text("# Day-16 Full Raman/ISRS C+S Validation Report\n\nStatus: pending. Some reference_gsnr_db values are missing.\n", encoding="utf-8")
        print("Day-16 pending: some reference_gsnr_db values are missing.")
        return 2
    if "reference_type" not in ref.columns or not ref["reference_type"].astype(str).str.contains("gnpy_full_raman_isrs").all():
        report_path.write_text("# Day-16 Full Raman/ISRS C+S Validation Report\n\nStatus: failed. reference_type must be gnpy_full_raman_isrs for all rows.\n", encoding="utf-8")
        print("Day-16 failed: reference_type is not gnpy_full_raman_isrs.")
        return 1
    oesc = load_oesc_cs(cfg)
    df = oesc.merge(ref, on=["launch_power_dbm", "spans"], how="inner", suffixes=("", "_ref"))
    if len(df) < 4:
        raise RuntimeError(f"Expected 4 matched C+S cases, got {len(df)}")
    df["uncalibrated_error_db"] = df["oesc_uniform_gsnr_mean_db"] - df["reference_gsnr_db"].astype(float)
    df["needed_correction_db"] = df["reference_gsnr_db"].astype(float) - df["oesc_uniform_gsnr_mean_db"]
    cal_p = cfg["validation"]["calibration_powers_dbm"]
    held_p = cfg["validation"]["heldout_powers_dbm"]
    cal = df[df["launch_power_dbm"].isin(cal_p)].copy(); held = df[df["launch_power_dbm"].isin(held_p)].copy()
    a,b = fit_linear(cal["launch_power_dbm"].to_numpy(float), cal["needed_correction_db"].to_numpy(float))
    df["applied_correction_db"] = a + b * df["launch_power_dbm"].astype(float)
    df["calibrated_oesc_gsnr_db"] = df["oesc_uniform_gsnr_mean_db"] + df["applied_correction_db"]
    df["calibrated_error_db"] = df["calibrated_oesc_gsnr_db"] - df["reference_gsnr_db"].astype(float)
    df["abs_calibrated_error_db"] = df["calibrated_error_db"].abs()
    df["set"] = np.where(df["launch_power_dbm"].isin(cal_p), "calibration", "heldout_validation")
    held_err = df[df["set"]=="heldout_validation"]["calibrated_error_db"].to_numpy(float)
    unc = metrics(df["uncalibrated_error_db"].to_numpy(float)); hm=metrics(held_err)
    hm_pass = hm["rmse_db"] <= cfg["validation"]["rmse_gate_db"] and hm["max_abs_db"] <= cfg["validation"]["max_abs_gate_db"]
    # LOPO
    lopo_rows=[]
    for p in sorted(df["launch_power_dbm"].unique()):
        train=df[df["launch_power_dbm"]!=p]; test=df[df["launch_power_dbm"]==p]
        aa,bb=fit_linear(train["launch_power_dbm"].to_numpy(float), train["needed_correction_db"].to_numpy(float))
        pred = test["oesc_uniform_gsnr_mean_db"].iloc[0] + aa + bb*float(p)
        err = pred - float(test["reference_gsnr_db"].iloc[0])
        lopo_rows.append({"launch_power_dbm":p,"calibrated_oesc_gsnr_db":pred,"reference_gsnr_db":float(test["reference_gsnr_db"].iloc[0]),"calibrated_error_db":err,"abs_calibrated_error_db":abs(err)})
    lopo=pd.DataFrame(lopo_rows); lm=metrics(lopo["calibrated_error_db"].to_numpy(float))
    lm_pass = lm["rmse_db"] <= cfg["validation"]["lopo_rmse_gate_db"] and lm["max_abs_db"] <= cfg["validation"]["lopo_max_abs_gate_db"]
    summary=pd.DataFrame([
        {"protocol":"cs_full_raman_uncalibrated","set":"all_cases","passed":False, **unc, "interpretation":"Raw full C+S Raman/ISRS GNPy reference comparison."},
        {"protocol":"cs_full_raman_low_power_to_high_power_holdout","set":"heldout_validation","passed":hm_pass, **hm, "interpretation":"Primary C+S full Raman/ISRS calibrated held-out validation."},
        {"protocol":"cs_full_raman_leave_one_power_out","set":"heldout_validation_all_folds","passed":lm_pass, **lm, "interpretation":"C+S full Raman/ISRS cross-validation stability check."},
    ])
    # outputs
    for key, obj in [("predictions", df), ("protocol_summary", summary), ("coefficients", pd.DataFrame([{"intercept_db":a,"slope_db_per_dbm":b,"calibration_powers_dbm":str(cal_p),"heldout_powers_dbm":str(held_p)}]))]:
        path=Path(cfg["outputs"][key]); ensure(path); obj.to_csv(path,index=False)
    if plt:
        # corrections
        fig,ax=plt.subplots(figsize=(9,5));
        ax.scatter(df["launch_power_dbm"], df["needed_correction_db"], label="Needed correction")
        xs=np.linspace(min(df["launch_power_dbm"]), max(df["launch_power_dbm"]), 100); ax.plot(xs, a+b*xs, label="Fitted correction")
        ax.axhline(0, lw=0.8); ax.set_xlabel("Launch power (dBm)"); ax.set_ylabel("Reference - O-E-S-C-L GSNR (dB)"); ax.legend(); fig.tight_layout();
        p=Path(cfg["outputs"]["figure_correction"]); ensure(p); fig.savefig(p,dpi=200); plt.close(fig)
        fig,ax=plt.subplots(figsize=(10,5)); x=np.arange(len(df)); ax.bar(x-0.2, df["uncalibrated_error_db"], width=0.4, label="Uncalibrated"); ax.bar(x+0.2, df["calibrated_error_db"], width=0.4, label="Calibrated"); ax.axhline(0,lw=0.8); ax.set_xticks(x); ax.set_xticklabels([f"CS {p:+g} dBm" for p in df["launch_power_dbm"]], rotation=25, ha="right"); ax.set_ylabel("GSNR error (dB)"); ax.legend(); fig.tight_layout(); p=Path(cfg["outputs"]["figure_errors"]); ensure(p); fig.savefig(p,dpi=200); plt.close(fig)
        fig,ax=plt.subplots(figsize=(8,5)); x=np.arange(len(lopo)); ax.bar(x,lopo["calibrated_error_db"]); ax.axhline(0,lw=0.8); ax.set_xticks(x); ax.set_xticklabels([f"CS {p:+g} dBm" for p in lopo["launch_power_dbm"]], rotation=25, ha="right"); ax.set_ylabel("GSNR error (dB)"); fig.tight_layout(); p=Path(cfg["outputs"]["figure_lopo"]); ensure(p); fig.savefig(p,dpi=200); plt.close(fig)
    latex = f"""% Day-16 full Raman/ISRS-aware C+S validation snippet
The C+S scenario was evaluated using a combined C+S GNPy reference with Raman/ISRS-aware simulation settings. The calibrated held-out RMSE was {hm['rmse_db']:.4f} dB and the maximum absolute held-out error was {hm['max_abs_db']:.4f} dB. Leave-one-power-out validation produced an RMSE of {lm['rmse_db']:.4f} dB.
"""
    lp=Path(cfg["outputs"]["latex_snippet"]); ensure(lp); lp.write_text(latex,encoding="utf-8")
    status="passed" if hm_pass and lm_pass else "failed"
    report=f"""# Day-16 Full Raman/ISRS-Aware C+S Validation Report

## Reference type

- Reference type: `gnpy_full_raman_isrs`
- Interpretation: combined C+S GNPy reference with Raman/ISRS-aware simulation settings.

## Summary gate

- Full C+S Raman/ISRS calibrated held-out gate passed: `{hm_pass}`
- Held-out RMSE: `{hm['rmse_db']:.4f} dB`
- Held-out MAE: `{hm['mae_db']:.4f} dB`
- Held-out max absolute error: `{hm['max_abs_db']:.4f} dB`
- LOPO gate passed: `{lm_pass}`
- LOPO RMSE: `{lm['rmse_db']:.4f} dB`
- Overall status: `{status}`

## Calibration model

```text
G_calibrated_CS_full_Raman(P) = G_OESC_CS(P) + a_CS + b_CS * P
```

- intercept a_CS: `{a:.4f} dB`
- slope b_CS: `{b:.4f} dB/dBm`
- calibration powers: `{cal_p}`
- held-out validation powers: `{held_p}`

## Correct manuscript claim

If this report passed, the manuscript may state calibrated C+S validation against a combined Raman/ISRS-aware GNPy reference. It should still mention calibration and should not describe the raw uncalibrated C+S result as direct agreement.
"""
    report_path.write_text(report,encoding="utf-8")
    print("O-E-S-C-L Day-16 full Raman/ISRS C+S validation completed.")
    print(f"Report: {report_path.resolve()}")
    print(f"Overall status: {status}")
    return 0 if status=="passed" else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/day16_cs_full_raman_isrs_config.yaml")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--parse-logs", action="store_true")
    args=ap.parse_args()
    cfg=yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.prepare:
        make_inputs(cfg)
        print("Prepared Day-16 Raman/ISRS GNPy input files and PowerShell runner.")
        print("Next: powershell -ExecutionPolicy Bypass -File scripts\\run_day16_gnpy_cs_raman_cases.ps1")
        return 0
    if args.parse_logs:
        parse_logs(cfg)
        print(f"Parsed logs into {cfg['inputs']['raman_reference_csv']}")
        return 0
    return run_validation(cfg)

if __name__ == "__main__":
    raise SystemExit(main())
