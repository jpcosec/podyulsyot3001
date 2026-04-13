"""Graph recording utilities for Ariadne execution traces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.automation.ariadne.io import (
    append_jsonl,
    append_jsonl_async,
    read_jsonl,
    read_jsonl_async,
)


class GraphRecorder:
    """Persist append-only Ariadne graph events for later promotion."""

    def __init__(self, base_dir: Path | str = "data/ariadne/recordings") -> None:
        self.base_dir = Path(base_dir)

    def record_event(
        self, thread_id: str, event_type: str, payload: dict[str, Any]
    ) -> Path:
        """Append one normalized event to the session timeline."""
        trace_path = self._trace_path(thread_id)
        return append_jsonl(
            trace_path, self._build_event(thread_id, event_type, payload)
        )

    async def record_event_async(
        self, thread_id: str, event_type: str, payload: dict[str, Any]
    ) -> Path:
        """Append one normalized event to the session timeline asynchronously."""
        trace_path = self._trace_path(thread_id)
        return await append_jsonl_async(
            trace_path,
            self._build_event(thread_id, event_type, payload),
        )

    def load_events(self, thread_id: str) -> list[dict[str, Any]]:
        """Load all recorded events for one session."""
        return read_jsonl(self._trace_path(thread_id))

    async def load_events_async(self, thread_id: str) -> list[dict[str, Any]]:
        """Load all recorded events for one session asynchronously."""
        return await read_jsonl_async(self._trace_path(thread_id))

    def _trace_path(self, thread_id: str) -> Path:
        return self.base_dir / thread_id / "raw_timeline.jsonl"

    def _build_event(
        self, thread_id: str, event_type: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "event_type": event_type,
            "thread_id": thread_id,
            "payload": payload,
        }
