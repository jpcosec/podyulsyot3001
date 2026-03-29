"""E2E tests for the pipeline.

Verifies:
1. Pipeline graph can be built and compiled
2. Pipeline can be invoked with mock data
3. HITL pause/resume flow works (interrupt_before)
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from src.ai.match_skill.contracts import MatchEnvelope
from src.ai.match_skill.graph import build_match_skill_graph, resume_with_review
from src.ai.match_skill.storage import MatchArtifactStore


class MockMatchChain:
    """Mock chain that returns deterministic match results."""

    def __init__(self, response: MatchEnvelope | None = None):
        self.response = response or MatchEnvelope(
            matches=[
                {
                    "requirement_id": "R1",
                    "status": "matched",
                    "score": 0.85,
                    "evidence_ids": ["P1"],
                    "evidence_quotes": ["Python experience"],
                    "reasoning": "Directly supported by profile",
                }
            ],
            total_score=0.85,
            decision_recommendation="proceed",
            summary_notes="Strong match",
        )
        self.invoked = False

    def invoke(self, payload: dict[str, Any]) -> MatchEnvelope:
        self.invoked = True
        return self.response


class MockGenChain:
    """Mock document generation chain."""

    def __init__(self):
        self.invoked = False

    def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.invoked = True
        return {"documents": {"cv": "generated", "letter": "generated"}}


# TODO(future): lock the cross-module fixture convention around tmp_path integration artifacts vs injected stores — see future_docs/issues/pipeline_unification_followups.md
class TestPipelineBuild:
    """Tests for pipeline building and compilation."""

    def test_graph_builds_successfully(self, tmp_path):
        """Verify the match skill graph can be built without errors."""
        app = build_match_skill_graph(
            match_chain=MockMatchChain(),
            gen_chain=MockGenChain(),
            artifact_store=MatchArtifactStore(tmp_path),
            checkpointer=InMemorySaver(),
        )
        assert app is not None
        assert hasattr(app, "invoke")
        assert hasattr(app, "update_state")

    def test_graph_with_interrupt_before_compiles(self, tmp_path):
        """Verify graph compiles with interrupt_before breakpoint."""
        app = build_match_skill_graph(
            match_chain=MockMatchChain(),
            checkpointer=InMemorySaver(),
            interrupt_before=("human_review_node",),
        )
        assert app is not None


class TestPipelineInvocation:
    """Tests for pipeline invocation with mock data."""

    def test_pipeline_invokes_with_mock_data(self, tmp_path):
        """Verify pipeline can be invoked with valid mock input data."""
        mock_chain = MockMatchChain()
        app = build_match_skill_graph(
            match_chain=mock_chain,
            artifact_store=MatchArtifactStore(tmp_path),
            checkpointer=InMemorySaver(),
        )
        config = {"configurable": {"thread_id": "invoke-test"}}
        initial_state = {
            "source": "test_source",
            "job_id": "job-123",
            "requirements": [
                {"id": "R1", "text": "Python programming", "priority": "must"},
                {"id": "R2", "text": "Machine learning", "priority": "nice"},
            ],
            "profile_evidence": [
                {"id": "P1", "description": "5 years Python development"},
                {"id": "P2", "description": "ML projects experience"},
            ],
        }

        result = app.invoke(initial_state, config=config)

        assert result is not None
        assert mock_chain.invoked is True
        assert "match_result" in result

    def test_pipeline_initial_state_validates(self, tmp_path):
        """Verify initial state is validated properly."""
        app = build_match_skill_graph(
            match_chain=MockMatchChain(),
            artifact_store=MatchArtifactStore(tmp_path),
            checkpointer=InMemorySaver(),
        )
        config = {"configurable": {"thread_id": "validation-test"}}

        with pytest.raises(ValueError, match="source is required"):
            app.invoke({}, config=config)

        with pytest.raises(ValueError, match="job_id is required"):
            app.invoke({"source": "test"}, config=config)


class TestHITLPauseResume:
    """Tests for HITL pause/resume flow."""

    def test_interrupt_before_pauses_at_match_skill(self, tmp_path):
        """Verify interrupt_before causes pause at human_review_node."""
        mock_chain = MockMatchChain()
        app = build_match_skill_graph(
            match_chain=mock_chain,
            artifact_store=MatchArtifactStore(tmp_path),
            checkpointer=InMemorySaver(),
            interrupt_before=("human_review_node",),
        )
        config = {"configurable": {"thread_id": "pause-test"}}
        initial_state = {
            "source": "pause_source",
            "job_id": "job-pause-1",
            "requirements": [{"id": "R1", "text": "Python", "priority": "must"}],
            "profile_evidence": [{"id": "P1", "description": "Python dev"}],
        }

        paused_result = app.invoke(initial_state, config=config)

        assert paused_result["status"] == "pending_review"
        assert "match_result_hash" in paused_result

        state = app.get_state(config)
        assert state.next == ("human_review_node",)

    def test_resume_with_approve_sets_correct_state(self, tmp_path):
        """Verify resuming with approve decision sets correct state after review."""
        mock_chain = MockMatchChain()
        app = build_match_skill_graph(
            match_chain=mock_chain,
            artifact_store=MatchArtifactStore(tmp_path),
            checkpointer=InMemorySaver(),
            interrupt_before=("human_review_node",),
        )
        config = {"configurable": {"thread_id": "resume-test"}}
        initial_state = {
            "source": "resume_source",
            "job_id": "job-resume-1",
            "requirements": [{"id": "R1", "text": "Python", "priority": "must"}],
            "profile_evidence": [{"id": "P1", "description": "Python developer"}],
        }

        paused = app.invoke(initial_state, config=config)
        assert paused["status"] == "pending_review"

        app.update_state(
            config,
            {
                "review_payload": {
                    "source_state_hash": paused["match_result_hash"],
                    "items": [
                        {"requirement_id": "R1", "decision": "approve", "note": "LGTM"}
                    ],
                }
            },
            as_node="human_review_node",
        )

        state = app.get_state(config)
        assert state.next == ("apply_review_decision",)
        assert state.values["status"] == "pending_review"

    def test_resume_with_regeneration_loops_back(self, tmp_path):
        """Verify request_regeneration loops back to match node."""
        mock_chain = MockMatchChain(
            MatchEnvelope(
                matches=[
                    {
                        "requirement_id": "R1",
                        "status": "matched",
                        "score": 0.9,
                        "evidence_ids": ["P1"],
                        "evidence_quotes": ["Python"],
                        "reasoning": "OK",
                    },
                    {
                        "requirement_id": "R2",
                        "status": "missing",
                        "score": 0.1,
                        "evidence_ids": [],
                        "evidence_quotes": [],
                        "reasoning": "Missing",
                    },
                ],
                total_score=0.5,
                decision_recommendation="marginal",
                summary_notes="Need more",
            )
        )
        app = build_match_skill_graph(
            match_chain=mock_chain,
            artifact_store=MatchArtifactStore(tmp_path),
            checkpointer=InMemorySaver(),
            interrupt_before=("human_review_node",),
        )
        config = {"configurable": {"thread_id": "regen-loop-test"}}
        initial_state = {
            "source": "regen_source",
            "job_id": "job-regen-1",
            "requirements": [
                {"id": "R1", "text": "Python", "priority": "must"},
                {"id": "R2", "text": "SQL", "priority": "must"},
            ],
            "profile_evidence": [{"id": "P1", "description": "Python dev"}],
        }

        paused = app.invoke(initial_state, config=config)
        assert paused["status"] == "pending_review"

        result = resume_with_review(
            app,
            config,
            {
                "source_state_hash": paused["match_result_hash"],
                "items": [
                    {"requirement_id": "R1", "decision": "approve"},
                    {
                        "requirement_id": "R2",
                        "decision": "request_regeneration",
                        "patch_evidence": {"id": "P2", "description": "SQL experience"},
                    },
                ],
            },
        )

        assert result["status"] == "pending_review"
        assert result["round_number"] == 2
        assert "regeneration_scope" in result


class TestResumeDecisions:
    """Tests for different resume decision paths."""

    def test_resume_with_reject_ends_cleanly(self, tmp_path):
        """Verify reject decision ends the graph."""
        mock_chain = MockMatchChain()
        app = build_match_skill_graph(
            match_chain=mock_chain,
            artifact_store=MatchArtifactStore(tmp_path),
            checkpointer=InMemorySaver(),
            interrupt_before=("human_review_node",),
        )
        config = {"configurable": {"thread_id": "reject-test"}}
        initial_state = {
            "source": "reject_source",
            "job_id": "job-reject-1",
            "requirements": [{"id": "R1", "text": "Python", "priority": "must"}],
            "profile_evidence": [{"id": "P1", "description": "Python developer"}],
        }

        paused = app.invoke(initial_state, config=config)
        assert paused["status"] == "pending_review"

        result = resume_with_review(
            app,
            config,
            {
                "source_state_hash": paused["match_result_hash"],
                "items": [
                    {
                        "requirement_id": "R1",
                        "decision": "reject",
                        "note": "Not suitable",
                    }
                ],
            },
        )

        # Reject should route to __end__ with completed status
        state = app.get_state(config)
        assert state.values.get("status") == "completed"
        assert state.values.get("review_decision") == "reject"

    def test_resume_with_stale_hash_rejected(self, tmp_path):
        """Verify stale hash is rejected."""
        mock_chain = MockMatchChain()
        app = build_match_skill_graph(
            match_chain=mock_chain,
            artifact_store=MatchArtifactStore(tmp_path),
            checkpointer=InMemorySaver(),
            interrupt_before=("human_review_node",),
        )
        config = {"configurable": {"thread_id": "stale-hash-test"}}
        initial_state = {
            "source": "stale_source",
            "job_id": "job-stale-1",
            "requirements": [{"id": "R1", "text": "Python", "priority": "must"}],
            "profile_evidence": [{"id": "P1", "description": "Python developer"}],
        }

        paused = app.invoke(initial_state, config=config)
        assert paused["status"] == "pending_review"

        # Try to resume with a stale/invalid hash
        with pytest.raises(ValueError, match="hash does not match"):
            resume_with_review(
                app,
                config,
                {
                    "source_state_hash": "stale_invalid_hash_12345",
                    "items": [
                        {"requirement_id": "R1", "decision": "approve", "note": "LGTM"}
                    ],
                },
            )

    def test_resume_bare_continue_returns_to_pending(self, tmp_path):
        """Verify bare resume returns to pending state."""
        mock_chain = MockMatchChain()
        app = build_match_skill_graph(
            match_chain=mock_chain,
            artifact_store=MatchArtifactStore(tmp_path),
            checkpointer=InMemorySaver(),
            interrupt_before=("human_review_node",),
        )
        config = {"configurable": {"thread_id": "bare-continue-test"}}
        initial_state = {
            "source": "bare_source",
            "job_id": "job-bare-1",
            "requirements": [{"id": "R1", "text": "Python", "priority": "must"}],
            "profile_evidence": [{"id": "P1", "description": "Python developer"}],
        }

        paused = app.invoke(initial_state, config=config)
        assert paused["status"] == "pending_review"

        # Resume without any review payload (bare continue)
        app.update_state(
            config,
            {},
            as_node="human_review_node",
        )
        result = app.invoke(None, config=config)

        # Should route back to human_review_node with pending status
        state = app.get_state(config)
        assert state.next == ("human_review_node",)
        assert state.values.get("status") == "pending_review"


class TestArtifactPersistence:
    """Tests for artifact persistence during pipeline execution."""

    def test_review_surface_written_to_disk(self, tmp_path):
        """Verify review surface is persisted to disk on pause."""
        mock_chain = MockMatchChain()
        store = MatchArtifactStore(tmp_path)
        app = build_match_skill_graph(
            match_chain=mock_chain,
            artifact_store=store,
            checkpointer=InMemorySaver(),
            interrupt_before=("human_review_node",),
        )
        config = {"configurable": {"thread_id": "artifact-test"}}
        initial_state = {
            "source": "artifact_source",
            "job_id": "job-artifact-1",
            "requirements": [{"id": "R1", "text": "Python", "priority": "must"}],
            "profile_evidence": [{"id": "P1", "description": "Python developer"}],
        }

        app.invoke(initial_state, config=config)

        review_file = (
            tmp_path
            / "artifact_source/job-artifact-1/nodes/match_skill/review/current.json"
        )
        assert review_file.exists()

        review_data = json.loads(review_file.read_text(encoding="utf-8"))
        assert "items" in review_data
        assert len(review_data["items"]) > 0
