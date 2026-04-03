from __future__ import annotations

import json

import pytest

from src.core.ai.generate_documents_v2.contracts.job import (
    CompanyData,
    JobKG,
    JobLogistics,
    JobRequirement,
)
from src.core.ai.generate_documents_v2.nodes.ingestion import (
    load_ingestion_artifact_bundle,
    run_ingestion,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


FAKE_JOB_KG = JobKG(
    source_language="de",
    job_title_original="Data Scientist / KI-Expert (w/m/d)",
    job_title_english="Data Scientist / AI Expert",
    hard_requirements=[
        JobRequirement(id="R1", text="Python 3.10+", category="hard", priority=5),
        JobRequirement(id="R2", text="Rust experience", category="hard", priority=4),
    ],
    soft_context=[
        JobRequirement(id="S1", text="Team player", category="soft", priority=2),
    ],
    logistics=JobLogistics(location="Munich", relocation=True),
    company=CompanyData(name="Deutsche Bahn AG", department="Data & Analytics"),
)


class FakeIngestionChain:
    def __init__(self, response: JobKG):
        self._response = response
        self.calls: list[dict] = []

    def invoke(self, payload: dict) -> JobKG:
        self.calls.append(payload)
        return self._response


@pytest.fixture
def store(tmp_path):
    return PipelineArtifactStore(tmp_path)


def test_run_ingestion_returns_job_kg(store):
    chain = FakeIngestionChain(FAKE_JOB_KG)
    result = run_ingestion(
        source="demo",
        job_id="job-1",
        job_raw_text="We are looking for a Python and Rust engineer at Deutsche Bahn...",
        chain=chain,
        store=store,
    )
    assert "job_kg" in result
    kg = JobKG.model_validate(result["job_kg"])
    assert kg.company.name == "Deutsche Bahn AG"
    assert len(kg.hard_requirements) == 2


def test_run_ingestion_writes_to_disk(store, tmp_path):
    chain = FakeIngestionChain(FAKE_JOB_KG)
    run_ingestion(
        source="demo",
        job_id="job-2",
        job_raw_text="Software Engineer position...",
        chain=chain,
        store=store,
    )
    stored = json.loads(
        (
            tmp_path / "demo/job-2/nodes/generate_documents_v2/job_kg/current.json"
        ).read_text()
    )
    assert stored["company"]["name"] == "Deutsche Bahn AG"


def test_run_ingestion_calls_chain_once(store):
    chain = FakeIngestionChain(FAKE_JOB_KG)
    run_ingestion(
        source="demo",
        job_id="job-3",
        job_raw_text="some job text",
        chain=chain,
        store=store,
    )
    assert len(chain.calls) == 1


def test_run_ingestion_sets_status(store):
    chain = FakeIngestionChain(FAKE_JOB_KG)
    result = run_ingestion(
        source="demo",
        job_id="job-4",
        job_raw_text="some text",
        chain=chain,
        store=store,
    )
    assert result.get("status") == "job_extracted"


def test_run_ingestion_uses_bundle_prompt(store):
    chain = FakeIngestionChain(FAKE_JOB_KG)
    bundle = {
        "state": {"job_title": "Dateningenieur", "requirements": ["Python"]},
        "listing": {"listing_data": {"salary": "EUR 50k"}},
        "listing_case": {"teaser_location": "Berlin"},
    }
    run_ingestion(
        source="demo",
        job_id="job-5",
        job_bundle=bundle,
        chain=chain,
        store=store,
    )
    user_prompt = chain.calls[0]["user"]
    assert "CANONICAL STATE JSON" in user_prompt
    assert "LISTING JSON" in user_prompt
    assert "listing_data" in user_prompt


def test_load_ingestion_artifact_bundle_reads_minimal_files(tmp_path):
    base = tmp_path / "demo/job-1/nodes/ingest/proposed"
    base.mkdir(parents=True)
    (base / "state.json").write_text('{"job_title": "Role"}', encoding="utf-8")
    (base / "listing.json").write_text(
        '{"listing_data": {"salary": "EUR 50k"}}',
        encoding="utf-8",
    )
    bundle = load_ingestion_artifact_bundle(
        source="demo",
        job_id="job-1",
        jobs_root=tmp_path,
    )
    assert bundle["state"]["job_title"] == "Role"
    assert bundle["listing"]["listing_data"]["salary"] == "EUR 50k"


def test_run_ingestion_recovers_from_empty_model_output(store):
    chain = FakeIngestionChain(JobKG())
    bundle = {
        "state": {
            "job_title": "Dateningenieur",
            "company_name": "ACME",
            "location": "Berlin",
            "employment_type": "Full-time",
            "original_language": "en",
            "requirements": ["Python", "SQL"],
        }
    }
    result = run_ingestion(
        source="demo",
        job_id="job-6",
        job_bundle=bundle,
        chain=chain,
        store=store,
    )
    assert len(result["job_kg"]["hard_requirements"]) == 2
    assert result["job_kg"]["company"]["name"] == "ACME"
