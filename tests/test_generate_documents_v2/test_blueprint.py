from __future__ import annotations

import json

import pytest

from src.core.ai.generate_documents_v2.contracts.blueprint import (
    GlobalBlueprint,
    SectionBlueprint,
)
from src.core.ai.generate_documents_v2.contracts.job import JobDelta
from src.core.ai.generate_documents_v2.contracts.matching import MatchEdge
from src.core.ai.generate_documents_v2.contracts.profile import SectionMappingItem
from src.core.ai.generate_documents_v2.nodes.blueprint import run_blueprint
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


MAPPING = [SectionMappingItem(section_id="summary", target_document="cv")]
DELTA = JobDelta(must_highlight_skills=["Python"])
MATCHES = [
    MatchEdge(
        requirement_id="R01",
        profile_evidence_ids=["EXP001"],
        match_score=0.9,
        reasoning="Strong explicit match.",
    )
]


class FakeBlueprintChain:
    def __init__(self, response: GlobalBlueprint):
        self.response = response
        self.calls: list[dict] = []

    def invoke(self, payload: dict) -> GlobalBlueprint:
        self.calls.append(payload)
        return self.response


@pytest.fixture
def store(tmp_path):
    return PipelineArtifactStore(tmp_path)


def test_run_blueprint_returns_blueprint(store):
    chain = FakeBlueprintChain(
        GlobalBlueprint(
            application_id="APP1",
            strategy_type="professional",
            sections=[
                SectionBlueprint(
                    section_id="summary",
                    logical_train_of_thought=["EXP001"],
                    section_intent="Lead with fit.",
                )
            ],
        )
    )
    result = run_blueprint(
        source="demo",
        job_id="job-1",
        application_id="APP1",
        strategy_type="professional",
        section_mapping=MAPPING,
        job_delta=DELTA,
        matches=MATCHES,
        chain=chain,
        store=store,
    )
    assert result["status"] == "blueprinted"
    assert result["blueprint"]["sections"][0]["section_id"] == "summary"


def test_run_blueprint_writes_disk(store, tmp_path):
    chain = FakeBlueprintChain(
        GlobalBlueprint(
            application_id="APP1",
            strategy_type="professional",
            sections=[
                SectionBlueprint(
                    section_id="summary",
                    logical_train_of_thought=["EXP001"],
                    section_intent="Lead with fit.",
                )
            ],
        )
    )
    run_blueprint(
        source="demo",
        job_id="job-2",
        application_id="APP1",
        strategy_type="professional",
        section_mapping=MAPPING,
        job_delta=DELTA,
        matches=MATCHES,
        chain=chain,
        store=store,
    )
    payload = json.loads(
        (
            tmp_path / "demo/job-2/nodes/generate_documents_v2/blueprint/current.json"
        ).read_text()
    )
    assert payload["strategy_type"] == "professional"


def test_blueprint_prompt_includes_mapping_and_delta(store):
    chain = FakeBlueprintChain(
        GlobalBlueprint(
            application_id="APP1", strategy_type="professional", sections=[]
        )
    )
    run_blueprint(
        source="demo",
        job_id="job-3",
        application_id="APP1",
        strategy_type="professional",
        section_mapping=MAPPING,
        job_delta=DELTA,
        matches=MATCHES,
        chain=chain,
        store=store,
    )
    user_prompt = chain.calls[0]["user"]
    assert "SECTION MAPPING" in user_prompt
    assert "JOB DELTA" in user_prompt
