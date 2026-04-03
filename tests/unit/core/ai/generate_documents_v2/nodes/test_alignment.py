from __future__ import annotations

import json

import pytest

from src.core.ai.generate_documents_v2.contracts.job import JobKG, JobRequirement
from src.core.ai.generate_documents_v2.contracts.matching import MatchEdge
from src.core.ai.generate_documents_v2.contracts.profile import ProfileEntry, ProfileKG
from src.core.ai.generate_documents_v2.nodes.alignment import MatchResult, run_alignment
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


PROFILE = ProfileKG(
    entries=[
        ProfileEntry(
            id="EXP001",
            role="Data Engineer",
            organization="ACME",
            keywords=["Python", "Rust"],
        )
    ],
    skills=["Python", "Rust"],
    traits=["curious"],
)

JOB = JobKG(
    job_title_english="Data Engineer",
    hard_requirements=[JobRequirement(id="R01", text="Python", priority=5)],
)


class FakeAlignmentChain:
    def __init__(self, response: MatchResult):
        self.response = response
        self.calls: list[dict] = []

    def invoke(self, payload: dict) -> MatchResult:
        self.calls.append(payload)
        return self.response


@pytest.fixture
def store(tmp_path):
    return PipelineArtifactStore(tmp_path)


def test_run_alignment_returns_matches(store):
    chain = FakeAlignmentChain(
        MatchResult(
            matches=[
                MatchEdge(
                    requirement_id="R01",
                    profile_evidence_ids=["EXP001"],
                    match_score=0.9,
                    reasoning="Strong explicit match.",
                )
            ]
        )
    )
    result = run_alignment(
        source="demo",
        job_id="job-1",
        profile_kg=PROFILE,
        job_kg=JOB,
        chain=chain,
        store=store,
    )
    assert result["status"] == "aligned"
    assert result["matches"][0]["requirement_id"] == "R01"


def test_run_alignment_writes_disk(store, tmp_path):
    chain = FakeAlignmentChain(
        MatchResult(
            matches=[
                MatchEdge(
                    requirement_id="R01",
                    profile_evidence_ids=["EXP001"],
                    match_score=0.9,
                    reasoning="Strong explicit match.",
                )
            ]
        )
    )
    run_alignment(
        source="demo",
        job_id="job-2",
        profile_kg=PROFILE,
        job_kg=JOB,
        chain=chain,
        store=store,
    )
    payload = json.loads(
        (
            tmp_path / "demo/job-2/nodes/generate_documents_v2/match_edges/current.json"
        ).read_text()
    )
    assert payload["matches"][0]["profile_evidence_ids"] == ["EXP001"]


def test_alignment_prompt_includes_profile_and_job(store):
    chain = FakeAlignmentChain(MatchResult())
    run_alignment(
        source="demo",
        job_id="job-3",
        profile_kg=PROFILE,
        job_kg=JOB,
        chain=chain,
        store=store,
    )
    user_prompt = chain.calls[0]["user"]
    assert "PROFILE SKILLS" in user_prompt
    assert "JOB HARD REQUIREMENTS" in user_prompt
