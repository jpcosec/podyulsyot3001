"""Tests for the motivation step."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.steps import StepResult
from src.steps.motivation import run
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


def test_run_produces_letter_artifacts(mock_job_state: Mock):
    """Verify that run() produces motivation_letter.md and motivation_letter.json."""
    # Create required reviewed_mapping.json
    mapping_data = {
        "status": "reviewed",
        "claims": [
            {
                "requirement": "Python experience",
                "decision": "approved",
                "evidence": "5 years professional Python",
            }
        ],
        "summary": "Strong fit for the role",
    }
    mapping_path = mock_job_state.job_dir / "planning" / "reviewed_mapping.json"
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    mapping_path.write_text(json.dumps(mapping_data, indent=2), encoding="utf-8")

    # Mock the MotivationLetterService
    mock_result = Mock()
    mock_result.letter_path = mock_job_state.job_dir / "planning" / "motivation_letter.md"
    mock_result.analysis_path = mock_job_state.job_dir / "planning" / "motivation_letter.json"

    # Ensure output files exist
    mock_result.letter_path.parent.mkdir(parents=True, exist_ok=True)
    mock_result.letter_path.write_text("# Motivation Letter\n\nDear Hiring Committee,\n", encoding="utf-8")
    mock_result.analysis_path.write_text(
        json.dumps({
            "subject": "Application",
            "salutation": "Dear Hiring Committee,",
            "fit_signals": [],
            "risk_notes": [],
            "letter_markdown": "# Motivation Letter\n\nDear Hiring Committee,\n",
        }, indent=2),
        encoding="utf-8"
    )

    with patch("src.steps.motivation.MotivationLetterService") as mock_service_class:
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.generate_for_job.return_value = mock_result

        result = run(mock_job_state, force=False)

    assert result.status == "ok"
    assert "planning/motivation_letter.md" in result.produced
    assert "planning/motivation_letter.json" in result.produced
    assert result.comments_found == 0
    assert "Generated motivation letter" in result.message


def test_run_skips_when_complete(mock_job_state: Mock):
    """Verify that run() returns 'skipped' when step is already complete and force=False."""
    mock_job_state.step_complete.return_value = True

    result = run(mock_job_state, force=False)

    assert result.status == "skipped"
    assert result.produced == []
    assert result.comments_found == 0
    assert "already complete" in result.message


def test_run_force_reruns(mock_job_state: Mock):
    """Verify that run() re-runs when force=True even if step is complete."""
    mock_job_state.step_complete.return_value = True

    # Create required reviewed_mapping.json
    mapping_data = {
        "status": "reviewed",
        "claims": [{"requirement": "Test", "decision": "approved", "evidence": "test"}],
        "summary": "Test summary",
    }
    mapping_path = mock_job_state.job_dir / "planning" / "reviewed_mapping.json"
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    mapping_path.write_text(json.dumps(mapping_data), encoding="utf-8")

    # Mock the MotivationLetterService
    mock_result = Mock()
    mock_result.letter_path = mock_job_state.job_dir / "planning" / "motivation_letter.md"
    mock_result.analysis_path = mock_job_state.job_dir / "planning" / "motivation_letter.json"
    mock_result.letter_path.parent.mkdir(parents=True, exist_ok=True)
    mock_result.letter_path.write_text("# Test Letter", encoding="utf-8")
    mock_result.analysis_path.write_text(json.dumps({"test": "data"}, indent=2), encoding="utf-8")

    with patch("src.steps.motivation.MotivationLetterService") as mock_service_class:
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.generate_for_job.return_value = mock_result

        result = run(mock_job_state, force=True)

    assert result.status == "ok"
    assert "planning/motivation_letter.md" in result.produced


def test_run_requires_reviewed_mapping(mock_job_state: Mock):
    """Verify that run() returns error when reviewed_mapping.json is missing."""
    # Don't create reviewed_mapping.json
    result = run(mock_job_state, force=False)

    assert result.status == "error"
    assert "reviewed_mapping.json not found" in result.message


def test_run_reads_comments(mock_job_state: Mock):
    """Verify that run() extracts and logs comments from previous outputs."""
    # Create required reviewed_mapping.json
    mapping_data = {
        "status": "reviewed",
        "claims": [{"requirement": "Test", "decision": "approved", "evidence": "test"}],
        "summary": "Test",
    }
    mapping_path = mock_job_state.job_dir / "planning" / "reviewed_mapping.json"
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    mapping_path.write_text(json.dumps(mapping_data), encoding="utf-8")

    # Create a motivation_letter.md with comments
    letter_path = mock_job_state.job_dir / "planning" / "motivation_letter.md"
    letter_path.write_text("# Test\n<!-- This is a test comment -->\nBody", encoding="utf-8")

    # Mock the MotivationLetterService
    mock_result = Mock()
    mock_result.letter_path = letter_path
    mock_result.analysis_path = mock_job_state.job_dir / "planning" / "motivation_letter.json"
    mock_result.analysis_path.parent.mkdir(parents=True, exist_ok=True)
    mock_result.analysis_path.write_text(json.dumps({"test": "data"}), encoding="utf-8")
    mock_result.letter_path.write_text("# Updated Test", encoding="utf-8")

    with patch("src.steps.motivation.MotivationLetterService") as mock_service_class:
        with patch("src.steps.motivation.append_to_comment_log") as mock_log:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.generate_for_job.return_value = mock_result

            result = run(mock_job_state, force=False)

    assert result.status == "ok"
    # Comments should have been found and logged
    assert mock_log.called
