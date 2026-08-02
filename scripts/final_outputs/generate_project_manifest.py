"""Generate final project manifest for publication-grade traceability."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = ROOT / "results" / "final" / "manifests"
REPORT_DIR = ROOT / "results" / "final" / "reports"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(path_text: str) -> dict[str, Any]:
    path = ROOT / path_text
    return {
        "path": path_text.replace("\\", "/"),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def run_git(args: list[str]) -> str:
    try:
        out = subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
        return out.strip()
    except Exception:
        return ""


def read_csv_rows(path_text: str) -> list[dict[str, str]]:
    path = ROOT / path_text
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def build_manifest() -> dict[str, Any]:
    entropy_rows = read_csv_rows("results/final/tables/entropy_corrected_band_results.csv")
    day16_reference_rows = read_csv_rows("validation_data/gnpy_day16_cs_raman_reference.csv")
    day16_protocol_rows = read_csv_rows("results/tables/day16_cs_full_raman_protocol_summary.csv")

    key_files = [
        "src/oescl/final_outputs/entropy_corrected_bmd.py",
        "scripts/final_outputs/generate_entropy_corrected_band_results.py",
        "scripts/final_outputs/check_entropy_corrected_outputs.py",
        "results/final/tables/entropy_corrected_band_results.csv",
        "results/final/reports/entropy_corrected_band_results_report.md",
        "validation_data/gnpy_day16_cs_raman_reference.csv",
        "results/tables/day16_cs_full_raman_protocol_summary.csv",
        "results/reports/day16_cs_full_raman_isrs_validation_report.md",
        "results/reports/day13_model_alignment_report.md",
        "results/reports/day10_publication_validation_report.md",
        "results/reports/day8_q3_acceptance_report.md",
        "results/topology_verify/reports/day16_topology_decision.md",
        "results/topology_verify/reports/day16_ramanfiber_failed_attempt.md",
        "results/topology_verify/tables/day16_original_reference_topology_rows.csv",
    ]

    manifest: dict[str, Any] = {
        "manifest_schema": "oescl-final-project-manifest-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "repository": {
            "git_commit": run_git(["rev-parse", "HEAD"]),
            "git_branch": run_git(["branch", "--show-current"]),
            "git_status_short": run_git(["status", "--short"]),
            "last_five_commits": run_git(["log", "--oneline", "-5"]).splitlines(),
        },
        "final_claim_boundaries": {
            "pcs_rate_claim": "Use entropy-corrected BMD-rate differences, not old uncorrected demapper-score gains.",
            "c_band_claim": "Positive discovery-stage entropy-corrected gain; larger-symbol confirmation is borderline and should be described cautiously.",
            "s_band_claim": "Strongest confirmed internal entropy-corrected shaping result.",
            "cs_band_claim": "Exploratory internal C+S shaping result unless replaced by full ISRS-aware multichannel PCS validation.",
            "gnpy_claim": "Calibrated GNPy alignment within tested configurations; not raw digital-twin accuracy.",
            "raman_claim": "Ordinary Fiber topology with Raman/SRS-enabled GNPy simulation settings; not pump-amplified RamanFiber validation.",
        },
        "final_entropy_corrected_band_results": entropy_rows,
        "day16_gnpy_reference_rows": day16_reference_rows,
        "day16_protocol_summary_rows": day16_protocol_rows,
        "claim_to_source_traceability": [
            {
                "claim_id": "PCS-C-S-CS-entropy-corrected",
                "claim": "C, S, and C+S outputs are reported using entropy-corrected BMD-rate gains.",
                "source_script": "scripts/final_outputs/generate_entropy_corrected_band_results.py",
                "source_module": "src/oescl/final_outputs/entropy_corrected_bmd.py",
                "output_table": "results/final/tables/entropy_corrected_band_results.csv",
                "output_report": "results/final/reports/entropy_corrected_band_results_report.md",
                "checker": "scripts/final_outputs/check_entropy_corrected_outputs.py",
                "boundary": "Discovery-stage values; final confirmation remains strongest for S, borderline for C, exploratory for C+S.",
            },
            {
                "claim_id": "DAY16-CS-GNPY-topology",
                "claim": "Day-16 C+S GNPy reference uses ordinary Fiber with Raman/SRS simulation settings, not pump-amplified RamanFiber.",
                "reference_csv": "validation_data/gnpy_day16_cs_raman_reference.csv",
                "topology_report": "results/topology_verify/reports/day16_topology_decision.md",
                "failure_report": "results/topology_verify/reports/day16_ramanfiber_failed_attempt.md",
                "boundary": "RamanFiber attempt failed because operational parameters were missing.",
            },
            {
                "claim_id": "DAY16-CS-calibrated-GNPY-alignment",
                "claim": "C+S calibrated held-out GNPy alignment is supported by Day-16 protocol summary.",
                "protocol_summary": "results/tables/day16_cs_full_raman_protocol_summary.csv",
                "report": "results/reports/day16_cs_full_raman_isrs_validation_report.md",
                "boundary": "Calibrated alignment only; not uncalibrated direct agreement or experimental validation.",
            },
            {
                "claim_id": "DAY13-single-band-calibrated-GNPY-alignment",
                "claim": "Single-band C/S calibrated held-out GNPy alignment is supported by Day-13 report.",
                "report": "results/reports/day13_model_alignment_report.md",
                "boundary": "Band-dependent launch-power calibration; raw direct agreement failed.",
            },
        ],
        "file_inventory": [file_record(p) for p in key_files],
        "next_required_project_improvements": [
            "Replace exploratory C+S lumped stress result with ISRS-aware multichannel PCS evaluation.",
            "Expand confirmation seeds and symbol counts for C, S, and C+S.",
            "Expand GNPy validation across powers, spans, loadings, and fiber profiles.",
            "Build physically parameterized SSFM or Manakov validation branch.",
            "Add ablation studies and final one-command reproduction pipeline.",
        ],
    }

    return manifest


def write_markdown_report(manifest: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Final Project Manifest Summary")
    lines.append("")
    lines.append("## Repository")
    lines.append("")
    lines.append(f"Branch: {manifest["repository"]["git_branch"]}")
    lines.append(f"Commit: {manifest["repository"]["git_commit"]}")
    lines.append("")
    lines.append("## Final claim boundaries")
    lines.append("")
    for key, value in manifest["final_claim_boundaries"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Entropy-corrected final band results")
    lines.append("")
    lines.append("| Scenario | nu | Spans | Power dBm | Corrected BMD gain | CI95 | Rate Gbit/s | Aggregate Gbit/s |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in manifest["final_entropy_corrected_band_results"]:
        lines.append(
            f"| {row.get("scenario", "")} | {row.get("nu", "")} | {row.get("spans", "")} | "
            f"{row.get("launch_power_dbm", "")} | {row.get("corrected_bmd_gain_bit_per_symbol", "")} | "
            f"{row.get("corrected_bmd_ci95_bit_per_symbol", "")} | "
            f"{row.get("rate_gain_gbps_per_representative_channel", "")} | "
            f"{row.get("aggregate_rate_gain_gbps", "")} |"
        )
    lines.append("")
    lines.append("## Claim-to-source traceability")
    lines.append("")
    for item in manifest["claim_to_source_traceability"]:
        lines.append(f"### {item["claim_id"]}")
        lines.append("")
        lines.append(f"Claim: {item["claim"]}")
        lines.append("")
        lines.append(f"Boundary: {item["boundary"]}")
        lines.append("")
    lines.append("## File inventory check")
    lines.append("")
    lines.append("| File | Exists | SHA256 |")
    lines.append("|---|---:|---|")
    for item in manifest["file_inventory"]:
        sha = item["sha256"] if item["sha256"] is not None else ""
        lines.append(f"| {item["path"]} | {item["exists"]} | {sha} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest()
    json_path = MANIFEST_DIR / "project_manifest.json"
    md_path = REPORT_DIR / "project_manifest_report.md"

    json_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_markdown_report(manifest, md_path)

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
