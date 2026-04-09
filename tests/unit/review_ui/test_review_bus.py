from __future__ import annotations

import pytest

from src.review_ui.bus import _resolve_artifact_stage


def test_resolve_artifact_stage_for_match_review() -> None:
    artifact_stage, title = _resolve_artifact_stage("hitl_1_match_evidence")

    assert artifact_stage == "match_edges"
    assert title == "Match Evidence Review"


def test_resolve_artifact_stage_for_blueprint_review() -> None:
    artifact_stage, title = _resolve_artifact_stage("hitl_2_blueprint_logic")

    assert artifact_stage == "blueprint"
    assert title == "Blueprint Review"


def test_resolve_artifact_stage_for_outer_stage_review() -> None:
    artifact_stage, title = _resolve_artifact_stage("stage_2_semantic_bridge")

    assert artifact_stage == "match_edges"
    assert title == "Match Evidence Review"


def test_resolve_artifact_stage_rejects_unknown_stage() -> None:
    with pytest.raises(ValueError, match="Unsupported review stage"):
        _resolve_artifact_stage("human_review_node")
