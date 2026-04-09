"""E2E tests for the pipeline.

Verifies:
1. Pipeline graph can be built and compiled
2. Pipeline can be invoked with mock data
3. HITL pause/resume flow works (interrupt_before)
4. Full live pipeline: scrape → translate → match (auto-approve) → generate → render → package
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Any

import httpx
import pytest
from langgraph.checkpoint.memory import InMemorySaver

pytest.skip(
    "Legacy match_skill E2E suite is archived until it is migrated to generate_documents_v2.",
    allow_module_level=True,
)

from src.core.ai.match_skill.contracts import MatchEnvelope
from src.core.ai.match_skill.graph import build_match_skill_graph, resume_with_review
from src.core.ai.match_skill.storage import MatchArtifactStore


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

        # Reject should route to __end__ with rejected status
        state = app.get_state(config)
        assert state.values.get("status") == "rejected"
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


# ---------------------------------------------------------------------------
# Full pipeline e2e — requires live LangGraph server on port 8124
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent / "fixtures"
SERVER_URL = "http://localhost:8124"
PROFILE_PATH = "data/reference_data/profile/base_profile/profile_base_data.json"


def _server_available() -> bool:
    try:
        return httpx.get(f"{SERVER_URL}/ok", timeout=2).status_code == 200
    except Exception:
        return False


@pytest.fixture()
def stub_profile():
    """Install stub profile_base_data.json at the expected default path and clean up after."""
    dest = Path(PROFILE_PATH)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES / "stub_profile.json", dest)
    yield dest
    dest.unlink(missing_ok=True)


@pytest.fixture()
def fresh_job(stub_profile):
    """Scrape a fresh tuberlin job, yield (source, job_id), delete data/jobs/tuberlin after test."""
    from src.scraper.main import build_providers
    from src.core.data_manager import DataManager

    dm = DataManager()
    adapter = build_providers(dm)["tuberlin"]
    job_ids = asyncio.run(adapter.run(already_scraped=[], limit=1, drop_repeated=False))
    assert job_ids, "Scraper returned no jobs — check network or tuberlin availability"
    yield "tuberlin", job_ids[0]

    shutil.rmtree("data/jobs/tuberlin", ignore_errors=True)


@pytest.mark.e2e
@pytest.mark.skipif(
    not _server_available(), reason="LangGraph server not running on port 8124"
)
class TestFullPipelineE2E:
    """Full pipeline e2e: scrape → translate → match (auto-approve) → generate → render → package."""

    def test_scrape_produces_ingest_artifact(self, fresh_job):
        source, job_id = fresh_job
        state_file = Path(
            f"data/jobs/{source}/{job_id}/nodes/ingest/proposed/state.json"
        )
        assert state_file.exists(), f"Ingest artifact missing: {state_file}"
        data = json.loads(state_file.read_text())
        assert data.get("job_title"), "Ingest state has no job_title"
        assert data.get("original_language"), "Ingest state has no original_language"

    def test_translate_produces_artifact(self, fresh_job):
        from src.core.tools.translator.main import translate_single_job, PROVIDERS
        from src.core.data_manager import DataManager

        source, job_id = fresh_job
        dm = DataManager()
        translate_single_job(dm, PROVIDERS["google"], source, job_id)

        out = Path(f"data/jobs/{source}/{job_id}/nodes/translate/proposed/state.json")
        assert out.exists(), f"Translate artifact missing: {out}"
        data = json.loads(out.read_text())
        assert data.get("original_language") == "en", (
            "Translated state language not set to 'en'"
        )

    def test_full_pipeline_reaches_completed(self, fresh_job):
        """Full pipeline with auto-approve must reach status=completed and produce a manifest."""
        from src.core.tools.translator.main import translate_single_job, PROVIDERS
        from src.core.data_manager import DataManager
        from src.core.api_client import LangGraphAPIClient

        source, job_id = fresh_job

        dm = DataManager()
        translate_single_job(dm, PROVIDERS["google"], source, job_id)

        async def _run():
            client = LangGraphAPIClient(SERVER_URL)
            return await client.invoke_pipeline(
                source=source,
                job_id=job_id,
                initial_input={"auto_approve_review": True},
            )

        asyncio.run(_run())

        thread_id = LangGraphAPIClient.thread_id_for(source, job_id)
        r = httpx.get(f"{SERVER_URL}/threads/{thread_id}/state")
        state_values = r.json().get("values", {})
        final_status = state_values.get("status")

        assert final_status == "completed", (
            f"Pipeline did not complete. status={final_status!r}, "
            f"error_state={state_values.get('error_state')}"
        )

    def test_all_stage_artifacts_present(self, fresh_job):
        """After a completed pipeline run, every stage must have written its expected artifact."""
        from src.core.tools.translator.main import translate_single_job, PROVIDERS
        from src.core.data_manager import DataManager
        from src.core.api_client import LangGraphAPIClient

        source, job_id = fresh_job
        dm = DataManager()
        translate_single_job(dm, PROVIDERS["google"], source, job_id)

        async def _run():
            client = LangGraphAPIClient(SERVER_URL)
            return await client.invoke_pipeline(
                source=source,
                job_id=job_id,
                initial_input={"auto_approve_review": True},
            )

        asyncio.run(_run())

        base = Path(f"data/jobs/{source}/{job_id}/nodes")
        expected = {
            "ingest": base / "ingest/proposed/state.json",
            "translate": base / "translate/proposed/state.json",
            "load_profile": base / "pipeline_inputs/proposed/profile_evidence.json",
            "match_skill": base / "match_skill/approved/state.json",
        }

        missing = [name for name, path in expected.items() if not path.exists()]
        assert not missing, f"Missing artifacts after completed run: {missing}"

    def test_package_manifest_references_valid_files(self, fresh_job):
        """The final manifest must list files that actually exist on disk."""
        from src.core.tools.translator.main import translate_single_job, PROVIDERS
        from src.core.data_manager import DataManager
        from src.core.api_client import LangGraphAPIClient

        source, job_id = fresh_job
        dm = DataManager()
        translate_single_job(dm, PROVIDERS["google"], source, job_id)

        async def _run():
            client = LangGraphAPIClient(SERVER_URL)
            return await client.invoke_pipeline(
                source=source,
                job_id=job_id,
                initial_input={"auto_approve_review": True},
            )

        asyncio.run(_run())

        manifest_path = Path(
            f"data/jobs/{source}/{job_id}/nodes/package/final/manifest.json"
        )
        assert manifest_path.exists(), "manifest.json not written"

        manifest = json.loads(manifest_path.read_text())
        artifacts = manifest.get("artifacts", {})
        assert artifacts, "Manifest has no artifacts"

        missing_files = [ref for ref in artifacts.values() if not Path(ref).exists()]
        assert not missing_files, (
            f"Manifest references files that do not exist: {missing_files}"
        )
