from __future__ import annotations

from pydantic import BaseModel, Field


class MatchEdge(BaseModel):
    requirement_id: str
    profile_evidence_ids: list[str] = Field(default_factory=list)
    match_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
