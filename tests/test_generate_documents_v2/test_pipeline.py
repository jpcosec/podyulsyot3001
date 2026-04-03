from __future__ import annotations

import pytest

from src.core.ai.generate_documents_v2.pipeline import generate_application_documents
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


@pytest.fixture
def store(tmp_path):
    return PipelineArtifactStore(tmp_path)


def test_generate_application_documents_runs_end_to_end(store, tmp_path):
    ingest_dir = tmp_path / "demo/job-1/nodes/ingest/proposed"
    ingest_dir.mkdir(parents=True)
    (ingest_dir / "state.json").write_text(
        '{"job_title": "Dateningenieur", "company_name": "ACME", "location": "Berlin", "requirements": ["Python", "SQL"], "responsibilities": ["Build pipelines"], "original_language": "de"}',
        encoding="utf-8",
    )
    (ingest_dir / "listing.json").write_text(
        '{"listing_data": {"salary": "EUR 50k"}}',
        encoding="utf-8",
    )
    (ingest_dir / "listing_case.json").write_text(
        '{"teaser_location": "Berlin"}',
        encoding="utf-8",
    )

    result = generate_application_documents(
        source="demo",
        job_id="job-1",
        profile_path="tests/e2e/fixtures/stub_profile.json",
        target_language="en",
        store=store,
    )
    assert result["status"] == "assembled"
    assert "markdown_bundle" in result
    assert (
        tmp_path / "demo/job-1/nodes/generate_documents_v2/proposed/cv.en.md"
    ).exists()
