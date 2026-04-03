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
from src.core.ai.generate_documents_v2.nodes.requirement_filter import (
    run_requirement_filter,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


SAMPLE_JOB_KG = JobKG(
    hard_requirements=[
        JobRequirement(id="R01", text="Rust 1.7+", priority=5),
        JobRequirement(id="R02", text="Python 3.10+", priority=4),
        JobRequirement(id="R03", text="Nice to have: Haskell", priority=1),
    ],
    soft_context=[
        JobRequirement(
            id="S01", text="Passion for rail transport", category="soft", priority=3
        ),
    ],
    logistics=JobLogistics(location="Munich", relocation=True),
    company=CompanyData(name="Deutsche Bahn"),
)

FAKE_DELTA = JobDelta(
    must_highlight_skills=["Rust", "Python"],
    ignored_requirements=["Nice to have: Haskell"],
    soft_vibe_requirements=["Passion for rail transport"],
    logistics_flags={"relocation_relevant": True},
)


class FakeFilterChain:
    def __init__(self, response: JobDelta):
        self._response = response
        self.calls: list[dict] = []

    def invoke(self, payload: dict) -> JobDelta:
        self.calls.append(payload)
        return self._response


@pytest.fixture
def store(tmp_path):
    return PipelineArtifactStore(tmp_path)


def test_run_filter_returns_job_delta(store):
    chain = FakeFilterChain(FAKE_DELTA)
    result = run_requirement_filter(
        source="demo",
        job_id="job-1",
        job_kg=SAMPLE_JOB_KG,
        chain=chain,
        store=store,
    )
    assert "job_delta" in result
    delta = JobDelta.model_validate(result["job_delta"])
    assert "Rust" in delta.must_highlight_skills
    assert "Nice to have: Haskell" in delta.ignored_requirements


def test_run_filter_writes_to_disk(store, tmp_path):
    chain = FakeFilterChain(FAKE_DELTA)
    run_requirement_filter(
        source="demo",
        job_id="job-2",
        job_kg=SAMPLE_JOB_KG,
        chain=chain,
        store=store,
    )
    stored = json.loads(
        (
            tmp_path / "demo/job-2/nodes/generate_documents_v2/job_delta/current.json"
        ).read_text()
    )
    assert "Rust" in stored["must_highlight_skills"]


def test_run_filter_calls_chain_once(store):
    chain = FakeFilterChain(FAKE_DELTA)
    run_requirement_filter(
        source="demo",
        job_id="job-3",
        job_kg=SAMPLE_JOB_KG,
        chain=chain,
        store=store,
    )
    assert len(chain.calls) == 1


def test_run_filter_sets_status(store):
    chain = FakeFilterChain(FAKE_DELTA)
    result = run_requirement_filter(
        source="demo",
        job_id="job-4",
        job_kg=SAMPLE_JOB_KG,
        chain=chain,
        store=store,
    )
    assert result.get("status") == "requirements_filtered"


def test_run_filter_prompt_includes_kg_data(store):
    chain = FakeFilterChain(FAKE_DELTA)
    run_requirement_filter(
        source="demo",
        job_id="job-5",
        job_kg=SAMPLE_JOB_KG,
        chain=chain,
        store=store,
    )
    user_prompt = chain.calls[0]["user"]
    assert "Rust" in user_prompt
    assert "Munich" in user_prompt
