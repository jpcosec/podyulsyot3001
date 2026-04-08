"""Tests for BrowserOS MCP trace normalization into shared candidates."""

from __future__ import annotations

from src.automation.motors.browseros.cli.normalizer import BrowserOSMcpTraceNormalizer
from src.automation.motors.browseros.cli.recording import (
    BrowserOSMcpRecordedCall,
    BrowserOSMcpRecording,
)


def test_normalize_mcp_recording_into_shared_candidates():
    recording = BrowserOSMcpRecording(
        calls=[
            BrowserOSMcpRecordedCall(
                timestamp="2026-04-08T00:00:00+00:00",
                request_id=1,
                tool_name="navigate_page",
                arguments={"url": "https://example.com/apply"},
            ),
            BrowserOSMcpRecordedCall(
                timestamp="2026-04-08T00:00:01+00:00",
                request_id=2,
                tool_name="fill",
                arguments={"selector": "#first-name", "text": "Ada"},
            ),
        ]
    )

    candidates = BrowserOSMcpTraceNormalizer().normalize(recording)

    assert len(candidates) == 2
    assert candidates[0].actions[0].candidate_intent == "navigate"
    assert candidates[0].actions[0].target_hint == "https://example.com/apply"
    assert candidates[1].actions[0].candidate_intent == "fill"
    assert candidates[1].actions[0].target_hint == "#first-name"
    assert candidates[1].actions[0].value_hint == "Ada"


def test_normalize_mcp_recording_flags_snapshot_local_element_ids():
    recording = BrowserOSMcpRecording(
        calls=[
            BrowserOSMcpRecordedCall(
                timestamp="2026-04-08T00:00:00+00:00",
                request_id=1,
                tool_name="click",
                arguments={"page": 3, "element": 41},
            )
        ]
    )

    candidates = BrowserOSMcpTraceNormalizer().normalize(recording)

    assert len(candidates) == 1
    assert candidates[0].requires_review is True
    assert "snapshot-local element id" in candidates[0].review_reason
