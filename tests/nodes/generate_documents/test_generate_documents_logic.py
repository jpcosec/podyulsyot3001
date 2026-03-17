"""Tests for generate_documents logic orchestration and deterministic indicators."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.nodes.generate_documents.logic import run_logic


def _base_profile() -> dict:
    return {
        "owner": {
            "full_name": "Jane Doe",
            "contact": {
                "email": "jane@example.com",
                "phone": "+49-111",
                "addresses": [{"value": "Berlin, Germany"}],
            },
            "links": {"linkedin": "https://linkedin.com/in/jane"},
        },
        "cv_generation_context": {"tagline_seed": "Research Candidate"},
        "experience": [
            {
                "id": "EXP001",
                "organization": "AraraDS",
                "role": "ML Consultant",
                "start_date": "2025-01",
                "end_date": "2025-12",
                "achievements": ["Built data pipelines"],
            }
        ],
        "education": [],
        "publications": [],
        "languages": [],
        "skills": {
            "programming_languages": ["Python"],
            "ml_ai": ["PyTorch"],
            "data_platforms": ["BigQuery"],
            "orchestration_devops": ["Airflow"],
            "electronics_robotics": ["ROS"],
        },
    }


def _base_state() -> dict:
    return {
        "source": "tu_berlin",
        "job_id": "job-1",
        "run_id": "run-1",
        "current_node": "review_match",
        "status": "running",
        "profile_base_data": _base_profile(),
        "extracted_data": {
            "requirements": [{"id": "R1", "text": "Python", "priority": "must"}],
        },
        "matched_data": {
            "matches": [
                {
                    "req_id": "R1",
                    "match_score": 0.9,
                    "evidence_id": "P1",
                    "reasoning": "Direct evidence",
                }
            ]
        },
        "last_decision": {
            "node": "review_match",
            "job_id": "job-1",
            "round": 1,
            "source_state_hash": "sha256:abc",
            "decisions": [
                {
                    "block_id": "R1",
                    "decision": "approve",
                    "notes": "",
                    "directives": [],
                }
            ],
        },
    }


def test_run_logic_writes_artifacts_and_indicators(
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
        ) -> tuple[str, str]:
            assert node_name == "generate_documents"
            assert data["job_id"] == "job-1"
            assert required_xml_tags == ("candidate_base_cv", "validated_matches")
            assert optional_xml_tags == ()
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
                cv_summary="Excellent fit for the role\nFocused on applied ML",
                cv_injections=[
                    {
                        "experience_id": "EXP001",
                        "new_bullets": [
                            "Integrated deterministic review indicators into generation flow"
                        ],
                    }
                ],
                letter_deltas={
                    "subject_line": "Application - Research Role",
                    "intro_paragraph": "I am applying for this role.",
                    "core_argument_paragraph": "I implemented deterministic indicators and aligned CV deltas.",
                    "alignment_paragraph": "The project aligns with my applied ML background.",
                    "closing_paragraph": "Thank you for your time.",
                },
                email_body="Please find attached my documents.",
            )

    monkeypatch.setattr(
        "src.nodes.generate_documents.logic.PromptManager", FakePromptManager
    )
    monkeypatch.setattr("src.nodes.generate_documents.logic.LLMRuntime", FakeRuntime)

    out = run_logic(_base_state())

    assert out["current_node"] == "generate_documents"
    assert out["status"] == "running"
    assert out["document_deltas"]["cv_injections"][0]["experience_id"] == "EXP001"
    assert any(
        indicator["rule_id"].startswith("ANTI_FLUFF_")
        for indicator in out["text_review_indicators"]
    )

    approved_state = (
        tmp_path
        / "data/jobs/tu_berlin/job-1/nodes/generate_documents/approved/state.json"
    )
    assist_state = (
        tmp_path
        / "data/jobs/tu_berlin/job-1/nodes/generate_documents/assist/proposed/state.json"
    )
    cv_md = (
        tmp_path / "data/jobs/tu_berlin/job-1/nodes/generate_documents/proposed/cv.md"
    )

    assert approved_state.exists()
    assert assist_state.exists()
    assert cv_md.exists()
    assert "SUMMARY" in cv_md.read_text(encoding="utf-8")
    assert "Integrated deterministic review indicators" in cv_md.read_text(
        encoding="utf-8"
    )


def test_run_logic_rejects_unknown_experience_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    class FakePromptManager:
        def __init__(self, base_path: str):
            pass

        def build_prompt(self, node_name: str, data: dict, **kwargs):
            return "system", "user"

    class FakeRuntime:
        def __init__(self, model_name: str):
            pass

        def generate_structured(
            self, system_prompt: str, user_prompt: str, output_schema
        ):
            return output_schema(
                cv_summary="Factual summary",
                cv_injections=[
                    {
                        "experience_id": "EXP999",
                        "new_bullets": ["Added unsupported bullet"],
                    }
                ],
                letter_deltas={
                    "subject_line": "Application",
                    "intro_paragraph": "Intro",
                    "core_argument_paragraph": "Core",
                    "alignment_paragraph": "Align",
                    "closing_paragraph": "Close",
                },
                email_body="Please find attachments.",
            )

    monkeypatch.setattr(
        "src.nodes.generate_documents.logic.PromptManager", FakePromptManager
    )
    monkeypatch.setattr("src.nodes.generate_documents.logic.LLMRuntime", FakeRuntime)

    with pytest.raises(ValueError, match="unknown experience_id"):
        run_logic(_base_state())


def test_run_logic_uses_real_prompt_template_xml_tags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    repo_root = Path(__file__).resolve().parents[3]

    from src.ai.prompt_manager import PromptManager as RealPromptManager

    class PromptManagerWithRepoPath(RealPromptManager):
        def __init__(self, base_path: str):
            super().__init__(base_path=str(repo_root / "src/nodes"))

    class FakeRuntime:
        def __init__(self, model_name: str):
            assert model_name == "gemini-2.5-flash"

        def generate_structured(
            self, system_prompt: str, user_prompt: str, output_schema
        ):
            assert "<candidate_base_cv>" in user_prompt
            assert "<validated_matches>" in user_prompt
            return output_schema(
                cv_summary="Factual summary",
                cv_injections=[
                    {
                        "experience_id": "EXP001",
                        "new_bullets": ["Added deterministic bullet"],
                    }
                ],
                letter_deltas={
                    "subject_line": "Application",
                    "intro_paragraph": "Intro",
                    "core_argument_paragraph": "Core",
                    "alignment_paragraph": "Align",
                    "closing_paragraph": "Close",
                },
                email_body="Please find attachments.",
            )

    monkeypatch.setattr(
        "src.nodes.generate_documents.logic.PromptManager", PromptManagerWithRepoPath
    )
    monkeypatch.setattr("src.nodes.generate_documents.logic.LLMRuntime", FakeRuntime)

    out = run_logic(_base_state())
    assert out["current_node"] == "generate_documents"
