from __future__ import annotations

import argparse
from pathlib import Path


PRE_COMMIT_CONFIG = """repos:
  - repo: local
    hooks:
      - id: repo-protocol
        name: Repository protocol check
        entry: python -m src.cli.check_repo_protocol
        language: system
        pass_filenames: false
        stages: [pre-commit]

      - id: clean-tree-before-push
        name: Require clean tree before push
        entry: python -m src.cli.check_repo_protocol --require-clean-tree
        language: system
        pass_filenames: false
        stages: [pre-push]
"""

HOOK_PRE_COMMIT = """#!/usr/bin/env bash
set -euo pipefail

python -m src.cli.check_repo_protocol
"""

HOOK_PRE_PUSH = """#!/usr/bin/env bash
set -euo pipefail

python -m src.cli.check_repo_protocol --require-clean-tree
"""

WORKFLOW = """name: Repo Protocol

on:
  push:
    branches: [\"**\"]
  pull_request:

jobs:
  protocol:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: \"3.13\"

      - name: Protocol gate
        run: python -m src.cli.check_repo_protocol
"""

CHECKER = """from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[2]


def _git_status_porcelain() -> tuple[int, str, str]:
    result = subprocess.run(
        [\"git\", \"status\", \"--porcelain\"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def _tracked_data_files() -> list[str]:
    result = subprocess.run(
        [\"git\", \"ls-files\", \"data/**\"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return [f\"git ls-files failed: {result.stderr.strip()}\"]
    return [line for line in result.stdout.splitlines() if line.strip()]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=\"Check repository protocol compliance.\")
    parser.add_argument(
        \"--require-clean-tree\",
        action=\"store_true\",
        help=\"Fail if there are any tracked/untracked local changes.\",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    errors: list[str] = []

    tracked_data = _tracked_data_files()
    if tracked_data:
        errors.append(\"Tracked files under data/ are not allowed:\")
        errors.extend(f\"  - {item}\" for item in tracked_data)

    if args.require_clean_tree:
        code, stdout, stderr = _git_status_porcelain()
        if code != 0:
            errors.append(f\"git status failed: {stderr.strip()}\")
        else:
            lines = [line for line in stdout.splitlines() if line.strip()]
            if lines:
                errors.append(\"Uncommitted changes are not allowed:\")
                errors.extend(f\"  - working tree is dirty: {line}\" for line in lines)

    if errors:
        print(\"Protocol check: FAILED\")
        print()
        print(\"\\n\".join(errors))
        return 1

    print(\"Protocol check: PASSED\")
    return 0


if __name__ == \"__main__\":
    raise SystemExit(main())
"""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Propagate protocol enforcement pack to repositories."
    )
    parser.add_argument(
        "--workspace-root",
        default="/home/jp/phd-workspaces",
        help="Root directory used for auto-discovery.",
    )
    parser.add_argument(
        "--targets",
        nargs="*",
        default=[],
        help="Explicit repository paths.",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Discover git repos under workspace root and include them.",
    )
    parser.add_argument(
        "--include-self",
        action="store_true",
        help="Include this repository in discovered targets.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes. Without this flag it runs in dry-run mode.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files.",
    )
    parser.add_argument(
        "--skip-workflow",
        action="store_true",
        help="Do not write GitHub workflow file.",
    )
    return parser.parse_args()


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def _discover_repos(root: Path) -> list[Path]:
    repos: list[Path] = []
    if not root.exists():
        return repos
    for child in sorted(root.iterdir()):
        if child.is_dir() and _is_git_repo(child):
            repos.append(child)
    return repos


def _write_text(path: Path, content: str, *, apply: bool, overwrite: bool) -> str:
    if path.exists() and not overwrite:
        return "skip-existing"
    if not apply:
        return "would-write"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "written"


def _make_exec(path: Path, *, apply: bool) -> str:
    if not apply:
        return "would-chmod"
    mode = path.stat().st_mode
    path.chmod(mode | 0o111)
    return "chmod"


def _apply_to_repo(
    repo: Path, *, apply: bool, overwrite: bool, skip_workflow: bool
) -> list[str]:
    actions: list[str] = []

    files: list[tuple[Path, str]] = [
        (repo / ".pre-commit-config.yaml", PRE_COMMIT_CONFIG),
        (repo / ".githooks" / "pre-commit", HOOK_PRE_COMMIT),
        (repo / ".githooks" / "pre-push", HOOK_PRE_PUSH),
        (repo / "src" / "cli" / "check_repo_protocol.py", CHECKER),
    ]
    if not skip_workflow:
        files.append((repo / ".github" / "workflows" / "repo-protocol.yml", WORKFLOW))

    for path, content in files:
        result = _write_text(path, content, apply=apply, overwrite=overwrite)
        actions.append(f"{result}: {path}")

    for hook in (repo / ".githooks" / "pre-commit", repo / ".githooks" / "pre-push"):
        if hook.exists() or apply:
            actions.append(f"{_make_exec(hook, apply=apply)}: {hook}")

    return actions


def main() -> int:
    args = _parse_args()
    root = Path(args.workspace_root).expanduser().resolve()
    self_repo = Path(__file__).resolve().parents[2]

    targets: set[Path] = set(Path(t).expanduser().resolve() for t in args.targets)
    if args.discover:
        targets.update(_discover_repos(root))
    if not args.include_self and self_repo in targets:
        targets.remove(self_repo)

    if not targets:
        print("No target repositories provided. Use --discover and/or --targets.")
        return 1

    print("Mode:", "apply" if args.apply else "dry-run")
    print("Targets:")
    for repo in sorted(targets):
        print(f"- {repo}")

    for repo in sorted(targets):
        if not _is_git_repo(repo):
            print(f"\n[skip] {repo} (not a git repo)")
            continue
        print(f"\n[repo] {repo}")
        for action in _apply_to_repo(
            repo,
            apply=args.apply,
            overwrite=args.overwrite,
            skip_workflow=args.skip_workflow,
        ):
            print(f"  - {action}")

    print("\nNext step in each target repo:")
    print("- pip install pre-commit")
    print("- pre-commit install --hook-type pre-commit --hook-type pre-push")
    print("- optional: git config core.hooksPath .githooks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
