"""Low-level BrowserOS CDP recording helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BrowserOSCdpEvent(BaseModel):
    """Normalized low-level BrowserOS CDP capture event."""

    timestamp: str
    event_type: str
    data: dict[str, Any]


class BrowserOSCdpRecording(BaseModel):
    """Collection of low-level BrowserOS CDP events."""

    started_at: str = Field(default_factory=_utc_now)
    events: list[BrowserOSCdpEvent] = Field(default_factory=list)


class BrowserOSCdpRecorder:
    """Parse useful Ariadne-relevant signals from BrowserOS CDP events."""

    def __init__(self) -> None:
        self.recording = BrowserOSCdpRecording()

    def ingest(self, event: dict[str, Any]) -> BrowserOSCdpEvent | None:
        method = event.get("method")
        if method == "Page.frameNavigated":
            frame = event.get("params", {}).get("frame", {})
            normalized = BrowserOSCdpEvent(
                timestamp=_utc_now(),
                event_type="navigate",
                data={
                    "url": frame.get("url"),
                    "frame_id": frame.get("id"),
                },
            )
            self.recording.events.append(normalized)
            return normalized

        if method != "Runtime.consoleAPICalled":
            return None

        payload = self._extract_console_payload(event)
        if not isinstance(payload, dict) or not payload.get("__rec"):
            return None

        normalized = BrowserOSCdpEvent(
            timestamp=_utc_now(),
            event_type=str(payload.get("type", "unknown")),
            data={
                key: value
                for key, value in payload.items()
                if key not in {"__rec", "type"}
            },
        )
        self.recording.events.append(normalized)
        return normalized

    def _extract_console_payload(self, event: dict[str, Any]) -> dict[str, Any] | None:
        args = event.get("params", {}).get("args", [])
        for arg in args:
            value = arg.get("value") if isinstance(arg, dict) else None
            if not isinstance(value, str):
                continue
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return None
