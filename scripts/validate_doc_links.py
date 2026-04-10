"""Validate that all file-path references in markdown files point to existing files.

Checks every backtick-quoted path that looks like a file reference (contains a
slash and a dot) across all .md files in the repository. Exits non-zero if any
broken link is found so this can be used as a CI gate.

Usage:
    python scripts/validate_doc_links.py
    python scripts/validate_doc_links.py --root path/to/repo
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Matches `src/foo/bar.py` or `docs/standards/docs/guide.md` style references.
# Requires at least one slash and a dot-extension to avoid matching plain words.
_FILE_REF = re.compile(r"`([a-zA-Z0-9_./-]+/[a-zA-Z0-9_.-]+\.[a-zA-Z]+)`")

# Markdown link targets: [text](path) — only local paths (no http/https).
_MD_LINK = re.compile(r"\[(?:[^\]]+)\]\((?!https?://)([^)]+)\)")

# Path prefixes that point to runtime artifacts or data, not source files.
# These appear in docs as illustrative paths and are not expected to exist in the repo.
_ARTIFACT_PREFIXES = (
    "output/",
    "data/",
    "approved/",
    "review/",
    "logs/",
)

# Paths documented as not-yet-existing (future work). Skip them.
_FUTURE_PREFIXES = (
    "scripts/expand_context.py",
    "scripts/export_schemas.py",
    "docs/runtime/data_management.md",
    "src/review_ui/README.md",
)

# Historical or generated markdown we do not keep link-clean as part of the
# active documentation contract.
_IGNORED_MD_DIR_PARTS = {
    "future_docs",
}

_IGNORED_MD_PATH_FRAGMENTS = (
    "docs/superpowers/plans/",
    "docs/superpowers/specs/",
    "docs/runtime/pipeline_overview.md",
    "plan_docs/archive/",
    "plan_docs/ariadne/",
    "plan_docs/contracts/",
    "plan_docs/motors/",
    "plan_docs/planning/",
    "plan_docs/automation/",
)


def _check_file(md_path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    text = md_path.read_text(encoding="utf-8")

    candidates: list[str] = []
    candidates += _FILE_REF.findall(text)
    candidates += _MD_LINK.findall(text)

    for ref in candidates:
        # Strip leading/trailing whitespace and anchors (#section)
        ref = ref.split("#")[0].strip()
        if not ref:
            continue

        # Skip runtime artifact paths — these are illustrative, not repo files.
        if any(ref.startswith(p) for p in _ARTIFACT_PREFIXES):
            continue

        # Skip paths explicitly documented as future/not-yet-existing.
        if any(ref == p or ref.endswith("/" + p) for p in _FUTURE_PREFIXES):
            continue

        # Resolve relative to the markdown file's directory first, then repo root.
        resolved = (md_path.parent / ref).resolve()
        if not resolved.exists():
            resolved = (repo_root / ref).resolve()

        if not resolved.exists():
            errors.append(f"  {md_path.relative_to(repo_root)}:{ref!r} — not found")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate file references in markdown docs."
    )
    parser.add_argument("--root", default=".", help="Repository root (default: cwd)")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    md_files = list(repo_root.rglob("*.md"))

    # Ignore generated, vendored directories, and historical logs.
    ignore_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv"}
    ignore_files = {"changelog.md"}
    md_files = [
        f
        for f in md_files
        if not any(p in ignore_dirs for p in f.parts) and f.name not in ignore_files
    ]
    md_files = [
        f
        for f in md_files
        if not any(part in _IGNORED_MD_DIR_PARTS for part in f.parts)
        and not any(fragment in f.as_posix() for fragment in _IGNORED_MD_PATH_FRAGMENTS)
        and not f.name.startswith("session-ses_")
    ]

    all_errors: list[str] = []
    for md_path in sorted(md_files):
        all_errors += _check_file(md_path, repo_root)

    if all_errors:
        print("Broken file references found:\n")
        for err in all_errors:
            print(err)
        return 1

    print(f"OK — checked {len(md_files)} markdown files, no broken references.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
