"""Tests for match node logic orchestration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.nodes.match.logic import run_logic


def test_run_logic_updates_state_with_match_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakePromptManager:
        def __init__(self, base_path: str):
            assert base_path == "src/nodes"

        def build_prompt(
            self,
            node_name: str,
            data: dict,
            *,
            required_xml_tags: tuple[str, ...],
            optional_xml_tags: tuple[str, ...],
        ):
            assert node_name == "match"
            assert data["job_id"] == "job-1"
            assert data["prev_round"] is None
            assert data["round_feedback"] is None
            assert data["regeneration_scope"] is None
            assert required_xml_tags == ("job_requirements", "profile_evidence")
            assert optional_xml_tags == ("round_feedback", "regeneration_scope")
            return "system", "user"

    class FakeRuntime:
        def __init__(self, model_name: str):
            assert model_name == "gemini-2.5-flash"

        def generate_structured(
            self, system_prompt: str, user_prompt: str, output_schema
        ):
            assert system_prompt == "system"
            assert user_prompt == "user"
            return output_schema(
                matches=[
                    {
                        "req_id": "R1",
                        "match_score": 0.9,
                        "evidence_id": "P1",
                        "reasoning": "Strong evidence",
                    }
                ],
                total_score=0.9,
                decision_recommendation="proceed",
                summary_notes="Good fit",
            )

    monkeypatch.setattr("src.nodes.match.logic.PromptManager", FakePromptManager)
    monkeypatch.setattr("src.nodes.match.logic.LLMRuntime", FakeRuntime)

    out = run_logic(
        {
            "job_id": "job-1",
            "extracted_data": {
                "requirements": [{"id": "R1", "text": "Python", "priority": "must"}],
            },
            "my_profile_evidence": [
                {"id": "P1", "description": "Built Python pipelines"}
            ],
        }
    )

    assert out["current_node"] == "match"
    assert out["status"] == "running"
    assert out["matched_data"]["decision_recommendation"] == "proceed"


def test_run_logic_requires_requirements() -> None:
    with pytest.raises(ValueError, match="requirements"):
        run_logic(
            {
                "job_id": "job-1",
                "extracted_data": {},
                "my_profile_evidence": [{"id": "P1", "description": "x"}],
            }
        )


def test_run_logic_requires_profile_evidence() -> None:
    with pytest.raises(ValueError, match="my_profile_evidence"):
        run_logic(
            {
                "job_id": "job-1",
                "extracted_data": {
                    "requirements": [
                        {"id": "R1", "text": "Python", "priority": "must"}
                    ],
                },
            }
        )


def test_run_logic_renders_review_markdown_with_requirement_and_evidence_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    class FakePromptManager:
        def __init__(self, base_path: str):
            assert base_path == "src/nodes"

        def build_prompt(
            self,
            node_name: str,
            data: dict,
            *,
            required_xml_tags: tuple[str, ...],
            optional_xml_tags: tuple[str, ...],
        ):
            return "system", "user"

    class FakeRuntime:
        def __init__(self, model_name: str):
            assert model_name == "gemini-2.5-flash"

        def generate_structured(
            self, system_prompt: str, user_prompt: str, output_schema
        ):
            return output_schema(
                matches=[
                    {
                        "req_id": "R1",
                        "match_score": 0.75,
                        "evidence_id": "P1",
                        "reasoning": "Aligned project",
                    }
                ],
                total_score=0.75,
                decision_recommendation="proceed",
                summary_notes="Good fit",
            )

    monkeypatch.setattr("src.nodes.match.logic.PromptManager", FakePromptManager)
    monkeypatch.setattr("src.nodes.match.logic.LLMRuntime", FakeRuntime)

    run_logic(
        {
            "source": "tu_berlin",
            "job_id": "job-2",
            "extracted_data": {
                "requirements": [{"id": "R1", "text": "Python", "priority": "must"}],
            },
            "my_profile_evidence": [
                {"id": "P1", "description": "Built Python pipelines"}
            ],
        }
    )

    decision_md = tmp_path / "data/jobs/tu_berlin/job-2/nodes/match/review/decision.md"
    decision_round_md = (
        tmp_path
        / "data/jobs/tu_berlin/job-2/nodes/match/review/rounds/round_001/decision.md"
    )
    content = decision_md.read_text(encoding="utf-8")
    assert decision_round_md.exists()
    assert content.startswith("---\n")
    assert "source_state_hash:" in content
    assert 'node: "match"' in content
    assert 'job_id: "job-2"' in content
    assert "Round: 1" in content
    assert (
        "Req ID | Requirement | Evidence (from profile) | Score | Reasoning | Action | Comments"
        in content
    )
    assert "| R1 | Python | Built Python pipelines |" in content
    assert "[ ] Proceed / [ ] Regen / [ ] Reject" in content


def test_run_logic_regeneration_focuses_review_table_on_patch_requirements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    class FakePromptManager:
        def __init__(self, base_path: str):
            assert base_path == "src/nodes"

        def build_prompt(
            self,
            node_name: str,
            data: dict,
            *,
            required_xml_tags: tuple[str, ...],
            optional_xml_tags: tuple[str, ...],
        ):
            assert data["prev_round"] == 1
            assert data["regeneration_scope"] == ["R2"]
            return "system", "user"

    class FakeRuntime:
        def __init__(self, model_name: str):
            assert model_name == "gemini-2.5-flash"

        def generate_structured(
            self, system_prompt: str, user_prompt: str, output_schema
        ):
            return output_schema(
                matches=[
                    {
                        "req_id": "R1",
                        "match_score": 0.85,
                        "evidence_id": "P1",
                        "reasoning": "Already covered",
                    },
                    {
                        "req_id": "R2",
                        "match_score": 0.55,
                        "evidence_id": "P2",
                        "reasoning": "Improved with patch",
                    },
                ],
                total_score=0.70,
                decision_recommendation="marginal",
                summary_notes="Updated",
            )

    monkeypatch.setattr("src.nodes.match.logic.PromptManager", FakePromptManager)
    monkeypatch.setattr("src.nodes.match.logic.LLMRuntime", FakeRuntime)

    feedback_path = (
        tmp_path
        / "data/jobs/tu_berlin/job-regen/nodes/match/review/rounds/round_001/feedback.json"
    )
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    feedback_path.write_text(
        json.dumps(
            {
                "round_n": 1,
                "feedback": [
                    {
                        "req_id": "R1",
                        "action": "proceed",
                        "reviewer_note": "Looks good",
                    },
                    {
                        "req_id": "R2",
                        "action": "patch",
                        "reviewer_note": "Improve requirement R2",
                        "patch_evidence": {
                            "id": "P2",
                            "description": "Experience with SQL dashboards",
                        },
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    run_logic(
        {
            "source": "tu_berlin",
            "job_id": "job-regen",
            "review_decision": "request_regeneration",
            "extracted_data": {
                "requirements": [
                    {"id": "R1", "text": "Python", "priority": "must"},
                    {"id": "R2", "text": "SQL", "priority": "must"},
                ],
            },
            "my_profile_evidence": [
                {"id": "P1", "description": "Built Python pipelines"}
            ],
        }
    )

    decision_md = (
        tmp_path / "data/jobs/tu_berlin/job-regen/nodes/match/review/decision.md"
    )
    content = decision_md.read_text(encoding="utf-8")
    assert "## Context (Outside Regeneration Scope)" in content
    assert "| R1 | Python | Built Python pipelines |" in content
    assert "carried forward" in content
    assert "## Regeneration Scope (Action Required)" in content
    assert "| R2 | SQL | Experience with SQL dashboards |" in content


def test_run_logic_fail_closed_when_regen_feedback_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    class FakePromptManager:
        def __init__(self, base_path: str):
            assert base_path == "src/nodes"

        def build_prompt(
            self,
            node_name: str,
            data: dict,
            *,
            required_xml_tags: tuple[str, ...],
            optional_xml_tags: tuple[str, ...],
        ):
            return "system", "user"

    class FakeRuntime:
        def __init__(self, model_name: str):
            assert model_name == "gemini-2.5-flash"

        def generate_structured(
            self, system_prompt: str, user_prompt: str, output_schema
        ):
            return output_schema(
                matches=[],
                total_score=0.0,
                decision_recommendation="reject",
                summary_notes="No fit",
            )

    monkeypatch.setattr("src.nodes.match.logic.PromptManager", FakePromptManager)
    monkeypatch.setattr("src.nodes.match.logic.LLMRuntime", FakeRuntime)

    with pytest.raises(ValueError, match="feedback.json"):
        run_logic(
            {
                "source": "tu_berlin",
                "job_id": "job-3",
                "review_decision": "request_regeneration",
                "extracted_data": {
                    "requirements": [
                        {"id": "R1", "text": "Python", "priority": "must"}
                    ],
                },
                "my_profile_evidence": [
                    {"id": "P1", "description": "Built Python pipelines"}
                ],
            }
        )
