"""Shared BrowserOS agent trace models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BrowserOSLevel2StreamEvent(BaseModel):
    """One parsed SSE event from BrowserOS `/chat`."""

    timestamp: str
    conversation_id: str
    event_type: str
    payload: dict[str, Any]


class BrowserOSLevel2Trace(BaseModel):
    """Raw Level 2 trace captured from BrowserOS `/chat`."""

    conversation_id: str
    source: str
    goal: str
    provider: str
    model: str
    mode: str
    started_at: str
    ended_at: str | None = None
    stream_events: list[BrowserOSLevel2StreamEvent] = Field(default_factory=list)
    final_text: str | None = None
    finish_reason: str | None = None
    evidence_paths: list[str] = Field(default_factory=list)
