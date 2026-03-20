from __future__ import annotations

import re
from typing import Any, Literal, Mapping

DecisionValue = Literal["approve", "request_regeneration", "reject"]


def parse_checkbox_decision(
    text: str,
) -> tuple[DecisionValue | None, Literal["valid", "none", "invalid"]]:
    marks = {
        "proceed": _parse_checkbox_mark(text, "proceed"),
        "regen": _parse_checkbox_mark(text, "regen"),
        "reject": _parse_checkbox_mark(text, "reject"),
    }
    if any(mark is None for mark in marks.values()):
        return None, "invalid"

    selected = [label for label, is_selected in marks.items() if is_selected]
    if not selected:
        return None, "none"
    if len(selected) != 1:
        return None, "invalid"

    if selected[0] == "proceed":
        return "approve", "valid"
    if selected[0] == "regen":
        return "request_regeneration", "valid"
    return "reject", "valid"


def route_from_decision_values(decisions: list[str]) -> DecisionValue | None:
    if not decisions:
        return None

    if any(value == "reject" for value in decisions):
        return "reject"
    if any(value == "request_regeneration" for value in decisions):
        return "request_regeneration"
    if all(value == "approve" for value in decisions):
        return "approve"
    return None


def feedback_action_from_decision(decision: DecisionValue) -> str:
    if decision == "approve":
        return "proceed"
    if decision == "request_regeneration":
        return "patch"
    return "reject"


def validate_feedback_payload_for_route(
    payload: Mapping[str, Any],
    routing_decision: DecisionValue,
) -> None:
    feedback = payload.get("feedback")
    if not isinstance(feedback, list):
        raise ValueError("feedback payload must contain feedback list")

    if routing_decision != "request_regeneration":
        return

    if not feedback:
        raise ValueError("request_regeneration requires non-empty feedback payload")

    has_patch_action = any(
        isinstance(item, Mapping) and str(item.get("action", "")).lower() == "patch"
        for item in feedback
    )
    if not has_patch_action:
        raise ValueError("request_regeneration requires patch feedback entries")


def _parse_checkbox_mark(text: str, label: str) -> bool | None:
    pattern = rf"\[(?P<mark>[^\]]*)\]\s*{re.escape(label)}\b"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match is None:
        return None

    mark = match.group("mark").strip().lower()
    if mark == "":
        return False
    if mark == "x":
        return True
    return None
