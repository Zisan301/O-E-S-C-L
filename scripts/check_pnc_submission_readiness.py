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
    "docs/PHYSICAL_MODEL_CLARIFICATION.md",
    "docs/PNC_FINAL_REQUIREMENT_STATUS.md",
    "docs/PNC_SUBMISSION_SCOPE_FREEZE.md",
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


RISKY_CLAIM_PHRASES = [
    "fully validated against gnpy",
    "raw gsnr directly matches gnpy",
    "experimentally validated",
    "field validated",
    "fully physical manakov",
    "direct physical manakov/nlse simulator",
    "raw absolute gnpy validation",
]


NEGATION_OR_WARNING_MARKERS = [
    "do not",
    "not ",
    "not:",
    "not as",
    "should not",
    "must not",
    "avoid",
    "forbidden",
    "never",
    "rather than",
    "no laboratory",
    "no field",
    "not claim",
    "not claimed",
    "not be interpreted",
    "does not support",
    "without",
    "unless",
]


CLAIM_TARGETS = [
    "README.md",
    "manuscript/main.tex",
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


def is_warning_or_negated_line(line: str) -> bool:
    lower = line.lower()
    return any(marker in lower for marker in NEGATION_OR_WARNING_MARKERS)


def check_risky_positive_claims() -> list[str]:
    errors: list[str] = []

    for rel in CLAIM_TARGETS:
        path = ROOT / rel
        if not path.exists():
            continue

        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()

        for line_no, line in enumerate(lines, start=1):
            lower = line.lower()

            if is_warning_or_negated_line(lower):
                continue

            for phrase in RISKY_CLAIM_PHRASES:
                if phrase in lower:
                    errors.append(
                        f"Risky positive claim in {rel}:{line_no}: {phrase}"
                    )

    return errors


def main() -> None:
    errors: list[str] = []

    errors.extend(check_required_files())

    tracked_files = git_ls_files()
    errors.extend(check_tracked_junk(tracked_files))
    errors.extend(check_risky_positive_claims())

    if errors:
        print("PNC submission-readiness check failed:")
        for err in errors:
            print(f"- {err}")
        raise SystemExit(1)

    print("PNC submission-readiness check passed.")
    print(
        "Note: this does not mean the paper is ready to submit; "
        "it only checks repository hygiene and claim-control basics."
    )


if __name__ == "__main__":
    main()
