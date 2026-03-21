"""Tests for extract_understand logic orchestration."""

from __future__ import annotations

import pytest

from src.nodes.extract_understand.contract import (
    ContactInfo,
    JobConstraint,
    JobRequirement,
    JobUnderstandingExtract,
)
from src.nodes.extract_understand.logic import _enrich_extraction_result, run_logic


def test_run_logic_updates_state_with_extracted_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_extract(node_data: dict) -> JobUnderstandingExtract:
        assert node_data["job_id"] == "job-1"
        assert "python" in node_data["source_text_md"]
        return JobUnderstandingExtract(
            job_title="PhD Position",
            analysis_notes="explicit extraction rationale",
            requirements=[JobRequirement(id="R1", text="Python", priority="must")],
            constraints=[
                JobConstraint(constraint_type="language", description="English")
            ],
            risk_areas=["onsite in another country"],
            contact_info=ContactInfo(
                name="Prof. Ada Lovelace", email="ada@example.org"
            ),
            salary_grade=None,
        )

    monkeypatch.setattr(
        "src.nodes.extract_understand.logic._run_langchain_extraction", fake_extract
    )

    updated = run_logic(
        {
            "job_id": "job-1",
            "ingested_data": {"raw_text": "Need python and statistics"},
            "active_feedback": [],
        }
    )

    assert updated["extracted_data"]["job_title"] == "PhD Position"
    assert updated["extracted_data"]["requirements"][0]["id"] == "R1"
    assert updated["extracted_data"]["contact_info"]["email"] == "ada@example.org"
    assert updated["extracted_data"]["salary_grade"] is None


def test_run_logic_requires_raw_text() -> None:
    with pytest.raises(ValueError, match="raw_text"):
        run_logic({"job_id": "job-2", "ingested_data": {}})


def test_enrich_extraction_result_fills_missing_contact_and_salary() -> None:
    result = JobUnderstandingExtract(
        job_title="PhD Position",
        analysis_notes="explicit extraction rationale",
        requirements=[JobRequirement(id="R1", text="Python", priority="must")],
        constraints=[],
        risk_areas=[],
        contact_info=ContactInfo(),
        salary_grade=None,
    )

    enriched = _enrich_extraction_result(
        result,
        "Prof. Dr. Ada Lovelace\nContact: ada@example.org\nSalary grade 13 TV-L",
    )

    assert enriched.contact_info.email == "ada@example.org"
    assert enriched.contact_info.name == "Prof. Dr. Ada Lovelace"
    assert enriched.salary_grade == "Salary grade 13"
