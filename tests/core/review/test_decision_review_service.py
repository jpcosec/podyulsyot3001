from __future__ import annotations

import pytest

from src.core.tools.review_decision_service import (
    feedback_action_from_decision,
    parse_checkbox_decision,
    route_from_decision_values,
    validate_feedback_payload_for_route,
)


def test_parse_checkbox_decision_supports_single_valid_selection() -> None:
    decision, status = parse_checkbox_decision("[ ] Proceed / [x] Regen / [ ] Reject")
    assert status == "valid"
    assert decision == "request_regeneration"


def test_route_from_decision_values_prioritizes_reject_over_other_values() -> None:
    routed = route_from_decision_values(["approve", "request_regeneration", "reject"])
    assert routed == "reject"


def test_feedback_action_from_decision_maps_all_outcomes() -> None:
    assert feedback_action_from_decision("approve") == "proceed"
    assert feedback_action_from_decision("request_regeneration") == "patch"
    assert feedback_action_from_decision("reject") == "reject"


def test_validate_feedback_payload_for_route_requires_patch_for_regeneration() -> None:
    with pytest.raises(ValueError, match="patch feedback entries"):
        validate_feedback_payload_for_route(
            payload={"feedback": [{"req_id": "R1", "action": "proceed"}]},
            routing_decision="request_regeneration",
        )
