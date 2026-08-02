"""Audit available O-E-S-C-L simulation engine functions for confirmation-run integration."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "results" / "final" / "reports" / "confirmation_engine_audit_report.md"


MODULES = [
    "src.oescl.experiments",
    "src.oescl.day8_q3_band_comparison",
    "src.oescl.day6",
    "src.oescl.day5_waveform",
    "src.oescl.gmi_exact",
    "src.oescl.rate_metrics",
    "src.oescl.metrics",
    "src.oescl.constellation",
    "src.oescl.channel",
]


def main() -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Confirmation Engine Integration Audit")
    lines.append("")
    lines.append("Purpose: identify existing project functions that can be safely reused for final-confirmation jobs.")
    lines.append("")

    for module_name in MODULES:
        lines.append(f"## {module_name}")
        lines.append("")

        try:
            mod = importlib.import_module(module_name)
        except Exception as exc:
            lines.append(f"IMPORT FAILED: {type(exc).__name__}: {exc}")
            lines.append("")
            continue

        functions = []
        for name, obj in inspect.getmembers(mod, inspect.isfunction):
            if obj.__module__ == module_name:
                try:
                    sig = str(inspect.signature(obj))
                except Exception:
                    sig = "(signature unavailable)"
                functions.append((name, sig))

        if not functions:
            lines.append("No local functions found.")
        else:
            for name, sig in functions:
                lines.append(f"- `{name}{sig}`")

        lines.append("")

    lines.append("## Integration decision rule")
    lines.append("")
    lines.append("The confirmation runner should only be connected to a function if it can output:")
    lines.append("")
    lines.append("- scenario")
    lines.append("- stage")
    lines.append("- seed")
    lines.append("- symbols")
    lines.append("- nu")
    lines.append("- spans")
    lines.append("- launch_power_dbm")
    lines.append("- uniform_bmd_rate_bit_per_symbol")
    lines.append("- pcs_stored_score_bit_per_symbol")
    lines.append("- entropy_correction_bit_per_symbol")
    lines.append("- pcs_corrected_bmd_rate_bit_per_symbol")
    lines.append("- delta_corrected_bmd_gain_bit_per_symbol")
    lines.append("- ber_uniform")
    lines.append("- ber_pcs")
    lines.append("- gsnr_uniform_db")
    lines.append("- gsnr_pcs_db")
    lines.append("")
    lines.append("If no existing function provides these safely, create a dedicated final_confirmation engine adapter instead of modifying old Day-X code.")

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()