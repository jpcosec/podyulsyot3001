"""Promotion - event loading helpers."""

from src.automation.ariadne.capabilities.recording import GraphRecorder


def load_deterministic_events(recorder: GraphRecorder, thread_id: str) -> list[dict]:
    """Load and filter deterministic events from thread recording."""
    events = recorder.load_events(thread_id)
    if not events:
        raise FileNotFoundError(f"No recording found for thread '{thread_id}'.")

    deterministic_events = [
        event for event in events if event.get("event_type") == "execute_deterministic"
    ]
    if not deterministic_events:
        raise ValueError(f"No deterministic events recorded for thread '{thread_id}'.")
    return deterministic_events


def extract_metadata(deterministic_events: list[dict]) -> tuple[str, str]:
    """Extract portal name and mission ID from first event."""
    first_payload = deterministic_events[0]["payload"]
    portal_name = first_payload.get("portal_name", "unknown")
    mission_id = first_payload.get("current_mission_id") or "promoted"
    return portal_name, mission_id
