"""Normalization of BrowserOS MCP recordings into shared promotion candidates."""

from __future__ import annotations

from typing import Any

from src.automation.motors.browseros.promotion_models import (
    BrowserOSActionCandidate,
    BrowserOSStepCandidate,
)

from .recording import BrowserOSMcpRecordedCall, BrowserOSMcpRecording


class BrowserOSMcpTraceNormalizer:
    """Convert deterministic BrowserOS MCP recordings into shared step candidates."""

    _INTENT_MAP = {
        "navigate_page": "navigate",
        "click": "click",
        "fill": "fill",
        "select_option": "select",
        "upload_file": "upload",
        "press_key": "press_key",
        "scroll": "scroll",
    }

    def normalize(
        self, recording: BrowserOSMcpRecording
    ) -> list[BrowserOSStepCandidate]:
        candidates: list[BrowserOSStepCandidate] = []
        step_index = 0
        for call in recording.calls:
            if call.tool_name == "take_snapshot":
                continue
            step_index += 1
            action = self._action_from_call(call)
            candidates.append(
                BrowserOSStepCandidate(
                    step_index=step_index,
                    source="level1",
                    actions=[action],
                    requires_review=action.requires_review,
                    review_reason=action.review_reason,
                )
            )
        return candidates

    def _action_from_call(
        self, call: BrowserOSMcpRecordedCall
    ) -> BrowserOSActionCandidate:
        intent = self._INTENT_MAP.get(call.tool_name)
        requires_review = intent is None or isinstance(
            call.arguments.get("element"), int
        )
        review_reason = None
        if intent is None:
            review_reason = f"unsupported BrowserOS tool: {call.tool_name}"
        elif isinstance(call.arguments.get("element"), int):
            review_reason = "tool input relies on snapshot-local element id"
        if call.error:
            requires_review = True
            review_reason = self._merge_reasons(review_reason, call.error)
        return BrowserOSActionCandidate(
            source="level1",
            origin=call.tool_name,
            candidate_intent=intent,
            target_hint=self._target_hint(call.tool_name, call.arguments),
            value_hint=self._value_hint(call.tool_name, call.arguments),
            requires_review=requires_review,
            review_reason=review_reason,
            evidence=[{"request_id": call.request_id, "arguments": call.arguments}],
        )

    def _target_hint(self, tool_name: str, arguments: dict[str, Any]) -> str | None:
        if tool_name == "navigate_page":
            url = arguments.get("url")
            return str(url) if url else None
        for key in ("selector", "text", "elementText", "name"):
            value = arguments.get(key)
            if isinstance(value, str) and value:
                return value
        return None

    def _value_hint(self, tool_name: str, arguments: dict[str, Any]) -> str | None:
        if tool_name == "fill":
            value = arguments.get("text") or arguments.get("value")
            return str(value) if value is not None else None
        if tool_name == "select_option":
            value = arguments.get("value") or arguments.get("label")
            return str(value) if value is not None else None
        if tool_name == "press_key":
            value = arguments.get("key")
            return str(value) if value is not None else None
        return None

    def _merge_reasons(self, left: str | None, right: str) -> str:
        if not left:
            return right
        if right in left:
            return left
        return f"{left}; {right}"
