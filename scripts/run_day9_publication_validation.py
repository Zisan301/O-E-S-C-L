from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.oescl.config import load_config
from src.oescl.day9_validation import run_day9_publication_validation
from src.oescl.utils import set_global_seed


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Day-9 publication-strength validation outputs for O-E-S-C-L.")
    parser.add_argument("--config", default="config/day9_validation_config.yaml", help="Path to Day-9 YAML config.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    set_global_seed(int(cfg["simulation"]["seed"]))
    bundle = run_day9_publication_validation(cfg)

    print("\nO-E-S-C-L Day-9 publication validation completed.")
    print("\nReports:")
    for name, path in bundle["reports"].items():
        print(f"- {name}: {Path(path).resolve()}")
    print("\nTables:")
    for name, path in bundle["tables"].items():
        print(f"- {name}: {Path(path).resolve()}")
    print("\nFigures:")
    for name, path in bundle["figures"].items():
        print(f"- {name}: {Path(path).resolve()}")


if __name__ == "__main__":
    main()
