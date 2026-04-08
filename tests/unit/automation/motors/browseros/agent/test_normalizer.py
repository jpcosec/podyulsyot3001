"""Tests for BrowserOS Level 2 trace normalization."""

from __future__ import annotations

from src.automation.motors.browseros.agent.normalizer import (
    BrowserOSLevel2TraceNormalizer,
)
from src.automation.motors.browseros.agent.models import (
    BrowserOSLevel2StreamEvent,
    BrowserOSLevel2Trace,
)


def _event(conversation_id: str, event_type: str, payload: dict):
    return BrowserOSLevel2StreamEvent(
        timestamp="2026-04-08T00:00:00+00:00",
        conversation_id=conversation_id,
        event_type=event_type,
        payload={"type": event_type, **payload},
    )


def test_normalize_maps_supported_tools_to_candidates():
    conversation_id = "conv-1"
    trace = BrowserOSLevel2Trace(
        conversation_id=conversation_id,
        source="xing",
        goal="apply",
        provider="browseros",
        model="browseros-auto",
        mode="agent",
        started_at="2026-04-08T00:00:00+00:00",
        stream_events=[
            _event(
                conversation_id,
                "tool-input-available",
                {
                    "toolCallId": "functions.navigate_page:0",
                    "toolName": "navigate_page",
                    "input": {"url": "https://example.com/apply"},
                },
            ),
            _event(
                conversation_id,
                "tool-input-available",
                {
                    "toolCallId": "functions.fill:1",
                    "toolName": "fill",
                    "input": {"selector": "#first-name", "text": "Ada"},
                },
            ),
        ],
    )

    candidates = BrowserOSLevel2TraceNormalizer().normalize(trace)

    assert len(candidates) == 2
    assert candidates[0].candidate_intent == "navigate"
    assert candidates[0].target_hint == "https://example.com/apply"
    assert candidates[0].requires_review is False
    assert candidates[1].candidate_intent == "fill"
    assert candidates[1].target_hint == "#first-name"
    assert candidates[1].value_hint == "Ada"


def test_normalize_flags_snapshot_local_element_ids_for_review():
    conversation_id = "conv-2"
    trace = BrowserOSLevel2Trace(
        conversation_id=conversation_id,
        source="xing",
        goal="apply",
        provider="browseros",
        model="browseros-auto",
        mode="agent",
        started_at="2026-04-08T00:00:00+00:00",
        stream_events=[
            _event(
                conversation_id,
                "tool-input-available",
                {
                    "toolCallId": "functions.click:0",
                    "toolName": "click",
                    "input": {"page": 4, "element": 512},
                },
            )
        ],
    )

    candidates = BrowserOSLevel2TraceNormalizer().normalize(trace)

    assert len(candidates) == 1
    assert candidates[0].candidate_intent == "click"
    assert candidates[0].requires_review is True
    assert "snapshot-local element id" in candidates[0].review_reason


def test_normalize_flags_tool_errors_for_review():
    conversation_id = "conv-3"
    trace = BrowserOSLevel2Trace(
        conversation_id=conversation_id,
        source="xing",
        goal="apply",
        provider="browseros",
        model="browseros-auto",
        mode="agent",
        started_at="2026-04-08T00:00:00+00:00",
        stream_events=[
            _event(
                conversation_id,
                "tool-input-available",
                {
                    "toolCallId": "functions.get_active_page:0",
                    "toolName": "get_active_page",
                    "input": {},
                },
            ),
            _event(
                conversation_id,
                "tool-output-available",
                {
                    "toolCallId": "functions.get_active_page:0",
                    "toolName": "get_active_page",
                    "output": {"isError": True},
                },
            ),
        ],
    )

    candidates = BrowserOSLevel2TraceNormalizer().normalize(trace)

    assert len(candidates) == 1
    assert candidates[0].requires_review is True
    assert "unsupported BrowserOS tool" in candidates[0].review_reason
    assert "tool output reported an error" in candidates[0].review_reason
