from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES: tuple[str, ...] = (
    "src/DEPENDENCY_GRAPH.md",
    "src/core/README.md",
    "src/ai/README.md",
    "src/nodes/README.md",
    "src/cli/README.md",
    "src/interfaces/api/README.md",
    "apps/review-workbench/README.md",
)

DOCS_FORBIDDEN_MARKERS: tuple[str, ...] = (
    "## b) target-state",
    "status: proposed",
    "future hardening",
    "todo backlog",
)


def _tracked_data_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "data/**"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return [f"git ls-files failed: {result.stderr.strip()}"]
    return [line for line in result.stdout.splitlines() if line.strip()]


def _missing_required_files() -> list[str]:
    missing: list[str] = []
    for rel in REQUIRED_FILES:
        if not (REPO_ROOT / rel).exists():
            missing.append(rel)
    return missing


def _git_status_porcelain() -> tuple[int, str, str]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def _docs_violations() -> list[str]:
    violations: list[str] = []
    docs_root = REPO_ROOT / "docs"
    for path in docs_root.rglob("*.md"):
        text = path.read_text(encoding="utf-8").lower()
        for marker in DOCS_FORBIDDEN_MARKERS:
            if marker in text:
                violations.append(
                    f"{path.relative_to(REPO_ROOT)} contains marker: {marker}"
                )
    return violations


def _clean_tree_violations() -> list[str]:
    code, stdout, stderr = _git_status_porcelain()
    if code != 0:
        return [f"git status failed: {stderr.strip()}"]
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines:
        return []
    return [f"working tree is dirty: {line}" for line in lines]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check repository protocol compliance."
    )
    parser.add_argument(
        "--require-clean-tree",
        action="store_true",
        help="Fail if there are any tracked/untracked local changes.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    errors: list[str] = []

    tracked_data = _tracked_data_files()
    if tracked_data:
        errors.append("Tracked files under data/ are not allowed:")
        errors.extend(f"  - {item}" for item in tracked_data)

    missing = _missing_required_files()
    if missing:
        errors.append("Missing required code-adjacent docs:")
        errors.extend(f"  - {item}" for item in missing)

    docs_violations = _docs_violations()
    if docs_violations:
        errors.append("Docs contain planning/target-state markers:")
        errors.extend(f"  - {item}" for item in docs_violations)

    if args.require_clean_tree:
        clean_tree_violations = _clean_tree_violations()
        if clean_tree_violations:
            errors.append("Uncommitted changes are not allowed:")
            errors.extend(f"  - {item}" for item in clean_tree_violations)

    if errors:
        print("Protocol check: FAILED")
        print()
        print("\n".join(errors))
        return 1

    print("Protocol check: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
