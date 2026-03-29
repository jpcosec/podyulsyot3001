from __future__ import annotations

import json

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from src.ai.match_skill.contracts import MatchEnvelope
from src.ai.match_skill.graph import build_match_skill_graph, resume_with_review
from src.ai.match_skill.storage import MatchArtifactStore


class FakeMatchChain:
    def __init__(self, responses: list[MatchEnvelope]):
        self.responses = list(responses)
        self.calls: list[dict[str, str]] = []

    def invoke(self, payload: dict[str, str]) -> MatchEnvelope:
        self.calls.append(payload)
        if not self.responses:
            raise AssertionError("no fake responses left")
        return self.responses.pop(0)


def test_match_skill_approve_flow(tmp_path) -> None:
    chain = FakeMatchChain(
        [
            MatchEnvelope(
                matches=[
                    {
                        "requirement_id": "R1",
                        "status": "matched",
                        "score": 0.9,
                        "evidence_ids": ["P1"],
                        "evidence_quotes": ["Built Python pipelines"],
                        "reasoning": "Directly supported",
                    }
                ],
                total_score=0.9,
                decision_recommendation="proceed",
                summary_notes="Strong fit",
            )
        ]
    )
    app = build_match_skill_graph(
        match_chain=chain,
        artifact_store=MatchArtifactStore(tmp_path),
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": "approve-thread"}}
    initial_state = {
        "source": "demo",
        "job_id": "job-1",
        "requirements": [{"id": "R1", "text": "Python", "priority": "must"}],
        "profile_evidence": [{"id": "P1", "description": "Built Python pipelines"}],
    }

    paused = app.invoke(initial_state, config=config)

    assert paused["status"] == "pending_review"
    assert paused["round_number"] == 1
    review_surface = json.loads(
        tmp_path.joinpath("demo/job-1/nodes/match_skill/review/current.json").read_text(
            encoding="utf-8"
        )
    )
    assert review_surface["items"][0]["requirement_text"] == "Python"

    result = resume_with_review(
        app,
        config,
        {
            "source_state_hash": paused["match_result_hash"],
            "items": [{"requirement_id": "R1", "decision": "approve", "note": "ok"}],
        },
    )

    assert result["review_decision"] == "approve"
    assert result["status"] == "completed"


def test_match_skill_regeneration_flow(tmp_path) -> None:
    chain = FakeMatchChain(
        [
            MatchEnvelope(
                matches=[
                    {
                        "requirement_id": "R1",
                        "status": "matched",
                        "score": 0.95,
                        "evidence_ids": ["P1"],
                        "evidence_quotes": ["Python pipelines"],
                        "reasoning": "Already supported",
                    },
                    {
                        "requirement_id": "R2",
                        "status": "missing",
                        "score": 0.2,
                        "evidence_ids": [],
                        "evidence_quotes": [],
                        "reasoning": "No SQL evidence",
                    },
                ],
                total_score=0.55,
                decision_recommendation="marginal",
                summary_notes="Needs SQL support",
            ),
            MatchEnvelope(
                matches=[
                    {
                        "requirement_id": "R1",
                        "status": "matched",
                        "score": 0.95,
                        "evidence_ids": ["P1"],
                        "evidence_quotes": ["Python pipelines"],
                        "reasoning": "Already supported",
                    },
                    {
                        "requirement_id": "R2",
                        "status": "matched",
                        "score": 0.75,
                        "evidence_ids": ["PATCH-SQL"],
                        "evidence_quotes": ["SQL dashboards"],
                        "reasoning": "Patched evidence covers SQL",
                    },
                ],
                total_score=0.85,
                decision_recommendation="proceed",
                summary_notes="Now good",
            ),
        ]
    )
    app = build_match_skill_graph(
        match_chain=chain,
        artifact_store=MatchArtifactStore(tmp_path),
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": "regen-thread"}}
    initial_state = {
        "source": "demo",
        "job_id": "job-2",
        "requirements": [
            {"id": "R1", "text": "Python", "priority": "must"},
            {"id": "R2", "text": "SQL", "priority": "must"},
        ],
        "profile_evidence": [{"id": "P1", "description": "Built Python pipelines"}],
    }

    paused = app.invoke(initial_state, config=config)
    regenerated = resume_with_review(
        app,
        config,
        {
            "source_state_hash": paused["match_result_hash"],
            "items": [
                {"requirement_id": "R1", "decision": "approve"},
                {
                    "requirement_id": "R2",
                    "decision": "request_regeneration",
                    "patch_evidence": {
                        "id": "PATCH-SQL",
                        "description": "Built SQL dashboards",
                    },
                },
            ],
        },
    )

    assert regenerated["status"] == "pending_review"
    assert regenerated["round_number"] == 2
    assert regenerated["regeneration_scope"] == ["R2"]
    patched_ids = {item["id"] for item in regenerated["effective_profile_evidence"]}
    assert "PATCH-SQL" in patched_ids
    assert chain.calls[1]["regeneration_scope_block"] == "- R2"


def test_match_skill_rejects_stale_review_payload(tmp_path) -> None:
    chain = FakeMatchChain(
        [
            MatchEnvelope(
                matches=[
                    {
                        "requirement_id": "R1",
                        "status": "matched",
                        "score": 0.8,
                        "evidence_ids": ["P1"],
                        "evidence_quotes": ["Python pipelines"],
                        "reasoning": "Looks good",
                    }
                ],
                total_score=0.8,
                decision_recommendation="proceed",
                summary_notes="Good",
            )
        ]
    )
    app = build_match_skill_graph(
        match_chain=chain,
        artifact_store=MatchArtifactStore(tmp_path),
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": "stale-thread"}}
    initial_state = {
        "source": "demo",
        "job_id": "job-3",
        "requirements": [{"id": "R1", "text": "Python", "priority": "must"}],
        "profile_evidence": [{"id": "P1", "description": "Built Python pipelines"}],
    }

    app.invoke(initial_state, config=config)
    app.update_state(
        config,
        {
            "review_payload": {
                "source_state_hash": "sha256:deadbeef",
                "items": [{"requirement_id": "R1", "decision": "approve"}],
            }
        },
        as_node="human_review_node",
    )

    with pytest.raises(ValueError, match="hash"):
        app.invoke(None, config=config)


def test_match_skill_continue_without_review_payload_stays_pending_review(
    tmp_path,
) -> None:
    chain = FakeMatchChain(
        [
            MatchEnvelope(
                matches=[
                    {
                        "requirement_id": "R1",
                        "status": "matched",
                        "score": 0.8,
                        "evidence_ids": ["P1"],
                        "evidence_quotes": ["Python pipelines"],
                        "reasoning": "Looks good",
                    }
                ],
                total_score=0.8,
                decision_recommendation="proceed",
                summary_notes="Good",
            )
        ]
    )
    app = build_match_skill_graph(
        match_chain=chain,
        artifact_store=MatchArtifactStore(tmp_path),
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": "continue-without-review"}}
    initial_state = {
        "source": "demo",
        "job_id": "job-4",
        "requirements": [{"id": "R1", "text": "Python", "priority": "must"}],
        "profile_evidence": [{"id": "P1", "description": "Built Python pipelines"}],
    }

    paused = app.invoke(initial_state, config=config)
    assert paused["status"] == "pending_review"

    result = app.invoke(None, config=config)
    assert result["status"] == "pending_review"
    assert app.get_state(config).next == ("human_review_node",)
