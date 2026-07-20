"""
tests/test_figures.py
=====================
Static checks that plotting functions do not use random generated values.
"""

from pathlib import Path

import src.utils as utils


def test_utils_module_has_no_random_plotting_calls():
    source = Path(utils.__file__).read_text(encoding="utf-8")
    assert "np.random" not in source
    assert "random." not in source
