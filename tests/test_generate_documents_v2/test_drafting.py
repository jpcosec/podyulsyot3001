from __future__ import annotations

import json

import pytest

from src.core.ai.generate_documents_v2.contracts.blueprint import (
    GlobalBlueprint,
    SectionBlueprint,
)
from src.core.ai.generate_documents_v2.contracts.drafting import DraftedDocument
from src.core.ai.generate_documents_v2.nodes.drafting import run_drafting
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


BLUEPRINT = GlobalBlueprint(
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


class FakeDraftingChain:
    def __init__(self, response: DraftedDocument):
        self.response = response
        self.calls: list[dict] = []

    def invoke(self, payload: dict) -> DraftedDocument:
        self.calls.append(payload)
        return self.response


@pytest.fixture
def store(tmp_path):
    return PipelineArtifactStore(tmp_path)


def test_run_drafting_returns_document(store):
    chain = FakeDraftingChain(
        DraftedDocument(doc_type="cv", sections_md={"summary": "Strong fit."})
    )
    result = run_drafting(
        source="demo",
        job_id="job-1",
        doc_type="cv",
        blueprint=BLUEPRINT,
        chain=chain,
        store=store,
    )
    assert result["status"] == "drafted_cv"
    assert result["drafted_document"]["sections_md"]["summary"] == "Strong fit."


def test_run_drafting_writes_disk(store, tmp_path):
    chain = FakeDraftingChain(
        DraftedDocument(doc_type="letter", sections_md={"intro": "Hello."})
    )
    run_drafting(
        source="demo",
        job_id="job-2",
        doc_type="letter",
        blueprint=BLUEPRINT,
        chain=chain,
        store=store,
    )
    payload = json.loads(
        (
            tmp_path
            / "demo/job-2/nodes/generate_documents_v2/draft_letter/current.json"
        ).read_text()
    )
    assert payload["doc_type"] == "letter"


def test_drafting_prompt_includes_blueprint(store):
    chain = FakeDraftingChain(
        DraftedDocument(doc_type="email", sections_md={"body": "Hi"})
    )
    run_drafting(
        source="demo",
        job_id="job-3",
        doc_type="email",
        blueprint=BLUEPRINT,
        chain=chain,
        store=store,
    )
    assert "BLUEPRINT" in chain.calls[0]["user"]
