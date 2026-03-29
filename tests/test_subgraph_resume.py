"""Integration test: subgraph pause/resume via state update.

Proves that an external caller (like the Textual TUI) can:
1. Run the match_skill subgraph until it pauses at the HITL breakpoint.
2. Inject a review_payload via update_state (simulating MatchBus).
3. Resume the graph with ainvoke(None) and observe correct routing.

This is a prerequisite for wiring the TUI to the pipeline's match_skill
subgraph — see docs/superpowers/specs/2026-03-29-pipeline-unification-design.md §7.4.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from langgraph.checkpoint.memory import InMemorySaver

from src.ai.match_skill.contracts import (
    MatchEnvelope,
    RequirementMatch,
    ReviewItemDecision,
    ReviewPayload,
)
from src.ai.match_skill.graph import build_match_skill_graph


def _stub_match_chain():
    """Return a fake chain that produces a valid MatchEnvelope."""
    from langchain_core.runnables import RunnableLambda

    def _invoke(_input):
        return MatchEnvelope(
            matches=[
                RequirementMatch(
                    requirement_id="REQ_001",
                    status="matched",
                    score=0.9,
                    evidence_ids=["EV_001"],
                    evidence_quotes=["Relevant experience"],
                    reasoning="Strong match based on experience",
                ),
            ],
            total_score=0.9,
            decision_recommendation="proceed",
            summary_notes="Good overall fit",
        )

    return RunnableLambda(_invoke)


@pytest.fixture()
def match_skill_app(tmp_path):
    """Build a match_skill graph with a stub chain and in-memory checkpointer."""
    from src.ai.match_skill.storage import MatchArtifactStore

    store = MatchArtifactStore(tmp_path)
    checkpointer = InMemorySaver()
    app = build_match_skill_graph(
        match_chain=_stub_match_chain(),
        artifact_store=store,
        checkpointer=checkpointer,
        interrupt_before=("human_review_node",),
    )
    return app, store


@pytest.mark.asyncio
async def test_subgraph_pause_update_resume(match_skill_app):
    """External caller can pause, inject review payload, and resume the subgraph."""
    app, store = match_skill_app
    thread_id = "test_subgraph_resume"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "source": "test",
        "job_id": "001",
        "requirements": [
            {"id": "REQ_001", "text": "Python experience", "priority": "must"},
        ],
        "profile_evidence": [
            {"id": "EV_001", "description": "5 years Python development"},
        ],
    }

    # Step 1: Run until HITL breakpoint
    paused_state = await app.ainvoke(initial_state, config=config)

    # The graph should have paused before human_review_node
    snapshot = await app.aget_state(config)
    assert snapshot.next, "Graph should be paused with pending next nodes"
    assert "human_review_node" in snapshot.next

    # Step 2: Simulate TUI injecting a review payload (what MatchBus does)
    match_result_hash = paused_state.get("match_result_hash", "")
    if not match_result_hash:
        # Compute hash from match_result the same way the graph does
        match_result = paused_state.get("match_result", {})
        match_result_hash = hashlib.sha256(
            json.dumps(match_result, sort_keys=True).encode()
        ).hexdigest()

    review_payload = ReviewPayload(
        source_state_hash=match_result_hash,
        items=[
            ReviewItemDecision(
                requirement_id="REQ_001",
                decision="approve",
                note="Looks good",
            ),
        ],
    )

    await app.aupdate_state(
        config,
        {"review_payload": review_payload.model_dump()},
    )

    # Step 3: Resume — the graph should route through apply_review_decision
    final_state = await app.ainvoke(None, config=config)

    # Verify the graph completed (approve routes to generate_documents → __end__)
    assert final_state.get("status") in ("completed", "running"), (
        f"Expected completed or running, got: {final_state.get('status')}"
    )

    # Verify the graph is no longer paused
    final_snapshot = await app.aget_state(config)
    assert not final_snapshot.next, "Graph should have completed, not paused"
