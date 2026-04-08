"""Shared BrowserOS promotion intermediate models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class BrowserOSActionCandidate(BaseModel):
    """One candidate replay action derived from BrowserOS evidence."""

    source: Literal["level1", "level2"]
    origin: str
    candidate_intent: str | None = None
    target_hint: str | None = None
    value_hint: str | None = None
    requires_review: bool = False
    review_reason: str | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)


class BrowserOSStepCandidate(BaseModel):
    """Shared BrowserOS promotion step used by both Level 1 and Level 2."""

    step_index: int
    source: Literal["level1", "level2"]
    actions: list[BrowserOSActionCandidate] = Field(default_factory=list)
    requires_review: bool = False
    review_reason: str | None = None
