"""Tests for low-level BrowserOS CDP recording helpers."""

from __future__ import annotations

import json

from src.automation.motors.browseros.cdp_recorder import BrowserOSCdpRecorder


def test_ingest_frame_navigation_event():
    recorder = BrowserOSCdpRecorder()

    normalized = recorder.ingest(
        {
            "method": "Page.frameNavigated",
            "params": {"frame": {"id": "frame-1", "url": "https://example.com/apply"}},
        }
    )

    assert normalized is not None
    assert normalized.event_type == "navigate"
    assert normalized.data["url"] == "https://example.com/apply"


def test_ingest_console_capture_event():
    recorder = BrowserOSCdpRecorder()
    payload = json.dumps(
        {
            "__rec": True,
            "type": "click",
            "tag": "BUTTON",
            "text": "Apply now",
            "x": 12,
            "y": 34,
        }
    )

    normalized = recorder.ingest(
        {
            "method": "Runtime.consoleAPICalled",
            "params": {"args": [{"value": payload}]},
        }
    )

    assert normalized is not None
    assert normalized.event_type == "click"
    assert normalized.data["text"] == "Apply now"


def test_ingest_ignores_non_recording_console_events():
    recorder = BrowserOSCdpRecorder()

    normalized = recorder.ingest(
        {
            "method": "Runtime.consoleAPICalled",
            "params": {"args": [{"value": json.dumps({"hello": "world"})}]},
        }
    )

    assert normalized is None
    assert recorder.recording.events == []
