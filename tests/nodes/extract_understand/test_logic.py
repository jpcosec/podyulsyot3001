"""Tests for extract_understand logic orchestration."""

from __future__ import annotations

import pytest

from src.nodes.extract_understand.logic import run_logic


def test_run_logic_updates_state_with_extracted_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakePromptManager:
        def __init__(self, base_path: str):
            assert base_path == "src/nodes"

        def build_prompt(self, node_name: str, data: dict):
            assert node_name == "extract_understand"
            assert data["job_id"] == "job-1"
            assert "python" in data["source_text_md"]
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
                job_title="PhD Position",
                analysis_notes="explicit extraction rationale",
                requirements=[
                    {"id": "R1", "text": "Python", "priority": "must"},
                ],
                constraints=[
                    {"constraint_type": "language", "description": "English"},
                ],
                risk_areas=["onsite in another country"],
            )

    monkeypatch.setattr(
        "src.nodes.extract_understand.logic.PromptManager", FakePromptManager
    )
    monkeypatch.setattr("src.nodes.extract_understand.logic.LLMRuntime", FakeRuntime)

    updated = run_logic(
        {
            "job_id": "job-1",
            "ingested_data": {"raw_text": "Need python and statistics"},
            "active_feedback": [],
        }
    )

    assert updated["extracted_data"]["job_title"] == "PhD Position"
    assert updated["extracted_data"]["requirements"][0]["id"] == "R1"


def test_run_logic_requires_raw_text() -> None:
    with pytest.raises(ValueError, match="raw_text"):
        run_logic({"job_id": "job-2", "ingested_data": {}})
