#!/usr/bin/env python3
"""Rebuild backup compendium manifest for data layout.

Scopes:
- data/pipelined_data/
- data/reference_data/
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build backup compendium manifest")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Workspace root",
    )
    return parser.parse_args()


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file())


def build_manifest(repo_root: Path) -> dict:
    data_root = repo_root / "data"
    pipelined_root = data_root / "pipelined_data"
    reference_root = data_root / "reference_data"

    files = []
    for source_root in (pipelined_root, reference_root):
        for file_path in iter_files(source_root):
            stats = file_path.stat()
            files.append(
                {
                    "path": file_path.relative_to(repo_root).as_posix(),
                    "size_bytes": stats.st_size,
                    "sha256": sha256sum(file_path),
                    "modified_utc": datetime.fromtimestamp(
                        stats.st_mtime, timezone.utc
                    ).isoformat(),
                }
            )

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "files": files,
    }


def main() -> None:
    args = parse_args()
    repo_root = args.root.resolve()
    output_path = (
        repo_root / "data" / "reference_data" / "backup" / "backup_compendium.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = build_manifest(repo_root)

    if args.dry_run:
        print(f"[DRY-RUN] manifest entries: {payload['file_count']}")
        print(f"[DRY-RUN] output path: {output_path}")
        return

    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(f"[DONE] manifest entries: {payload['file_count']}")
    print(f"[DONE] output path: {output_path}")


if __name__ == "__main__":
    main()
