"""Unit tests for the extract_bridge node."""

from __future__ import annotations

import json

import pytest

from src.core.io import WorkspaceManager
from src.graph.nodes.extract_bridge import (
    ExtractBridgeError,
    extract_bridge,
    extract_requirements_from_job_posting,
)


@pytest.fixture
def workspace(tmp_path) -> WorkspaceManager:
    """Create a temporary schema-v0 workspace."""

    return WorkspaceManager(jobs_root=tmp_path / "data" / "jobs")


def _write_translated_job(
    workspace: WorkspaceManager,
    source: str,
    job_id: str,
    data: dict,
    content: str | None = None,
) -> None:
    workspace.write_json(source, job_id, "nodes/translate/proposed/state.json", data)
    if content is not None:
        workspace.write_text(
            source, job_id, "nodes/translate/proposed/content.md", content
        )


def test_extract_requirements_from_job_posting_success() -> None:
    result = extract_requirements_from_job_posting(
        {"requirements": ["Python", "LangGraph"]}
    )

    assert [item.id for item in result] == ["REQ_001", "REQ_002"]
    assert [item.text for item in result] == ["Python", "LangGraph"]


def test_extract_requirements_from_job_posting_raises_on_missing_requirements() -> None:
    with pytest.raises(ExtractBridgeError, match="No requirements"):
        extract_requirements_from_job_posting({"job_title": "Engineer"})


def test_extract_bridge_success(workspace: WorkspaceManager) -> None:
    _write_translated_job(
        workspace,
        "stepstone",
        "12345",
        {
            "job_title": "Test Engineer",
            "company_name": "Test Corp",
            "requirements": [
                "5+ years Python experience",
                "Experience with LangGraph",
                "Strong communication skills",
            ],
        },
    )

    result = extract_bridge("stepstone", "12345", workspace)

    assert len(result) == 3
    assert result[0].id == "REQ_001"
    assert result[0].text == "5+ years Python experience"


def test_extract_bridge_writes_state_json(workspace: WorkspaceManager) -> None:
    _write_translated_job(
        workspace,
        "stepstone",
        "12345",
        {
            "job_title": "Test Engineer",
            "company_name": "Test Corp",
            "requirements": ["Python skill"],
        },
    )

    extract_bridge("stepstone", "12345", workspace)

    state = workspace.read_json(
        "stepstone",
        "12345",
        "nodes/extract_bridge/proposed/state.json",
    )
    assert state["source"] == "stepstone"
    assert state["job_id"] == "12345"
    assert state["requirements"][0]["id"] == "REQ_001"


def test_extract_bridge_copies_content_md(workspace: WorkspaceManager) -> None:
    _write_translated_job(
        workspace,
        "stepstone",
        "12345",
        {
            "requirements": ["Python skill"],
        },
        content="# Job Content",
    )

    extract_bridge("stepstone", "12345", workspace)

    assert (
        workspace.read_text(
            "stepstone", "12345", "nodes/extract_bridge/proposed/content.md"
        )
        == "# Job Content"
    )


def test_extract_bridge_raises_on_missing_input(workspace: WorkspaceManager) -> None:
    with pytest.raises(ExtractBridgeError, match="Failed to load translated state"):
        extract_bridge("stepstone", "12345", workspace)


def test_extract_bridge_raises_on_empty_requirements(
    workspace: WorkspaceManager,
) -> None:
    _write_translated_job(
        workspace,
        "stepstone",
        "12345",
        {"requirements": []},
    )

    with pytest.raises(ExtractBridgeError, match="No requirements"):
        extract_bridge("stepstone", "12345", workspace)


def test_extract_bridge_raises_on_malformed_json(workspace: WorkspaceManager) -> None:
    path = workspace.resolve_under_job(
        "stepstone",
        "12345",
        "nodes/translate/proposed/state.json",
    )
    workspace.ensure_parent(path)
    path.write_text("{ invalid json }", encoding="utf-8")

    with pytest.raises(ExtractBridgeError, match="Failed to load translated state"):
        extract_bridge("stepstone", "12345", workspace)
