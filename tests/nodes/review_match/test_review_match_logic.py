"""Tests for review_match markdown generation and parsing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.nodes.review_match.logic import run_logic


def _base_state() -> dict:
    return {
        "source": "tu_berlin",
        "job_id": "job-1",
        "run_id": "run-1",
        "current_node": "match",
        "status": "running",
        "matched_data": {
            "matches": [
                {
                    "req_id": "R1",
                    "match_score": 0.8,
                    "evidence_id": "P1",
                    "reasoning": "Strong overlap",
                }
            ],
            "total_score": 0.8,
            "decision_recommendation": "proceed",
            "summary_notes": "Looks good",
        },
        "extracted_data": {
            "requirements": [{"id": "R1", "text": "Python", "priority": "must"}],
        },
        "my_profile_evidence": [{"id": "P1", "description": "Built Python pipelines"}],
    }


def test_run_logic_creates_decision_markdown_and_pauses_review(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)

    out = run_logic(_base_state())

    assert out["status"] == "pending_review"
    assert out["pending_gate"] == "review_match"
    assert out["review_decision"] is None

    md_path = tmp_path / "data/jobs/tu_berlin/job-1/nodes/match/review/decision.md"
    round_md_path = (
        tmp_path
        / "data/jobs/tu_berlin/job-1/nodes/match/review/rounds/round_001/decision.md"
    )
    assert md_path.exists()
    assert round_md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert (
        "Requirement | Evidence (from profile) | Score | Reasoning | Action | Comments"
        in content
    )
    assert "| Python | Built Python pipelines |" in content
    assert "[ ] Proceed / [ ] Regen / [ ] Reject" in content


def test_run_logic_parses_regen_decision_and_writes_json(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)

    state = _base_state()
    run_logic(state)

    md_path = tmp_path / "data/jobs/tu_berlin/job-1/nodes/match/review/decision.md"
    text = md_path.read_text(encoding="utf-8")
    text = text.replace(
        "[ ] Proceed / [ ] Regen / [ ] Reject",
        "[ ] Proceed / [X] Regen / [ ] Reject",
    )
    md_path.write_text(text, encoding="utf-8")

    out = run_logic(state)

    assert out["review_decision"] == "request_regeneration"
    assert out["status"] == "running"

    json_path = tmp_path / "data/jobs/tu_berlin/job-1/nodes/match/review/decision.json"
    round_json_path = (
        tmp_path
        / "data/jobs/tu_berlin/job-1/nodes/match/review/rounds/round_001/decision.json"
    )
    feedback_path = (
        tmp_path
        / "data/jobs/tu_berlin/job-1/nodes/match/review/rounds/round_001/feedback.json"
    )
    assert json_path.exists()
    assert round_json_path.exists()
    assert feedback_path.exists()


def test_run_logic_parses_regen_with_loose_checkbox_spacing(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)

    state = _base_state()
    run_logic(state)

    md_path = tmp_path / "data/jobs/tu_berlin/job-1/nodes/match/review/decision.md"
    text = md_path.read_text(encoding="utf-8")
    text = text.replace(
        "[ ] Proceed / [ ] Regen / [ ] Reject",
        "[] Proceed / [ x] Regen / [ ] Reject",
    )
    md_path.write_text(text, encoding="utf-8")

    out = run_logic(state)

    assert out["review_decision"] == "request_regeneration"
    assert out["status"] == "running"


def test_run_logic_fails_on_stale_source_hash(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    state = _base_state()
    run_logic(state)

    proposed_path = (
        tmp_path / "data/jobs/tu_berlin/job-1/nodes/match/approved/state.json"
    )
    proposed_path.parent.mkdir(parents=True, exist_ok=True)
    proposed_path.write_text(
        json.dumps(
            {
                "matches": [
                    {
                        "req_id": "R1",
                        "match_score": 0.1,
                        "evidence_id": None,
                        "reasoning": "changed",
                    }
                ],
                "total_score": 0.1,
                "decision_recommendation": "reject",
                "summary_notes": "changed",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    md_path = tmp_path / "data/jobs/tu_berlin/job-1/nodes/match/review/decision.md"
    text = md_path.read_text(encoding="utf-8")
    text = text.replace(
        "[ ] Proceed / [ ] Regen / [ ] Reject",
        "[X] Proceed / [ ] Regen / [ ] Reject",
    )
    md_path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="source_state_hash mismatch"):
        run_logic(state)


def test_run_logic_fails_on_invalid_checkbox_markup(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)

    state = _base_state()
    run_logic(state)

    md_path = tmp_path / "data/jobs/tu_berlin/job-1/nodes/match/review/decision.md"
    text = md_path.read_text(encoding="utf-8")
    text = text.replace(
        "[ ] Proceed / [ ] Regen / [ ] Reject",
        "[X] Proceed / [X] Regen / [ ] Reject",
    )
    md_path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="invalid Action markup"):
        run_logic(state)
