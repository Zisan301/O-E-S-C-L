from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "README.md",
    ".gitignore",
    "requirements.txt",
    "requirements-lock.txt",
    "scripts/smoke_test_reproducibility.py",
    "docs/PNC_REQUIREMENT_CLOSURE_CHECKLIST.md",
    "docs/NOVELTY_BASELINES_AND_VALIDATION_PLAN.md",
    "config/day14_independent_validation_matrix.yaml",
    "manuscript/main.tex",
    "manuscript/references.bib",
]


FORBIDDEN_TRACKED_PATTERNS = [
    "gnpy_env/",
    "site-packages/",
    "__pycache__/",
    ".pyc",
    ".pyo",
    ".joblib",
    "results/models/",
]


FORBIDDEN_CLAIMS = [
    "fully validated against GNPy",
    "raw GSNR directly matches GNPy",
    "experimentally validated",
    "field validated",
    "fully physical Manakov",
    "direct physical Manakov/NLSE simulator",
]


def git_ls_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


def check_required_files() -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            errors.append(f"Missing required file: {rel}")
    return errors


def check_tracked_junk(files: list[str]) -> list[str]:
    errors: list[str] = []
    for f in files:
        normalized = f.replace("\\", "/")
        for pattern in FORBIDDEN_TRACKED_PATTERNS:
            if pattern in normalized or normalized.endswith(pattern):
                errors.append(f"Forbidden tracked artifact: {f}")
                break
    return errors


def check_forbidden_claims() -> list[str]:
    errors: list[str] = []
    targets = [
        ROOT / "README.md",
        ROOT / "manuscript" / "main.tex",
        ROOT / "docs" / "PNC_REQUIREMENT_CLOSURE_CHECKLIST.md",
        ROOT / "docs" / "NOVELTY_BASELINES_AND_VALIDATION_PLAN.md",
    ]

    for path in targets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for phrase in FORBIDDEN_CLAIMS:
            if phrase.lower() in text:
                errors.append(f"Forbidden claim phrase found in {path.relative_to(ROOT)}: {phrase}")
    return errors


def main() -> None:
    errors: list[str] = []

    errors.extend(check_required_files())

    tracked_files = git_ls_files()
    errors.extend(check_tracked_junk(tracked_files))
    errors.extend(check_forbidden_claims())

    if errors:
        print("PNC submission-readiness check failed:")
        for err in errors:
            print(f"- {err}")
        raise SystemExit(1)

    print("PNC submission-readiness check passed.")
    print("Note: this does not mean the paper is ready to submit; it only checks repository hygiene and claim-control basics.")


if __name__ == "__main__":
    main()
