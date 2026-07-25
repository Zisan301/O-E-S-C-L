from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from oescl.rate_metrics import achievable_rate_tbps, achievable_rate_gain_tbps  # noqa: E402


def test_achievable_rate_tbps_formula() -> None:
    # 4 bit/symbol * 64 Gbaud * 2 polarizations = 512 Gb/s = 0.512 Tb/s.
    assert abs(achievable_rate_tbps(4.0, 64.0, 2) - 0.512) < 1e-12


def test_achievable_rate_gain_tbps_formula() -> None:
    # 0.05 bit/symbol gain at 64 Gbaud and dual polarization = 0.0064 Tb/s.
    gain = achievable_rate_gain_tbps(3.70, 3.65, 64.0, 2)
    assert abs(gain - 0.0064) < 1e-12
