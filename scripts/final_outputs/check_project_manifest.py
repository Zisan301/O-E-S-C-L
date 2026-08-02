"""Check final project manifest integrity."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "results" / "final" / "manifests" / "project_manifest.json"


def main() -> None:
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Missing manifest: {MANIFEST}")

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    required_top_keys = [
        "manifest_schema",
        "repository",
        "final_claim_boundaries",
        "final_entropy_corrected_band_results",
        "claim_to_source_traceability",
        "file_inventory",
    ]

    for key in required_top_keys:
        if key not in data:
            raise AssertionError(f"Missing manifest key: {key}")

    scenarios = {row.get("scenario") for row in data["final_entropy_corrected_band_results"]}
    for scenario in ["C", "S", "C+S"]:
        if scenario not in scenarios:
            raise AssertionError(f"Missing final band scenario: {scenario}")

    missing_files = [item["path"] for item in data["file_inventory"] if not item["exists"]]
    allowed_missing = set()
    unexpected_missing = [p for p in missing_files if p not in allowed_missing]

    if unexpected_missing:
        raise AssertionError("Missing expected files: " + ", ".join(unexpected_missing))

    claim_ids = {item["claim_id"] for item in data["claim_to_source_traceability"]}
    required_claims = {
        "PCS-C-S-CS-entropy-corrected",
        "DAY16-CS-GNPY-topology",
        "DAY16-CS-calibrated-GNPY-alignment",
    }
    missing_claims = required_claims - claim_ids
    if missing_claims:
        raise AssertionError("Missing claim IDs: " + ", ".join(sorted(missing_claims)))

    print("PASS: final project manifest contains required claims, files, and final band outputs.")


if __name__ == "__main__":
    main()
