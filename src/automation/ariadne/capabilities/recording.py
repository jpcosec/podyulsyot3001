"""Graph recording utilities for Ariadne execution traces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class GraphRecorder:
    """Persist append-only Ariadne graph events for later promotion."""

    def __init__(self, base_dir: Path | str = "data/ariadne/recordings") -> None:
        self.base_dir = Path(base_dir)

    def record_event(
        self, thread_id: str, event_type: str, payload: dict[str, Any]
    ) -> Path:
        """Append one normalized event to the session JSONL trace."""
        session_dir = self.base_dir / thread_id
        session_dir.mkdir(parents=True, exist_ok=True)
        trace_path = session_dir / "raw_timeline.jsonl"
        event = {
            "event_type": event_type,
            "thread_id": thread_id,
            "payload": payload,
        }
        with trace_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
        return trace_path

    def load_events(self, thread_id: str) -> list[dict[str, Any]]:
        """Load all recorded events for one session."""
        trace_path = self.base_dir / thread_id / "raw_timeline.jsonl"
        if not trace_path.exists():
            return []
        with trace_path.open("r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]
