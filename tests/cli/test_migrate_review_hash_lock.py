"""Tests for legacy reviewed decision hash-lock migration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.cli.migrate_review_hash_lock import migrate_job_review_file


def test_migrate_job_review_file_adds_front_matter_and_keeps_review_body(
    tmp_path: Path,
) -> None:
    job_root = tmp_path / "data/jobs/tu_berlin/201588"
    decision_path = job_root / "nodes/match/review/decision.md"
    approved_path = job_root / "nodes/match/approved/state.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    approved_path.parent.mkdir(parents=True, exist_ok=True)

    approved_payload = {"matches": [{"req_id": "R1", "match_score": 0.2}]}
    approved_path.write_text(
        json.dumps(approved_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    decision_path.write_text(
        "# Match Review\n\nRound: 1\n\n"
        "| Requirement | Evidence (from profile) | Score | Reasoning | Action | Comments |\n"
        "|---|---|---:|---|---|---|\n"
        "| Req | Ev | 0.20 | why | [ ] Proceed / [x] Regen / [ ] Reject | keep this note |\n",
        encoding="utf-8",
    )

    out = migrate_job_review_file(
        source="tu_berlin",
        job_id="201588",
        data_root=tmp_path / "data/jobs",
        dry_run=False,
    )

    expected_hash = "sha256:" + hashlib.sha256(approved_path.read_bytes()).hexdigest()
    migrated = decision_path.read_text(encoding="utf-8")

    assert out.status == "migrated"
    assert out.backup_path is not None
    assert Path(out.backup_path).exists()
    assert f'source_state_hash: "{expected_hash}"' in migrated
    assert 'node: "match"' in migrated
    assert 'job_id: "201588"' in migrated
    assert "round: 1" in migrated
    assert "[ ] Proceed / [x] Regen / [ ] Reject" in migrated
    assert "keep this note" in migrated


def test_migrate_job_review_file_skips_when_hash_already_matches(
    tmp_path: Path,
) -> None:
    job_root = tmp_path / "data/jobs/tu_berlin/201601"
    decision_path = job_root / "nodes/match/review/decision.md"
    approved_path = job_root / "nodes/match/approved/state.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    approved_path.parent.mkdir(parents=True, exist_ok=True)

    approved_path.write_text('{"ok": true}\n', encoding="utf-8")
    expected_hash = "sha256:" + hashlib.sha256(approved_path.read_bytes()).hexdigest()

    decision_path.write_text(
        "---\n"
        f'source_state_hash: "{expected_hash}"\n'
        'node: "match"\n'
        'job_id: "201601"\n'
        "round: 1\n"
        "---\n\n"
        "# Match Review\n",
        encoding="utf-8",
    )

    out = migrate_job_review_file(
        source="tu_berlin",
        job_id="201601",
        data_root=tmp_path / "data/jobs",
        dry_run=False,
    )

    assert out.status == "skipped"
    assert out.backup_path is None
