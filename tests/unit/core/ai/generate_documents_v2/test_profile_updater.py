"""Tests for the profile updater node and the _apply_dot_path helper."""

from __future__ import annotations

import json

import pytest

from src.core.ai.generate_documents_v2.hitl_patch_engine import (
    _apply_dot_path,
    apply_patches,
)
from src.core.ai.generate_documents_v2.contracts.hitl import (
    GraphPatch,
    ProfileUpdateRecord,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


# ---------------------------------------------------------------------------
# _apply_dot_path
# ---------------------------------------------------------------------------


def test_apply_dot_path_top_level_key():
    result = _apply_dot_path({"a": 1}, "b", 2)
    assert result == {"a": 1, "b": 2}


def test_apply_dot_path_top_level_overwrites():
    result = _apply_dot_path({"a": 1}, "a", 99)
    assert result["a"] == 99


def test_apply_dot_path_nested_creates_intermediate_dicts():
    result = _apply_dot_path({}, "skills.languages", ["en", "de"])
    assert result == {"skills": {"languages": ["en", "de"]}}


def test_apply_dot_path_nested_preserves_siblings():
    obj = {"skills": {"technical": ["Python"]}}
    result = _apply_dot_path(obj, "skills.languages", ["en"])
    assert result["skills"]["technical"] == ["Python"]
    assert result["skills"]["languages"] == ["en"]


def test_apply_dot_path_does_not_mutate_original():
    obj = {"a": {"b": 1}}
    _apply_dot_path(obj, "a.b", 2)
    assert obj["a"]["b"] == 1


def test_apply_dot_path_deep_nesting():
    result = _apply_dot_path({}, "a.b.c", "leaf")
    assert result["a"]["b"]["c"] == "leaf"


def test_apply_dot_path_replaces_non_dict_intermediate():
    """When an intermediate key holds a non-dict value it is replaced by a dict."""
    obj = {"a": "not_a_dict"}
    result = _apply_dot_path(obj, "a.b", 42)
    assert result["a"]["b"] == 42


# ---------------------------------------------------------------------------
# profile_updater node — no updates
# ---------------------------------------------------------------------------


def _make_profile_updater():
    from src.core.ai.generate_documents_v2.graph import _make_profile_updater_node
    return _make_profile_updater_node()


def test_profile_updater_no_updates_returns_empty_list():
    node = _make_profile_updater()
    state = {
        "source": "test",
        "job_id": "j1",
        "approved_profile_updates": [],
    }
    result = node(state)
    assert result["approved_profile_updates"] == []
    assert result["status"] == "completed"


def test_profile_updater_no_profile_path_skips_write(tmp_path):
    node = _make_profile_updater()
    record = ProfileUpdateRecord(
        field_path="skills.languages",
        old_value=None,
        new_value=["en"],
        source_stage="hitl_1_match_evidence",
        approved=True,
    )
    state = {
        "source": "test",
        "job_id": "j1",
        "approved_profile_updates": [record.model_dump()],
        # no profile_path key
    }
    result = node(state)
    assert result["approved_profile_updates"] == []
    assert result["status"] == "completed"


# ---------------------------------------------------------------------------
# profile_updater node — with updates
# ---------------------------------------------------------------------------


def test_profile_updater_writes_to_disk_and_clears_list(tmp_path, monkeypatch):
    profile_file = tmp_path / "profile.json"
    profile_file.write_text(json.dumps({"skills": {"technical": ["Python"]}}), encoding="utf-8")

    # Patch PipelineArtifactStore so it writes inside tmp_path
    import src.core.ai.generate_documents_v2.graph as graph_mod
    monkeypatch.setattr(
        graph_mod,
        "PipelineArtifactStore",
        lambda: PipelineArtifactStore(tmp_path),
    )

    node = _make_profile_updater()
    record = ProfileUpdateRecord(
        field_path="skills.languages",
        old_value=None,
        new_value=["en", "de"],
        source_stage="hitl_1_match_evidence",
        approved=True,
    )
    state = {
        "source": "test",
        "job_id": "j1",
        "profile_path": str(profile_file),
        "approved_profile_updates": [record.model_dump()],
    }
    result = node(state)

    assert result["approved_profile_updates"] == []
    assert result["status"] == "completed"

    written = json.loads(profile_file.read_text(encoding="utf-8"))
    assert written["skills"]["languages"] == ["en", "de"]
    assert written["skills"]["technical"] == ["Python"]


def test_profile_updater_persists_audit_artifact(tmp_path, monkeypatch):
    profile_file = tmp_path / "profile.json"
    profile_file.write_text(json.dumps({}), encoding="utf-8")

    import src.core.ai.generate_documents_v2.graph as graph_mod
    monkeypatch.setattr(
        graph_mod,
        "PipelineArtifactStore",
        lambda: PipelineArtifactStore(tmp_path),
    )

    node = _make_profile_updater()
    record = ProfileUpdateRecord(
        field_path="name",
        old_value=None,
        new_value="Alice",
        source_stage="hitl_2_blueprint_logic",
        approved=True,
    )
    state = {
        "source": "test",
        "job_id": "j1",
        "profile_path": str(profile_file),
        "approved_profile_updates": [record.model_dump()],
    }
    node(state)

    artifact_path = (
        tmp_path
        / "test"
        / "j1"
        / "nodes"
        / "generate_documents_v2"
        / "profile_updater"
        / "current.json"
    )
    assert artifact_path.exists()
    artifact = json.loads(artifact_path.read_text())
    assert len(artifact["updates"]) == 1
    assert artifact["updates"][0]["field_path"] == "name"


# ---------------------------------------------------------------------------
# apply_patches — persist_to_profile flag accumulates ProfileUpdateRecord
# ---------------------------------------------------------------------------


@pytest.fixture
def store(tmp_path):
    return PipelineArtifactStore(tmp_path)


def test_persist_to_profile_patch_adds_approved_update(store):
    patch = GraphPatch(
        action="modify",
        target_id="skills.languages",
        new_value=["en"],
        persist_to_profile=True,
    )
    state = {
        "source": "test",
        "job_id": "j1",
        "blueprint": {"title": "t"},
        "pending_patches": [patch.model_dump()],
    }
    result = apply_patches(
        state=state,
        stage="hitl_2_blueprint_logic",
        outcome_key="blueprint_outcome",
        mutable_state_key="blueprint",
        store=store,
    )
    updates = result.get("approved_profile_updates", [])
    assert len(updates) == 1
    assert updates[0]["field_path"] == "skills.languages"
    assert updates[0]["new_value"] == ["en"]
    assert updates[0]["approved"] is True
    assert updates[0]["source_stage"] == "hitl_2_blueprint_logic"


def test_non_persist_patch_does_not_add_update(store):
    patch = GraphPatch(action="modify", target_id="title", new_value="new", persist_to_profile=False)
    state = {
        "source": "test",
        "job_id": "j1",
        "blueprint": {"title": "old"},
        "pending_patches": [patch.model_dump()],
    }
    result = apply_patches(
        state=state,
        stage="hitl_2_blueprint_logic",
        outcome_key="blueprint_outcome",
        mutable_state_key="blueprint",
        store=store,
    )
    assert result.get("approved_profile_updates", []) == []


def test_persist_to_profile_accumulates_across_patches(store):
    patches = [
        GraphPatch(action="modify", target_id="skills.a", new_value="x", persist_to_profile=True).model_dump(),
        GraphPatch(action="modify", target_id="skills.b", new_value="y", persist_to_profile=True).model_dump(),
    ]
    state = {
        "source": "test",
        "job_id": "j1",
        "blueprint": {},
        "pending_patches": patches,
    }
    result = apply_patches(
        state=state,
        stage="hitl_2_blueprint_logic",
        outcome_key="blueprint_outcome",
        mutable_state_key="blueprint",
        store=store,
    )
    assert len(result["approved_profile_updates"]) == 2


def test_persist_to_profile_appends_to_existing_state_updates(store):
    existing = ProfileUpdateRecord(
        field_path="traits.0",
        old_value=None,
        new_value="resilient",
        source_stage="hitl_1_match_evidence",
        approved=True,
    )
    patch = GraphPatch(
        action="modify",
        target_id="name",
        new_value="Bob",
        persist_to_profile=True,
    )
    state = {
        "source": "test",
        "job_id": "j1",
        "blueprint": {},
        "pending_patches": [patch.model_dump()],
        "approved_profile_updates": [existing.model_dump()],
    }
    result = apply_patches(
        state=state,
        stage="hitl_2_blueprint_logic",
        outcome_key="blueprint_outcome",
        mutable_state_key="blueprint",
        store=store,
    )
    assert len(result["approved_profile_updates"]) == 2
