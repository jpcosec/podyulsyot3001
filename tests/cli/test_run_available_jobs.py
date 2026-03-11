"""Tests for artifact-based available jobs runner."""

from __future__ import annotations

import json
from pathlib import Path

from src.cli.run_available_jobs import continue_job_from_artifacts


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_continue_job_plans_regeneration_from_existing_decision_json(
    tmp_path: Path,
) -> None:
    job_root = tmp_path / "data/jobs/tu_berlin/201588"
    _write_json(
        job_root / "nodes/extract_understand/approved/state.json",
        {"requirements": [{"id": "R1", "text": "Python"}]},
    )
    _write_json(
        job_root / "nodes/match/approved/state.json",
        {"matches": [{"req_id": "R1", "match_score": 0.2}]},
    )
    _write_json(
        job_root / "nodes/match/review/decision.json",
        {
            "decisions": [
                {
                    "block_id": "R1",
                    "decision": "request_regeneration",
                    "notes": "patch",
                }
            ]
        },
    )

    out = continue_job_from_artifacts(
        source="tu_berlin",
        job_id="201588",
        run_id="r1",
        data_root=tmp_path / "data/jobs",
        profile_evidence=None,
        dry_run=True,
    )

    assert out.status == "planned"
    assert out.action == "run_regeneration"
    assert out.review_decision == "request_regeneration"


def test_continue_job_dry_run_prefers_active_markdown_over_stale_decision_json(
    tmp_path: Path,
) -> None:
    job_root = tmp_path / "data/jobs/tu_berlin/201700"
    _write_json(
        job_root / "nodes/extract_understand/approved/state.json",
        {"requirements": [{"id": "R1", "text": "Python"}]},
    )
    _write_json(
        job_root / "nodes/match/approved/state.json",
        {"matches": [{"req_id": "R1", "match_score": 0.2}]},
    )
    _write_json(
        job_root / "nodes/match/review/decision.json",
        {
            "decisions": [
                {
                    "block_id": "R1",
                    "decision": "request_regeneration",
                    "notes": "stale previous round",
                }
            ]
        },
    )

    md_path = job_root / "nodes/match/review/decision.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(
        "# Match Review\n\n"
        "| Requirement | Evidence (from profile) | Score | Reasoning | Action | Comments |\n"
        "|---|---|---:|---|---|---|\n"
        "| Req | Ev | 0.20 | why | [ ] Proceed / [ ] Regen / [ ] Reject | - |\n",
        encoding="utf-8",
    )

    out = continue_job_from_artifacts(
        source="tu_berlin",
        job_id="201700",
        run_id="r1",
        data_root=tmp_path / "data/jobs",
        profile_evidence=None,
        dry_run=True,
    )

    assert out.status == "planned"
    assert out.action == "await_review"
    assert out.review_decision is None


def test_continue_job_runs_initial_match_cycle_with_callbacks(tmp_path: Path) -> None:
    job_root = tmp_path / "data/jobs/tu_berlin/201637"
    _write_json(
        job_root / "nodes/extract_understand/approved/state.json",
        {"requirements": [{"id": "R1", "text": "Python"}]},
    )

    calls = {"match": 0, "review": 0}

    def fake_match(state):
        calls["match"] += 1
        return {
            **dict(state),
            "matched_data": {"matches": [{"req_id": "R1", "match_score": 0.8}]},
            "status": "pending_review",
        }

    def fake_review(state):
        calls["review"] += 1
        return {
            **dict(state),
            "status": "pending_review",
            "review_decision": None,
        }

    out = continue_job_from_artifacts(
        source="tu_berlin",
        job_id="201637",
        run_id="r1",
        data_root=tmp_path / "data/jobs",
        profile_evidence=[{"id": "P1", "description": "evidence"}],
        dry_run=False,
        run_match_node=fake_match,
        run_review_node=fake_review,
    )

    assert out.status == "pending_review"
    assert out.action == "await_review"
    assert calls == {"match": 1, "review": 1}


def test_continue_job_requires_profile_when_regeneration_execution_needed(
    tmp_path: Path,
) -> None:
    job_root = tmp_path / "data/jobs/tu_berlin/201601"
    _write_json(
        job_root / "nodes/extract_understand/approved/state.json",
        {"requirements": [{"id": "R1", "text": "Python"}]},
    )
    _write_json(
        job_root / "nodes/match/approved/state.json",
        {"matches": [{"req_id": "R1", "match_score": 0.8}]},
    )

    def fake_review(state):
        return {
            **dict(state),
            "review_decision": "request_regeneration",
            "status": "running",
        }

    out = continue_job_from_artifacts(
        source="tu_berlin",
        job_id="201601",
        run_id="r1",
        data_root=tmp_path / "data/jobs",
        profile_evidence=None,
        dry_run=False,
        run_review_node=fake_review,
    )

    assert out.status == "error"
    assert out.action == "run_regeneration"
    assert "--profile-evidence" in out.message
