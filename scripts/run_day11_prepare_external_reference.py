from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def is_blank_series(s: pd.Series) -> bool:
    return s.isna().all() or s.astype(str).str.strip().eq("").all()


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare Day-11 external reference request.")
    parser.add_argument(
        "--day10-config",
        default="config/day10_c_stronger_validation_config.yaml",
        help="Day-10 config used for the accepted stability run.",
    )
    args = parser.parse_args()

    day10_config_path = PROJECT_ROOT / args.day10_config
    base_raw_path = PROJECT_ROOT / "results/tables/day10_raw_per_seed_metrics.csv"

    if not day10_config_path.exists():
        raise FileNotFoundError(f"Missing Day-10 config: {day10_config_path}")

    if not base_raw_path.exists():
        raise FileNotFoundError(
            "Missing Day-10 raw metrics. Run Day-10 first: "
            "python scripts/run_day10_publication_validation.py --config config/day10_c_stronger_validation_config.yaml"
        )

    day10_cfg = load_yaml(day10_config_path)
    base_cfg = load_yaml(PROJECT_ROOT / day10_cfg.get("base_config", "config/day8_q3_band_comparison_config.yaml"))

    d10 = day10_cfg["day10"]
    largest_symbol = int(max(d10["symbol_counts"]))
    steps = int(d10["ssfm_steps_per_span"])

    raw = pd.read_csv(base_raw_path)

    rows = []
    for p in d10["accepted_points"]:
        scenario = str(p["scenario_group"])
        spans = int(p["spans"])
        launch_power = float(p["launch_power_dbm"])

        filt = (
            (raw["scenario_group"].astype(str) == scenario)
            & (raw["spans"].astype(int) == spans)
            & (raw["launch_power_dbm"].astype(float) == launch_power)
            & (raw["symbol_count"].astype(int) == largest_symbol)
            & (raw["ssfm_steps_per_span"].astype(int) == steps)
            & (raw["scenario"].astype(str) == "uniform_raw")
        )

        matched = raw[filt].copy()
        if matched.empty:
            oescl_gsnr = ""
            oescl_note = "No matching O-E-S-C-L uniform rows found."
        else:
            oescl_gsnr = float(matched["gsnr_db"].astype(float).mean())
            oescl_note = f"Mean over {matched.shape[0]} seeds. For orientation only; do not copy as external reference."

        if scenario == "C":
            bands = ["C"]
        elif scenario == "S":
            bands = ["S"]
        elif scenario == "C+S":
            bands = ["C", "S"]
        else:
            bands = [scenario]

        for band in bands:
            band_cfg = base_cfg["bands"].get(band, {})
            rows.append({
                "scenario_group": scenario,
                "band": band,
                "spans": spans,
                "span_length_km": float(base_cfg["simulation"]["span_length_km"]),
                "launch_power_dbm": launch_power,
                "baud_rate_gbaud": float(base_cfg["simulation"]["baud_rate_gbaud"]),
                "channel_spacing_ghz": float(base_cfg["simulation"]["channel_spacing_ghz"]),
                "center_nm": band_cfg.get("center_nm", ""),
                "attenuation_db_per_km": band_cfg.get("attenuation_db_per_km", ""),
                "dispersion_ps_nm_km": band_cfg.get("dispersion_ps_nm_km", ""),
                "noise_figure_db": band_cfg.get("noise_figure_db", ""),
                "gamma_w_inv_km": base_cfg["fiber"].get("gamma_w_inv_km", ""),
                "reference_model": "GNPy",
                "reference_gsnr_db": "",
                "oescl_uniform_gsnr_db_for_orientation_only": oescl_gsnr,
                "notes": oescl_note,
            })

    request_df = pd.DataFrame(rows)

    validation_dir = PROJECT_ROOT / "validation_data"
    reports_dir = PROJECT_ROOT / "results/reports"
    validation_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    request_csv = validation_dir / "day11_external_reference_request.csv"
    expected_csv = validation_dir / "gnpy_day10_reference.csv"
    report_md = reports_dir / "day11_external_reference_request.md"

    request_df.to_csv(request_csv, index=False)

    expected_cols = [
        "scenario_group",
        "band",
        "spans",
        "launch_power_dbm",
        "reference_model",
        "reference_gsnr_db",
        "notes",
    ]
    expected_df = request_df[expected_cols].copy()
    expected_df["notes"] = "Fill reference_gsnr_db using independent GNPy/GN/EGN output."

    write_expected = True
    if expected_csv.exists():
        old = pd.read_csv(expected_csv)
        if "reference_gsnr_db" in old.columns and not is_blank_series(old["reference_gsnr_db"]):
            write_expected = False

    if write_expected:
        expected_df.to_csv(expected_csv, index=False)

    report = []
    report.append("# Day-11 External Reference Request")
    report.append("")
    report.append("Day-11 prepares the external GSNR reference input for the accepted Day-10 stability case.")
    report.append("")
    report.append("Important: do not copy O-E-S-C-L GSNR into `reference_gsnr_db`. That value is printed only for orientation.")
    report.append("")
    report.append("## Files generated")
    report.append(f"- `{request_csv.relative_to(PROJECT_ROOT)}`")
    report.append(f"- `{expected_csv.relative_to(PROJECT_ROOT)}`")
    report.append("")
    report.append("## Reference request")
    report.append(request_df.to_markdown(index=False))
    report.append("")
    report.append("## Next action")
    report.append("Run an independent GNPy/GN/EGN model for the listed case, fill `reference_gsnr_db`, then rerun Day-10 validation.")

    report_md.write_text("\n".join(report), encoding="utf-8")

    print("Day-11 external reference request prepared.")
    print(f"Request CSV: {request_csv}")
    print(f"Expected Day-10 reference CSV: {expected_csv}")
    print(f"Report: {report_md}")


if __name__ == "__main__":
    main()
