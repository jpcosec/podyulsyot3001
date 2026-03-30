"""Tests for the schema-v0 DataManager."""

from __future__ import annotations

from src.core.data_manager import DataManager


def test_ensure_job_creates_meta(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")

    metadata = manager.ensure_job("stepstone", "12345")

    meta_path = tmp_path / "data" / "jobs" / "stepstone" / "12345" / "meta.json"
    assert meta_path.exists()
    assert metadata.schema_version == "v0"
    assert metadata.status == "active"


def test_update_job_status_does_not_move_job_root(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")
    manager.ensure_job("stepstone", "12345")

    updated = manager.update_job_status("stepstone", "12345", "urgent")

    job_root = tmp_path / "data" / "jobs" / "stepstone" / "12345"
    assert job_root.exists()
    assert updated.status == "urgent"


def test_write_and_read_json_artifact(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")

    path = manager.write_json_artifact(
        source="stepstone",
        job_id="12345",
        node_name="translate",
        stage="proposed",
        filename="state.json",
        data={"language": "en"},
    )

    assert path.exists()
    assert manager.read_json_artifact(
        source="stepstone",
        job_id="12345",
        node_name="translate",
        stage="proposed",
        filename="state.json",
    ) == {"language": "en"}


def test_write_and_read_text_artifact(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")

    path = manager.write_text_artifact(
        source="stepstone",
        job_id="12345",
        node_name="ingest",
        stage="proposed",
        filename="content.md",
        content="# Job",
    )

    assert path.exists()
    assert (
        manager.read_text_artifact(
            source="stepstone",
            job_id="12345",
            node_name="ingest",
            stage="proposed",
            filename="content.md",
        )
        == "# Job"
    )


def test_ingest_raw_job_writes_canonical_artifacts(tmp_path) -> None:
    manager = DataManager(tmp_path / "data" / "jobs")

    refs = manager.ingest_raw_job(
        source="stepstone",
        job_id="12345",
        payload={"job_title": "Engineer"},
        content="# Posting",
        metadata={"success": True},
        raw_html="<html>raw</html>",
        cleaned_html="<html>clean</html>",
    )

    assert refs["state"].exists()
    assert refs["content"].exists()
    assert refs["meta"].exists()
    assert refs["raw_html"].exists()
    assert refs["cleaned_html"].exists()
    assert manager.has_ingested_job("stepstone", "12345") is True
