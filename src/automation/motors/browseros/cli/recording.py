"""Recording helpers for BrowserOS MCP interactions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BrowserOSMcpRecordedCall(BaseModel):
    """One recorded BrowserOS MCP tool invocation."""

    timestamp: str
    request_id: int
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None = None
    error: str | None = None


class BrowserOSMcpSnapshotRecord(BaseModel):
    """Parsed snapshot tied to a recorded MCP call."""

    timestamp: str
    request_id: int
    elements: list[Any]


class BrowserOSMcpRecording(BaseModel):
    """Raw deterministic BrowserOS MCP recording."""

    started_at: str = Field(default_factory=_utc_now)
    calls: list[BrowserOSMcpRecordedCall] = Field(default_factory=list)
    snapshots: list[BrowserOSMcpSnapshotRecord] = Field(default_factory=list)


class BrowserOSMcpRecorder:
    """Collect raw MCP calls and parsed snapshots."""

    def __init__(self) -> None:
        self.recording = BrowserOSMcpRecording()

    def record_call(
        self,
        *,
        request_id: int,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        self.recording.calls.append(
            BrowserOSMcpRecordedCall(
                timestamp=_utc_now(),
                request_id=request_id,
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                error=error,
            )
        )

    def record_snapshot(
        self,
        *,
        request_id: int,
        elements: list[SnapshotElement],
    ) -> None:
        self.recording.snapshots.append(
            BrowserOSMcpSnapshotRecord(
                timestamp=_utc_now(),
                request_id=request_id,
                elements=elements,
            )
        )
