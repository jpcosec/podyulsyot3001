"""Unit tests for WorkspaceManager."""

from __future__ import annotations

import pytest

from src.core.io import WorkspaceManager


@pytest.fixture
def workspace(tmp_path) -> WorkspaceManager:
    """Create a WorkspaceManager with temporary root."""
    return WorkspaceManager(jobs_root=tmp_path / "jobs")


def test_job_root(workspace: WorkspaceManager, tmp_path) -> None:
    """Test job_root returns correct path."""
    result = workspace.job_root("stepstone", "12345")
    expected = tmp_path / "jobs" / "stepstone" / "12345"
    assert result == expected


def test_node_root(workspace: WorkspaceManager, tmp_path) -> None:
    """Test node_root returns correct path."""
    result = workspace.node_root("stepstone", "12345", "extract_bridge")
    expected = tmp_path / "jobs" / "stepstone" / "12345" / "nodes" / "extract_bridge"
    assert result == expected


def test_node_stage_dir(workspace: WorkspaceManager, tmp_path) -> None:
    """Test node_stage_dir returns correct path."""
    result = workspace.node_stage_dir(
        "stepstone", "12345", "extract_bridge", "proposed"
    )
    expected = (
        tmp_path
        / "jobs"
        / "stepstone"
        / "12345"
        / "nodes"
        / "extract_bridge"
        / "proposed"
    )
    assert result == expected


def test_node_stage_artifact(workspace: WorkspaceManager, tmp_path) -> None:
    """Test node_stage_artifact returns correct path."""
    result = workspace.node_stage_artifact(
        "stepstone", "12345", "extract_bridge", "proposed", "state.json"
    )
    expected = (
        tmp_path
        / "jobs"
        / "stepstone"
        / "12345"
        / "nodes"
        / "extract_bridge"
        / "proposed"
        / "state.json"
    )
    assert result == expected


def test_validated_segment_rejects_empty(workspace: WorkspaceManager) -> None:
    """Test that empty segment raises ValueError."""
    with pytest.raises(ValueError, match="is required"):
        workspace._validated_segment("", "source")


def test_validated_segment_rejects_whitespace_only(workspace: WorkspaceManager) -> None:
    """Test that whitespace-only segment raises ValueError."""
    with pytest.raises(ValueError, match="is required"):
        workspace._validated_segment("   ", "source")


def test_validated_segment_rejects_invalid_chars(workspace: WorkspaceManager) -> None:
    """Test that invalid characters raise ValueError."""
    with pytest.raises(ValueError, match="unsupported characters"):
        workspace._validated_segment("step/stone", "source")


def test_validated_segment_accepts_valid(workspace: WorkspaceManager) -> None:
    """Test that valid segments are accepted."""
    result = workspace._validated_segment("stepstone_123", "source")
    assert result == "stepstone_123"


def test_safe_relative_path_rejects_absolute(workspace: WorkspaceManager) -> None:
    """Test that absolute paths are rejected."""
    with pytest.raises(ValueError, match="must not be absolute"):
        workspace._safe_relative_path("/etc/passwd")


def test_safe_relative_path_rejects_parent_traversal(
    workspace: WorkspaceManager,
) -> None:
    """Test that parent traversal is rejected."""
    with pytest.raises(ValueError, match="must not contain '..'"):
        workspace._safe_relative_path("../etc/passwd")


def test_safe_relative_path_accepts_nested(workspace: WorkspaceManager) -> None:
    """Test that nested relative paths are accepted."""
    result = workspace._safe_relative_path("nodes/extract_bridge/proposed")
    assert str(result) == "nodes/extract_bridge/proposed"


def test_resolve_under_job_prevents_escape_via_parent_ref(
    workspace: WorkspaceManager,
) -> None:
    """Test that path cannot escape job root via parent refs."""
    with pytest.raises(ValueError, match="must not contain '..'"):
        workspace.resolve_under_job("stepstone", "12345", "../../../etc/passwd")


def test_resolve_under_job_prevents_escape_via_symlink(tmp_path) -> None:
    """Test that symlinks cannot escape job root."""
    import os

    wm = WorkspaceManager(jobs_root=tmp_path / "jobs")

    job_dir = tmp_path / "jobs" / "stepstone" / "12345"
    job_dir.mkdir(parents=True)

    escape_dir = tmp_path / "escape"
    escape_dir.mkdir()
    (escape_dir / "file.txt").write_text("escaped")

    symlink_dir = job_dir / "nodes"
    symlink_dir.mkdir()
    os.symlink(escape_dir, symlink_dir / "link", target_is_directory=True)

    with pytest.raises(ValueError, match="escapes job root"):
        wm.resolve_under_job("stepstone", "12345", "nodes/link/file.txt")


def test_resolve_under_job_accepts_valid_path(workspace: WorkspaceManager) -> None:
    """Test that valid relative paths work."""
    result = workspace.resolve_under_job("stepstone", "12345", "nodes/test/file.txt")
    assert "jobs/stepstone/12345/nodes/test/file.txt" in str(result)


def test_write_json_and_read_json(workspace: WorkspaceManager) -> None:
    """Test writing and reading JSON."""
    data = {"key": "value", "number": 42}
    workspace.write_json("stepstone", "12345", "test.json", data)

    result = workspace.read_json("stepstone", "12345", "test.json")
    assert result == data


def test_write_text_and_read_text(workspace: WorkspaceManager) -> None:
    """Test writing and reading text."""
    content = "Hello, World!"
    workspace.write_text("stepstone", "12345", "test.txt", content)

    result = workspace.read_text("stepstone", "12345", "test.txt")
    assert result == content


def test_ensure_parent_creates_directories(tmp_path) -> None:
    """Test that ensure_parent creates parent directories."""
    wm = WorkspaceManager(jobs_root=tmp_path)
    path = tmp_path / "jobs" / "stepstone" / "12345" / "nodes" / "test" / "file.txt"
    wm.ensure_parent(path)

    assert path.parent.exists()
    assert path.parent.is_dir()


def test_path_resolution_with_special_chars_in_job_id(
    workspace: WorkspaceManager,
) -> None:
    """Test that job IDs with special characters are rejected."""
    with pytest.raises(ValueError, match="unsupported characters"):
        workspace.job_root("stepstone", "123/456")


def test_path_resolution_with_special_chars_in_source(
    workspace: WorkspaceManager,
) -> None:
    """Test that source with special characters are rejected."""
    with pytest.raises(ValueError, match="unsupported characters"):
        workspace.job_root("step@stone", "12345")
