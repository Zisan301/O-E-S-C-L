"""Generate entropy-corrected final C/S/C+S project outputs."""

from __future__ import annotations

import csv
from pathlib import Path

from oescl.final_outputs.entropy_corrected_bmd import build_publication_band_results


ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "results" / "final" / "tables"
REPORT_DIR = ROOT / "results" / "final" / "reports"


def fmt(x: float | None, digits: int = 4) -> str:
    if x is None:
        return ""
    return f"{x:.{digits}f}"


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    results = build_publication_band_results()

    csv_path = TABLE_DIR / "entropy_corrected_band_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "scenario",
                "nu",
                "spans",
                "launch_power_dbm",
                "stored_score_gain_bit_per_symbol",
                "entropy_correction_bit_per_symbol",
                "corrected_bmd_gain_bit_per_symbol",
                "corrected_bmd_ci95_bit_per_symbol",
                "rate_gain_gbps_per_representative_channel",
                "rate_gain_ci95_gbps_per_representative_channel",
                "aggregate_rate_gain_gbps",
                "aggregate_rate_gain_ci95_gbps",
            ],
        )
        writer.writeheader()
        for r in results:
            writer.writerow({
                "scenario": r.scenario,
                "nu": r.nu,
                "spans": r.spans,
                "launch_power_dbm": r.launch_power_dbm,
                "stored_score_gain_bit_per_symbol": fmt(r.stored_score_gain_bit_per_symbol, 6),
                "entropy_correction_bit_per_symbol": fmt(r.entropy_correction_bit_per_symbol, 5),
                "corrected_bmd_gain_bit_per_symbol": fmt(r.corrected_bmd_gain_bit_per_symbol, 6),
                "corrected_bmd_ci95_bit_per_symbol": fmt(r.corrected_bmd_ci95_bit_per_symbol, 4),
                "rate_gain_gbps_per_representative_channel": fmt(r.rate_gain_gbps_per_representative_channel, 3),
                "rate_gain_ci95_gbps_per_representative_channel": fmt(r.rate_gain_ci95_gbps_per_representative_channel, 3),
                "aggregate_rate_gain_gbps": fmt(r.aggregate_rate_gain_gbps, 3),
                "aggregate_rate_gain_ci95_gbps": fmt(r.aggregate_rate_gain_ci95_gbps, 3),
            })

    report_path = REPORT_DIR / "entropy_corrected_band_results_report.md"
    lines = []
    lines.append("# Entropy-Corrected C/S/C+S Band Results")
    lines.append("")
    lines.append("This report converts the stored Day-8 demapper-score gains into entropy-corrected BMD-rate gains.")
    lines.append("")
    lines.append("Correction used for nu = 0.36: 0.02961 bit/symbol.")
    lines.append("")
    lines.append("| Scenario | nu | Spans | Power dBm | Stored score gain | Corrected BMD gain | 95% CI | Rate gain Gbit/s | Aggregate Gbit/s |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in results:
        lines.append(
            f"| {r.scenario} | {r.nu:.2f} | {r.spans} | {r.launch_power_dbm:g} | "
            f"{r.stored_score_gain_bit_per_symbol:.4f} | "
            f"{r.corrected_bmd_gain_bit_per_symbol:.4f} | "
            f"+/- {r.corrected_bmd_ci95_bit_per_symbol:.4f} | "
            f"{r.rate_gain_gbps_per_representative_channel:.2f} | "
            f"{fmt(r.aggregate_rate_gain_gbps, 2)} |"
        )
    lines.append("")
    lines.append("Claim boundary: these are entropy-corrected discovery-stage results. Larger-symbol confirmation remains strongest for S, borderline for C, and exploratory for C+S shaping.")

    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
