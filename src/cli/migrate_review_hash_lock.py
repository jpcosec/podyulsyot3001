"""Migrate legacy reviewed decision files to hash-locked format."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from src.core.round_manager import RoundManager

SOURCE_HASH_RE = re.compile(
    r'^\s*source_state_hash:\s*"?(sha256:[0-9a-fA-F]{64})"?\s*$',
    flags=re.MULTILINE,
)
ROUND_RE = re.compile(r"^(?:Round|round):\s*(\d+)\s*$", flags=re.IGNORECASE)


@dataclass(frozen=True)
class MigrationResult:
    source: str
    job_id: str
    status: str
    message: str
    decision_path: str
    backup_path: str | None = None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate reviewed match decision.md files to include source_state_hash"
    )
    parser.add_argument("--source", default="tu_berlin")
    parser.add_argument(
        "--job-id",
        action="append",
        help="Repeatable job id. Use --all-jobs to migrate all numeric jobs under source.",
    )
    parser.add_argument("--all-jobs", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--data-root", default="data/jobs")
    args = parser.parse_args()

    root = Path(args.data_root) / args.source
    if not root.exists():
        raise ValueError(f"source root not found: {root}")

    job_ids = _resolve_job_ids(root, args.job_id or [], all_jobs=args.all_jobs)
    results = [
        migrate_job_review_file(
            source=args.source,
            job_id=job_id,
            data_root=Path(args.data_root),
            dry_run=args.dry_run,
        )
        for job_id in job_ids
    ]

    print(json.dumps([asdict(item) for item in results], indent=2, ensure_ascii=False))
    return 1 if any(item.status == "error" for item in results) else 0


def migrate_job_review_file(
    *,
    source: str,
    job_id: str,
    data_root: Path,
    dry_run: bool,
) -> MigrationResult:
    job_root = data_root / source / job_id
    decision_path = job_root / "nodes/match/review/decision.md"
    proposed_path = job_root / "nodes/match/approved/state.json"

    if not decision_path.exists():
        return MigrationResult(
            source=source,
            job_id=job_id,
            status="error",
            message="missing review decision.md",
            decision_path=str(decision_path),
        )
    if not proposed_path.exists():
        return MigrationResult(
            source=source,
            job_id=job_id,
            status="error",
            message="missing match approved state.json",
            decision_path=str(decision_path),
        )

    expected_hash = _sha256_file(proposed_path)
    decision_text = decision_path.read_text(encoding="utf-8")
    embedded_hash = _extract_source_hash(decision_text)

    if embedded_hash == expected_hash:
        return MigrationResult(
            source=source,
            job_id=job_id,
            status="skipped",
            message="decision.md already contains matching source_state_hash",
            decision_path=str(decision_path),
        )
    if embedded_hash is not None and embedded_hash != expected_hash:
        return MigrationResult(
            source=source,
            job_id=job_id,
            status="error",
            message=(
                "decision.md already contains source_state_hash but it mismatches "
                "current approved/state.json"
            ),
            decision_path=str(decision_path),
        )

    round_n = _extract_round_number(decision_text) or _fallback_round_number(job_root)
    migrated_text = _inject_front_matter(
        decision_text,
        source_hash=expected_hash,
        job_id=job_id,
        round_n=round_n,
    )

    backup_path = _next_backup_path(decision_path)
    if not dry_run:
        backup_path.write_text(decision_text, encoding="utf-8")
        decision_path.write_text(migrated_text, encoding="utf-8")

    return MigrationResult(
        source=source,
        job_id=job_id,
        status="migrated",
        message="added hash-lock front matter and preserved existing review body",
        decision_path=str(decision_path),
        backup_path=str(backup_path),
    )


def _resolve_job_ids(root: Path, job_ids: list[str], *, all_jobs: bool) -> list[str]:
    normalized = [item.strip() for item in job_ids if item and item.strip()]
    if normalized:
        return normalized
    if not all_jobs:
        raise ValueError("pass --job-id (repeatable) or use --all-jobs")
    return sorted(
        path.name for path in root.iterdir() if path.is_dir() and path.name.isdigit()
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _extract_source_hash(text: str) -> str | None:
    match = SOURCE_HASH_RE.search(text)
    if match is None:
        return None
    return match.group(1)


def _extract_round_number(text: str) -> int | None:
    for line in text.splitlines():
        match = ROUND_RE.match(line.strip())
        if match is not None:
            return int(match.group(1))
    return None


def _fallback_round_number(job_root: Path) -> int:
    latest = RoundManager(job_root).get_latest_round()
    return latest if latest >= 1 else 1


def _inject_front_matter(
    text: str,
    *,
    source_hash: str,
    job_id: str,
    round_n: int,
) -> str:
    normalized = text.replace("\r\n", "\n")
    lines = normalized.split("\n")

    if lines and lines[0].strip() == "---":
        closing_idx = None
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                closing_idx = idx
                break
        if closing_idx is not None:
            existing = lines[1:closing_idx]
            body = lines[closing_idx + 1 :]
            kept = [
                line for line in existing if not _is_reserved_front_matter_key(line)
            ]
            front = _front_matter_lines(source_hash, job_id, round_n)
            out = ["---", *front, *kept, "---", *body]
            return "\n".join(out).rstrip("\n") + "\n"

    front = _front_matter_lines(source_hash, job_id, round_n)
    return "\n".join(["---", *front, "---", "", normalized]).rstrip("\n") + "\n"


def _front_matter_lines(source_hash: str, job_id: str, round_n: int) -> list[str]:
    return [
        f'source_state_hash: "{source_hash}"',
        'node: "match"',
        f'job_id: "{job_id}"',
        f"round: {round_n}",
    ]


def _is_reserved_front_matter_key(line: str) -> bool:
    return bool(
        re.match(r"^\s*(source_state_hash|node|job_id|round)\s*:", line, re.IGNORECASE)
    )


def _next_backup_path(decision_path: Path) -> Path:
    base = decision_path.with_name("decision.legacy_reviewed.md")
    if not base.exists():
        return base

    idx = 1
    while True:
        candidate = decision_path.with_name(f"decision.legacy_reviewed.{idx:03d}.md")
        if not candidate.exists():
            return candidate
        idx += 1


if __name__ == "__main__":
    raise SystemExit(main())
