from __future__ import annotations

import json

import pytest

from src.core.ai.generate_documents_v2.contracts.job import (
    CompanyData,
    JobDelta,
    JobKG,
    JobLogistics,
    JobRequirement,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


@pytest.fixture
def store(tmp_path):
    return PipelineArtifactStore(tmp_path)


def test_write_and_load_job_kg(store, tmp_path):
    kg = JobKG(
        hard_requirements=[JobRequirement(id="R1", text="Python")],
        logistics=JobLogistics(location="Berlin"),
        company=CompanyData(name="TestCo"),
    )
    refs = store.write_stage("demo", "job-1", "job_kg", kg.model_dump())
    assert "job_kg_ref" in refs

    loaded = json.loads(
        (
            tmp_path / "demo/job-1/nodes/generate_documents_v2/job_kg/current.json"
        ).read_text()
    )
    assert loaded["hard_requirements"][0]["id"] == "R1"
    assert loaded["company"]["name"] == "TestCo"


def test_write_and_load_job_delta(store, tmp_path):
    delta = JobDelta(must_highlight_skills=["Rust", "Kafka"])
    refs = store.write_stage("demo", "job-2", "job_delta", delta.model_dump())
    assert "job_delta_ref" in refs

    loaded = json.loads(
        (
            tmp_path / "demo/job-2/nodes/generate_documents_v2/job_delta/current.json"
        ).read_text()
    )
    assert "Rust" in loaded["must_highlight_skills"]


def test_load_stage_returns_none_when_missing(store):
    result = store.load_stage("demo", "missing-job", "job_kg")
    assert result is None


def test_sha256_is_stable(store, tmp_path):
    kg = JobKG(hard_requirements=[JobRequirement(id="R1", text="Go")])
    store.write_stage("demo", "job-3", "job_kg", kg.model_dump())
    path = tmp_path / "demo/job-3/nodes/generate_documents_v2/job_kg/current.json"
    h1 = store.sha256_file(path)
    h2 = store.sha256_file(path)
    assert h1 == h2
    assert h1.startswith("sha256:")
