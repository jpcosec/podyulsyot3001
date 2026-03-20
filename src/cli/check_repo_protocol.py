from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[2]


def _git_status_porcelain() -> tuple[int, str, str]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check repository protocol compliance.")
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

    if args.require_clean_tree:
        code, stdout, stderr = _git_status_porcelain()
        if code != 0:
            errors.append(f"git status failed: {stderr.strip()}")
        else:
            lines = [line for line in stdout.splitlines() if line.strip()]
            if lines:
                errors.append("Uncommitted changes are not allowed:")
                errors.extend(f"  - working tree is dirty: {line}" for line in lines)

    if errors:
        print("Protocol check: FAILED")
        print()
        print("\n".join(errors))
        return 1

    print("Protocol check: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
