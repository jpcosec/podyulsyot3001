"""Tests for prep-match CLI helper."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.cli.run_prep_match import (
    _load_dotenv_if_present,
    _load_profile_evidence,
    _write_run_summary_artifact,
    _write_verification_artifact,
)


def test_load_profile_evidence_requires_path() -> None:
    with pytest.raises(ValueError, match="profile-evidence"):
        _load_profile_evidence(None)


def test_load_profile_evidence_reads_list_of_dicts(tmp_path: Path) -> None:
    p = tmp_path / "profile.json"
    p.write_text(
        json.dumps([{"id": "P1", "description": "Python"}, "skip", {"id": "P2"}]),
        encoding="utf-8",
    )
    out = _load_profile_evidence(str(p))
    assert out == [{"id": "P1", "description": "Python"}, {"id": "P2"}]


def test_load_profile_evidence_reads_profile_base_shape(tmp_path: Path) -> None:
    p = tmp_path / "profile_base_data.json"
    p.write_text(
        json.dumps(
            {
                "cv_generation_context": {
                    "professional_summary_seed": "Applied AI engineer",
                    "tagline_seed": "AI profile",
                },
                "education": [
                    {
                        "degree": "Electrical Engineering",
                        "specialization": "Computational Intelligence",
                        "institution": "UChile",
                    }
                ],
                "experience": [
                    {
                        "role": "ML Engineer",
                        "organization": "Kwali",
                        "achievements": ["Built CV pipelines"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    out = _load_profile_evidence(str(p))

    assert len(out) >= 2
    assert all("id" in item and "description" in item for item in out)
    assert all(not item["id"].startswith("P_SUM") for item in out)


def test_write_run_summary_artifact_writes_graph_summary(tmp_path: Path) -> None:
    state = {
        "source": "tu_berlin",
        "job_id": "job-1",
        "run_id": "run-1",
        "current_node": "package",
        "status": "completed",
    }

    prev_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        _write_run_summary_artifact(state)
    finally:
        os.chdir(prev_cwd)

    summary_path = tmp_path / "data/jobs/tu_berlin/job-1/graph/run_summary.json"
    assert summary_path.exists()
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["current_node"] == "package"
    assert payload["status"] == "completed"


def test_write_run_summary_artifact_includes_error_state(tmp_path: Path) -> None:
    state = {
        "source": "tu_berlin",
        "job_id": "job-err",
        "run_id": "run-err",
        "current_node": "match",
        "status": "failed",
        "error_state": {
            "failure_type": "INTERNAL_ERROR",
            "message": "boom",
            "attempt_count": 1,
        },
    }

    prev_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        _write_run_summary_artifact(state)
    finally:
        os.chdir(prev_cwd)

    summary_path = tmp_path / "data/jobs/tu_berlin/job-err/graph/run_summary.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["error_state"]["message"] == "boom"


def test_write_verification_artifact(tmp_path: Path) -> None:
    report = {
        "verifier": "prep_match_v1",
        "passed": True,
        "score": 1.0,
        "checks": [],
    }

    prev_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        _write_verification_artifact(
            source="tu_berlin",
            job_id="job-2",
            verification_report=report,
        )
    finally:
        os.chdir(prev_cwd)

    out_path = tmp_path / "data/jobs/tu_berlin/job-2/graph/langsmith_verification.json"
    assert out_path.exists()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["passed"] is True


def test_load_dotenv_if_present_loads_env_vars(tmp_path: Path, monkeypatch) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text("LANGSMITH_PROJECT=from-dotenv\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LANGSMITH_PROJECT", raising=False)

    _load_dotenv_if_present()

    assert os.environ.get("LANGSMITH_PROJECT") == "from-dotenv"


def test_load_dotenv_if_present_does_not_override_existing_env(
    tmp_path: Path, monkeypatch
) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text("LANGSMITH_PROJECT=from-dotenv\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LANGSMITH_PROJECT", "from-env")

    _load_dotenv_if_present()

    assert os.environ.get("LANGSMITH_PROJECT") == "from-env"
