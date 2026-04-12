"""Tests for graph recording and promotion."""

import json

from src.automation.ariadne.capabilities.recording import GraphRecorder
from src.automation.ariadne.promotion import AriadnePromoter


def test_graph_recorder_writes_jsonl_events(tmp_path):
    """Recorder should append events to the session timeline."""
    recorder = GraphRecorder(tmp_path)

    trace_path = recorder.record_event(
        "thread-1",
        "observe",
        {"current_state_id": "job_details", "current_url": "https://example.com"},
    )

    assert trace_path.exists()
    lines = trace_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["event_type"] == "observe"
    assert event["payload"]["current_state_id"] == "job_details"


def test_promoter_builds_draft_map_from_recording(tmp_path):
    """Promotion should turn deterministic events into a draft Ariadne map."""
    recorder = GraphRecorder(tmp_path)
    recorder.record_event(
        "thread-2",
        "execute_deterministic",
        {
            "portal_name": "linkedin",
            "current_mission_id": "easy_apply",
            "state_before": {
                "current_state_id": "job_details",
                "profile_data": {"first_name": "Ariadne"},
                "job_data": {"cv_path": "/tmp/cv.pdf"},
            },
            "selected_edges": [
                {
                    "from_state": "job_details",
                    "to_state": "easy_apply_modal",
                    "mission_id": "easy_apply",
                    "intent": "fill",
                    "target": {"css": "input[name='firstName']"},
                    "value": "Ariadne",
                    "extract": None,
                }
            ],
            "result": {"status": "success", "error": None},
            "state_after": {"current_state_id": "easy_apply_modal", "errors": []},
        },
    )

    promoter = AriadnePromoter(tmp_path)
    promoted_map = promoter.promote_thread("thread-2")

    assert promoted_map.meta.source == "linkedin"
    assert promoted_map.meta.flow == "easy_apply"
    assert promoted_map.meta.status == "draft"
    assert promoted_map.edges[0].value == "{{first_name}}"
    assert (tmp_path / "thread-2" / "normalized_map.json").exists()
