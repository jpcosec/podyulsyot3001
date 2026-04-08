"""Tests for deterministic BrowserOS MCP promotion."""

from __future__ import annotations

from src.automation.motors.browseros.cli.promoter import BrowserOSMcpPromoter
from src.automation.motors.browseros.cli.recording import (
    BrowserOSMcpRecordedCall,
    BrowserOSMcpRecording,
)


def test_promote_deterministic_mcp_recording_into_replay_path():
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
            BrowserOSMcpRecordedCall(
                timestamp="2026-04-08T00:00:02+00:00",
                request_id=3,
                tool_name="click",
                arguments={"text": "Submit application"},
            ),
        ]
    )

    grouped, assessment, path = BrowserOSMcpPromoter().promote(
        portal="xing",
        recording=recording,
    )

    assert len(grouped) == 2
    assert assessment.outcome == "promotable"
    assert path is not None
    assert path.steps[0].actions[0].intent == "navigate"
    assert len(path.steps[1].actions) == 2


def test_promote_mcp_recording_blocks_unstable_element_ids():
    recording = BrowserOSMcpRecording(
        calls=[
            BrowserOSMcpRecordedCall(
                timestamp="2026-04-08T00:00:00+00:00",
                request_id=1,
                tool_name="click",
                arguments={"page": 1, "element": 55},
            )
        ]
    )

    grouped, assessment, path = BrowserOSMcpPromoter().promote(
        portal="xing",
        recording=recording,
    )

    assert len(grouped) == 1
    assert assessment.outcome == "blocked"
    assert path is None
