"""Tests for the HITL patch application engine."""

from __future__ import annotations

import json
import pytest

from src.core.ai.generate_documents_v2.contracts.hitl import GraphPatch, PatchBundle
from src.core.ai.generate_documents_v2.hitl_patch_engine import (
    OUTCOME_APPROVED,
    OUTCOME_REJECTED,
    OUTCOME_REGENERATING,
    apply_patches,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def store(tmp_path):
    return PipelineArtifactStore(tmp_path)


def _base_state(**overrides) -> dict:
    state = {
        "source": "test_source",
        "job_id": "job-42",
        "matches": [{"id": "m1", "value": "original"}],
        "blueprint": {"title": "original_title", "sections": []},
        "markdown_bundle": {"cv": "# CV"},
    }
    state.update(overrides)
    return state


# ---------------------------------------------------------------------------
# approve patch
# ---------------------------------------------------------------------------


def test_approve_patch_clears_pending_and_sets_approved(store):
    patch = GraphPatch(action="approve", target_id="any")
    state = _base_state(pending_patches=[patch.model_dump()])

    result = apply_patches(
        state=state,
        stage="hitl_1_match_evidence",
        outcome_key="match_outcome",
        mutable_state_key="matches",
        store=store,
    )

    assert result["match_outcome"] == OUTCOME_APPROVED
    assert result["pending_patches"] == []
    assert result["status"] == "running"


def test_empty_patches_treated_as_approve(store):
    state = _base_state(pending_patches=[])

    result = apply_patches(
        state=state,
        stage="hitl_1_match_evidence",
        outcome_key="match_outcome",
        mutable_state_key="matches",
        store=store,
    )

    assert result["match_outcome"] == OUTCOME_APPROVED
    assert result["pending_patches"] == []


# ---------------------------------------------------------------------------
# reject patch
# ---------------------------------------------------------------------------


def test_reject_patch_sets_rejected_outcome(store):
    patch = GraphPatch(action="reject", target_id="any")
    state = _base_state(pending_patches=[patch.model_dump()])

    result = apply_patches(
        state=state,
        stage="hitl_2_blueprint_logic",
        outcome_key="blueprint_outcome",
        mutable_state_key="blueprint",
        store=store,
    )

    assert result["blueprint_outcome"] == OUTCOME_REJECTED
    assert result["status"] == "rejected"
    assert result["pending_patches"] == []


# ---------------------------------------------------------------------------
# request_regeneration patch
# ---------------------------------------------------------------------------


def test_regeneration_patch_sets_regenerating_outcome(store):
    patch = GraphPatch(action="request_regeneration", target_id="any")
    state = _base_state(pending_patches=[patch.model_dump()])

    result = apply_patches(
        state=state,
        stage="hitl_2_blueprint_logic",
        outcome_key="blueprint_outcome",
        mutable_state_key="blueprint",
        store=store,
    )

    assert result["blueprint_outcome"] == OUTCOME_REGENERATING
    assert result["pending_patches"] == []


# ---------------------------------------------------------------------------
# modify patch — dict artifact
# ---------------------------------------------------------------------------


def test_modify_patch_updates_dict_field(store):
    patch = GraphPatch(action="modify", target_id="title", new_value="patched_title")
    state = _base_state(
        blueprint={"title": "original_title", "sections": []},
        pending_patches=[patch.model_dump()],
    )

    result = apply_patches(
        state=state,
        stage="hitl_2_blueprint_logic",
        outcome_key="blueprint_outcome",
        mutable_state_key="blueprint",
        store=store,
    )

    assert result["blueprint_outcome"] == OUTCOME_APPROVED
    assert result["blueprint"]["title"] == "patched_title"
    assert result["pending_patches"] == []


def test_modify_patch_does_not_mutate_original(store):
    original_blueprint = {"title": "original", "sections": []}
    patch = GraphPatch(action="modify", target_id="title", new_value="new")
    state = _base_state(
        blueprint=original_blueprint,
        pending_patches=[patch.model_dump()],
    )

    apply_patches(
        state=state,
        stage="hitl_2_blueprint_logic",
        outcome_key="blueprint_outcome",
        mutable_state_key="blueprint",
        store=store,
    )

    assert original_blueprint["title"] == "original"


# ---------------------------------------------------------------------------
# modify patch — list artifact (matches)
# ---------------------------------------------------------------------------


def test_modify_patch_updates_matching_list_item(store):
    patch = GraphPatch(action="modify", target_id="m1", new_value="patched_value")
    state = _base_state(
        matches=[{"id": "m1", "value": "original"}, {"id": "m2", "value": "other"}],
        pending_patches=[patch.model_dump()],
    )

    result = apply_patches(
        state=state,
        stage="hitl_1_match_evidence",
        outcome_key="match_outcome",
        mutable_state_key="matches",
        store=store,
    )

    updated = result["matches"]
    assert updated[0]["value"] == "patched_value"
    assert updated[1]["value"] == "other"


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def test_apply_patches_persists_bundle_artifact(store, tmp_path):
    patch = GraphPatch(action="approve", target_id="any")
    state = _base_state(pending_patches=[patch.model_dump()])

    apply_patches(
        state=state,
        stage="hitl_1_match_evidence",
        outcome_key="match_outcome",
        mutable_state_key="matches",
        store=store,
    )

    artifact_path = (
        tmp_path
        / "test_source"
        / "job-42"
        / "nodes"
        / "generate_documents_v2"
        / "hitl_1_match_evidence"
        / "applied_patches"
        / "current.json"
    )
    assert artifact_path.exists()
    bundle = json.loads(artifact_path.read_text())
    assert bundle["stage"] == "hitl_1_match_evidence"
    assert len(bundle["patches"]) == 1


# ---------------------------------------------------------------------------
# Multiple patches — last action wins for outcome
# ---------------------------------------------------------------------------


def test_approve_then_modify_gives_approved_with_updated_artifact(store):
    patches = [
        GraphPatch(action="approve", target_id="any").model_dump(),
        GraphPatch(action="modify", target_id="title", new_value="v2").model_dump(),
    ]
    state = _base_state(
        blueprint={"title": "v1", "sections": []},
        pending_patches=patches,
    )

    result = apply_patches(
        state=state,
        stage="hitl_2_blueprint_logic",
        outcome_key="blueprint_outcome",
        mutable_state_key="blueprint",
        store=store,
    )

    assert result["blueprint_outcome"] == OUTCOME_APPROVED
    assert result["blueprint"]["title"] == "v2"
