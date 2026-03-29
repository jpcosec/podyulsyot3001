"""Unit tests for the extract_bridge node."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.io import WorkspaceManager
from src.graph.nodes.extract_bridge import (
    ExtractBridgeError,
    extract_bridge,
)


@pytest.fixture
def temp_data_root(tmp_path: Path) -> Path:
    """Create a temporary data source directory structure."""
    data_root = tmp_path / "data" / "source"
    data_root.mkdir(parents=True, exist_ok=True)
    return data_root


@pytest.fixture
def temp_output_root(tmp_path: Path) -> Path:
    """Create a temporary output directory structure."""
    output_root = tmp_path / "output" / "match_skill"
    output_root.mkdir(parents=True, exist_ok=True)
    return output_root


def _write_job_data(data_root: Path, source: str, job_id: str, data: dict) -> None:
    """Helper to write job posting data."""
    job_dir = data_root / source / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "extracted_data.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


def test_extract_bridge_success(temp_data_root: Path, temp_output_root: Path) -> None:
    """Test successful extraction of requirements from job posting data."""
    job_data = {
        "job_title": "Test Engineer",
        "company_name": "Test Corp",
        "requirements": [
            "5+ years Python experience",
            "Experience with LangGraph",
            "Strong communication skills",
        ],
    }
    _write_job_data(temp_data_root, "stepstone", "12345", job_data)

    result = extract_bridge(
        source="stepstone",
        job_id="12345",
        data_root=temp_data_root,
        output_root=temp_output_root,
    )

    assert len(result) == 3
    assert result[0].id == "REQ_001"
    assert result[0].text == "5+ years Python experience"
    assert result[0].priority == "must"
    assert result[1].id == "REQ_002"
    assert result[2].id == "REQ_003"


def test_extract_bridge_writes_state_json(
    temp_data_root: Path, temp_output_root: Path
) -> None:
    """Test that state.json is written to the correct output location."""
    job_data = {
        "job_title": "Test Engineer",
        "company_name": "Test Corp",
        "requirements": ["Python skill"],
    }
    _write_job_data(temp_data_root, "stepstone", "12345", job_data)

    extract_bridge(
        source="stepstone",
        job_id="12345",
        data_root=temp_data_root,
        output_root=temp_output_root,
    )

    state_file = (
        temp_output_root
        / "stepstone"
        / "12345"
        / "nodes"
        / "extract_bridge"
        / "proposed"
        / "state.json"
    )
    assert state_file.exists()

    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert state["source"] == "stepstone"
    assert state["job_id"] == "12345"
    assert len(state["requirements"]) == 1
    assert state["requirements"][0]["id"] == "REQ_001"


def test_extract_bridge_prefers_en_file(
    temp_data_root: Path, temp_output_root: Path
) -> None:
    """Test that extracted_data_en.json is preferred over extracted_data.json."""
    job_dir = temp_data_root / "xing" / "999"
    job_dir.mkdir(parents=True, exist_ok=True)

    en_data = {
        "requirements": ["English requirement"],
    }
    (job_dir / "extracted_data_en.json").write_text(
        json.dumps(en_data), encoding="utf-8"
    )

    raw_data = {
        "requirements": ["German requirement"],
    }
    (job_dir / "extracted_data.json").write_text(json.dumps(raw_data), encoding="utf-8")

    result = extract_bridge(
        source="xing",
        job_id="999",
        data_root=temp_data_root,
        output_root=temp_output_root,
    )

    assert len(result) == 1
    assert result[0].text == "English requirement"


def test_extract_bridge_missing_requirements_returns_error_requirement(
    temp_data_root: Path, temp_output_root: Path
) -> None:
    """Test that missing requirements field returns error dummy requirement."""
    job_data = {
        "job_title": "Test Engineer",
        "company_name": "Test Corp",
    }
    _write_job_data(temp_data_root, "stepstone", "12345", job_data)

    result = extract_bridge(
        source="stepstone",
        job_id="12345",
        data_root=temp_data_root,
        output_root=temp_output_root,
    )

    assert len(result) == 1
    assert result[0].id == "REQ_ERROR"
    assert "[ERROR:" in result[0].text


def test_extract_bridge_missing_file_returns_error_requirement(
    temp_data_root: Path, temp_output_root: Path
) -> None:
    """Test that missing data file returns error dummy requirement."""
    result = extract_bridge(
        source="stepstone",
        job_id="12345",
        data_root=temp_data_root,
        output_root=temp_output_root,
    )

    assert len(result) == 1
    assert result[0].id == "REQ_ERROR"
    assert "[ERROR:" in result[0].text


def test_extract_bridge_with_workspace(temp_data_root: Path, tmp_path: Path) -> None:
    """Test that extract_bridge works with WorkspaceManager."""
    job_data = {
        "job_title": "Test Engineer",
        "company_name": "Test Corp",
        "requirements": [
            "5+ years Python experience",
            "Experience with LangGraph",
        ],
    }
    _write_job_data(temp_data_root, "stepstone", "12345", job_data)

    workspace = WorkspaceManager(jobs_root=tmp_path / "output")

    result = extract_bridge(
        source="stepstone",
        job_id="12345",
        data_root=temp_data_root,
        workspace=workspace,
    )

    assert len(result) == 2
    assert result[0].id == "REQ_001"
    assert result[0].text == "5+ years Python experience"
    assert result[1].id == "REQ_002"

    state_path = workspace.node_stage_artifact(
        "stepstone", "12345", "extract_bridge", "proposed", "state.json"
    )
    assert state_path.exists()

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["source"] == "stepstone"
    assert state["job_id"] == "12345"


def test_extract_bridge_copies_content_md(
    temp_data_root: Path, temp_output_root: Path
) -> None:
    """Test that content.md is copied to output directory."""
    job_data = {
        "job_title": "Test Engineer",
        "company_name": "Test Corp",
        "requirements": ["Python skill"],
    }
    job_dir = temp_data_root / "stepstone" / "12345"
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "extracted_data.json").write_text(json.dumps(job_data), encoding="utf-8")
    (job_dir / "content.md").write_text("# Job Content", encoding="utf-8")

    extract_bridge(
        source="stepstone",
        job_id="12345",
        data_root=temp_data_root,
        output_root=temp_output_root,
    )

    content_dst = (
        temp_output_root
        / "stepstone"
        / "12345"
        / "nodes"
        / "extract_bridge"
        / "proposed"
        / "content.md"
    )
    assert content_dst.exists()
    assert content_dst.read_text(encoding="utf-8") == "# Job Content"


def test_extract_bridge_handles_empty_requirements(
    temp_data_root: Path, temp_output_root: Path
) -> None:
    """Test that empty requirements list returns error requirement."""
    job_data = {
        "job_title": "Test Engineer",
        "company_name": "Test Corp",
        "requirements": [],
    }
    _write_job_data(temp_data_root, "stepstone", "12345", job_data)

    result = extract_bridge(
        source="stepstone",
        job_id="12345",
        data_root=temp_data_root,
        output_root=temp_output_root,
    )

    assert len(result) == 1
    assert result[0].id == "REQ_ERROR"


def test_extract_bridge_handles_malformed_json(
    temp_data_root: Path, temp_output_root: Path
) -> None:
    """Test that malformed JSON returns error dummy requirement."""
    job_dir = temp_data_root / "stepstone" / "12345"
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "extracted_data.json").write_text("{ invalid json }", encoding="utf-8")

    result = extract_bridge(
        source="stepstone",
        job_id="12345",
        data_root=temp_data_root,
        output_root=temp_output_root,
    )

    assert len(result) == 1
    assert result[0].id == "REQ_ERROR"
    assert "[ERROR:" in result[0].text
