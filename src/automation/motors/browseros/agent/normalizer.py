"""Normalization helpers for BrowserOS Level 2 traces."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .models import BrowserOSLevel2Trace, BrowserOSLevel2StreamEvent
from src.automation.motors.browseros.promotion_models import (
    BrowserOSActionCandidate,
    BrowserOSStepCandidate,
)


class BrowserOSLevel2StepCandidate(BaseModel):
    """Intermediate Ariadne candidate derived from BrowserOS Level 2 traces."""

    step_index: int
    tool_name: str
    candidate_intent: str | None = None
    target_hint: str | None = None
    value_hint: str | None = None
    requires_review: bool = False
    review_reason: str | None = None
    tool_events: list[BrowserOSLevel2StreamEvent] = Field(default_factory=list)

    def to_shared_step(self) -> BrowserOSStepCandidate:
        action = BrowserOSActionCandidate(
            source="level2",
            origin=self.tool_name,
            candidate_intent=self.candidate_intent,
            target_hint=self.target_hint,
            value_hint=self.value_hint,
            requires_review=self.requires_review,
            review_reason=self.review_reason,
            evidence=[event.model_dump(mode="json") for event in self.tool_events],
        )
        return BrowserOSStepCandidate(
            step_index=self.step_index,
            source="level2",
            actions=[action],
            requires_review=self.requires_review,
            review_reason=self.review_reason,
        )


class BrowserOSLevel2TraceNormalizer:
    """Convert BrowserOS `/chat` tool events into step candidates."""

    _IGNORED_TOOLS = {
        "browseros_info",
        "get_active_page",
        "list_pages",
        "take_snapshot",
        "take_enhanced_snapshot",
        "get_dom",
        "get_page_content",
    }

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
        self, trace: BrowserOSLevel2Trace
    ) -> list[BrowserOSLevel2StepCandidate]:
        grouped: dict[str, list[BrowserOSLevel2StreamEvent]] = {}
        ordered_tool_call_ids: list[str] = []
        for event in trace.stream_events:
            payload = event.payload
            tool_call_id = payload.get("toolCallId")
            if not isinstance(tool_call_id, str):
                continue
            if tool_call_id not in grouped:
                ordered_tool_call_ids.append(tool_call_id)
            grouped.setdefault(tool_call_id, []).append(event)

        candidates: list[BrowserOSLevel2StepCandidate] = []
        for index, tool_call_id in enumerate(ordered_tool_call_ids, start=1):
            events = grouped[tool_call_id]
            first_payload = events[0].payload
            tool_name = str(first_payload.get("toolName") or "unknown")
            if tool_name in self._IGNORED_TOOLS:
                continue
            input_payload = self._input_payload(events)
            candidate = BrowserOSLevel2StepCandidate(
                step_index=index,
                tool_name=tool_name,
                candidate_intent=self._INTENT_MAP.get(tool_name),
                target_hint=self._target_hint(tool_name, input_payload),
                value_hint=self._value_hint(tool_name, input_payload),
                tool_events=events,
            )
            if candidate.candidate_intent is None:
                candidate.requires_review = True
                candidate.review_reason = f"unsupported BrowserOS tool: {tool_name}"
            elif self._contains_unstable_element_id(input_payload):
                candidate.requires_review = True
                candidate.review_reason = (
                    "tool input relies on snapshot-local element id"
                )
            if self._tool_error(events):
                candidate.requires_review = True
                candidate.review_reason = self._merge_reasons(
                    candidate.review_reason,
                    "tool output reported an error",
                )
            candidates.append(candidate)
        return candidates

    def normalize_shared(
        self, trace: BrowserOSLevel2Trace
    ) -> list[BrowserOSStepCandidate]:
        return [candidate.to_shared_step() for candidate in self.normalize(trace)]

    def _input_payload(
        self, events: list[BrowserOSLevel2StreamEvent]
    ) -> dict[str, Any]:
        for event in events:
            payload = event.payload
            input_payload = payload.get("input")
            if isinstance(input_payload, dict):
                return input_payload
        return {}

    def _tool_error(self, events: list[BrowserOSLevel2StreamEvent]) -> bool:
        for event in events:
            output = event.payload.get("output")
            if isinstance(output, dict) and output.get("isError") is True:
                return True
        return False

    def _contains_unstable_element_id(self, input_payload: dict[str, Any]) -> bool:
        return isinstance(input_payload.get("element"), int)

    def _target_hint(self, tool_name: str, input_payload: dict[str, Any]) -> str | None:
        if tool_name == "navigate_page":
            url = input_payload.get("url")
            return str(url) if url else None
        for key in ("selector", "text", "elementText", "name"):
            value = input_payload.get(key)
            if isinstance(value, str) and value:
                return value
        return None

    def _value_hint(self, tool_name: str, input_payload: dict[str, Any]) -> str | None:
        if tool_name == "fill":
            value = input_payload.get("text") or input_payload.get("value")
            return str(value) if value is not None else None
        if tool_name == "select_option":
            value = input_payload.get("value") or input_payload.get("label")
            return str(value) if value is not None else None
        if tool_name == "press_key":
            value = input_payload.get("key")
            return str(value) if value is not None else None
        return None

    def _merge_reasons(self, left: str | None, right: str) -> str:
        if not left:
            return right
        if right in left:
            return left
        return f"{left}; {right}"
