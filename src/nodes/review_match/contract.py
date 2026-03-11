"""Contracts for review_match deterministic parsing stage."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ReviewDirective(BaseModel):#TODO: Se esta usando esto?
    scope: Literal["local", "global"]
    directive_type: Literal[
        "factual", "strategic", "stylistic", "structural", "process"
    ]
    target: str
    action: Literal["keep", "edit", "drop", "regenerate", "forbid"]
    normalized_rule: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ParsedDecision(BaseModel):
    block_id: str
    decision: Literal["approve", "request_regeneration", "reject"]
    notes: str = ""
    directives: list[ReviewDirective] = Field(default_factory=list)


class DecisionEnvelope(BaseModel):
    node: str
    job_id: str
    round: int
    source_state_hash: str
    decisions: list[ParsedDecision]
    updated_at: str
