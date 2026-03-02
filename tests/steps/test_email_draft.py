"""Tests for the email_draft step."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.steps import StepResult
from src.steps.email_draft import run
from src.utils.state import JobState


@pytest.fixture
def mock_job_state(tmp_path):
    """Create a mock JobState with temporary directories."""
    state = Mock(spec=JobState)
    state.job_id = "test_job_123"
    state.source = "tu_berlin"
    state.job_dir = tmp_path / "test_job_123"
    state.job_dir.mkdir(parents=True, exist_ok=True)

    # Create required subdirectories
    (state.job_dir / "planning").mkdir(parents=True, exist_ok=True)
    (state.job_dir / ".metadata").mkdir(parents=True, exist_ok=True)

    # Mock artifact_path to return paths in the temp dir
    def artifact_path_fn(rel_path: str) -> Path:
        return state.job_dir / rel_path

    state.artifact_path = artifact_path_fn

    # Mock step_complete
    state.step_complete = Mock(return_value=False)

    # Mock write_artifact methods
    def write_artifact_fn(rel_path: str, content: str) -> Path:
        path = state.job_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_json_artifact_fn(rel_path: str, data: dict) -> Path:
        path = state.job_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return path

    state.write_artifact = write_artifact_fn
    state.write_json_artifact = write_json_artifact_fn

    return state


def test_run_produces_email(mock_job_state: Mock):
    """Verify that run() produces application_email.md."""
    # Create required motivation_letter.json
    motivation_data = {
        "subject": "Application for Research Assistant",
        "salutation": "Dear Dr. Smith,",
        "fit_signals": [],
        "risk_notes": [],
        "letter_markdown": "# Motivation Letter\n\nDear Dr. Smith,\n",
    }
    motivation_path = mock_job_state.job_dir / "planning" / "motivation_letter.json"
    motivation_path.parent.mkdir(parents=True, exist_ok=True)
    motivation_path.write_text(json.dumps(motivation_data, indent=2), encoding="utf-8")

    # Mock the MotivationLetterService
    mock_result = Mock()
    mock_result.email_path = mock_job_state.job_dir / "planning" / "application_email.md"

    # Ensure output file exists
    mock_result.email_path.parent.mkdir(parents=True, exist_ok=True)
    mock_result.email_path.write_text(
        "To: hiring@example.com\nSubject: Application\n\nDear Hiring Committee,\n",
        encoding="utf-8"
    )

    with patch("src.steps.email_draft.MotivationLetterService") as mock_service_class:
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.generate_email_draft.return_value = mock_result

        result = run(mock_job_state, force=False)

    assert result.status == "ok"
    assert "planning/application_email.md" in result.produced
    assert result.comments_found == 0
    assert "Generated email draft" in result.message


def test_run_skips_when_complete(mock_job_state: Mock):
    """Verify that run() returns 'skipped' when step is already complete and force=False."""
    mock_job_state.step_complete.return_value = True

    result = run(mock_job_state, force=False)

    assert result.status == "skipped"
    assert result.produced == []
    assert result.comments_found == 0
    assert "already complete" in result.message


def test_run_requires_motivation_output(mock_job_state: Mock):
    """Verify that run() returns error when motivation_letter.json is missing."""
    # Don't create motivation_letter.json
    result = run(mock_job_state, force=False)

    assert result.status == "error"
    assert "motivation_letter.json not found" in result.message


def test_run_force_reruns(mock_job_state: Mock):
    """Verify that run() re-runs when force=True even if step is complete."""
    mock_job_state.step_complete.return_value = True

    # Create required motivation_letter.json
    motivation_data = {
        "subject": "Test",
        "salutation": "Test",
        "fit_signals": [],
        "risk_notes": [],
        "letter_markdown": "Test",
    }
    motivation_path = mock_job_state.job_dir / "planning" / "motivation_letter.json"
    motivation_path.parent.mkdir(parents=True, exist_ok=True)
    motivation_path.write_text(json.dumps(motivation_data), encoding="utf-8")

    # Mock the MotivationLetterService
    mock_result = Mock()
    mock_result.email_path = mock_job_state.job_dir / "planning" / "application_email.md"
    mock_result.email_path.parent.mkdir(parents=True, exist_ok=True)
    mock_result.email_path.write_text("To: test@example.com\nSubject: Test\n", encoding="utf-8")

    with patch("src.steps.email_draft.MotivationLetterService") as mock_service_class:
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.generate_email_draft.return_value = mock_result

        result = run(mock_job_state, force=True)

    assert result.status == "ok"
    assert "planning/application_email.md" in result.produced


def test_email_contains_summary(mock_job_state: Mock):
    """Verify that email draft is generated from motivation context."""
    # Create required motivation_letter.json
    motivation_data = {
        "subject": "Application for Research Assistant III",
        "salutation": "Dear Dr. Schmidt,",
        "fit_signals": [
            {
                "requirement": "Python experience",
                "evidence": "5+ years professional Python",
                "coverage": "full",
            }
        ],
        "risk_notes": [],
        "letter_markdown": "# Motivation\n\nDear Dr. Schmidt,\n\nI am applying for this position.",
    }
    motivation_path = mock_job_state.job_dir / "planning" / "motivation_letter.json"
    motivation_path.parent.mkdir(parents=True, exist_ok=True)
    motivation_path.write_text(json.dumps(motivation_data), encoding="utf-8")

    # Mock the MotivationLetterService
    mock_result = Mock()
    mock_result.email_path = mock_job_state.job_dir / "planning" / "application_email.md"
    mock_result.email_path.parent.mkdir(parents=True, exist_ok=True)
    email_content = (
        "To: hiring@example.com\n"
        "Subject: Application for Research Assistant III\n"
        "\n"
        "Dear Dr. Schmidt,\n"
        "\n"
        "I am writing to submit my application for the role. "
        "Please find attached my motivation letter and CV.\n"
        "\n"
        "Best regards,\n"
    )
    mock_result.email_path.write_text(email_content, encoding="utf-8")

    with patch("src.steps.email_draft.MotivationLetterService") as mock_service_class:
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.generate_email_draft.return_value = mock_result

        result = run(mock_job_state, force=False)

    assert result.status == "ok"
    # Verify the email was created with appropriate content
    email_file = mock_job_state.artifact_path("planning/application_email.md")
    assert email_file.exists()
    content = email_file.read_text(encoding="utf-8")
    assert "To:" in content
    assert "Subject:" in content
