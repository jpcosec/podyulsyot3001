"""Typed contracts for the LangGraph-native match skill.

The models in this module serve three roles:

1. define the structured input/output contract for the LLM call,
2. define the human review payload exchanged through LangGraph state updates,
3. define the persisted JSON review surface and feedback artifacts.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


ReviewDecision = Literal["approve", "request_regeneration", "reject"]
MatchRecommendation = Literal["proceed", "marginal", "reject"]
MatchStatus = Literal["matched", "partial", "missing"]


class RequirementInput(BaseModel):
    """Requirement extracted from a job posting.

    Attributes:
        id: Stable requirement identifier used across match and review rounds.
        text: Human-readable requirement text shown to the model and reviewers.
        priority: Optional importance label preserved from upstream extraction.
    """

    id: str = Field(description="Stable requirement identifier")
    text: str = Field(description="Human-readable requirement text")
    priority: str | None = Field(default=None, description="Priority label if present")


class ProfileEvidence(BaseModel):
    """Evidence item from the candidate profile.

    Attributes:
        id: Stable evidence identifier used for traceability.
        description: Evidence text that the model may cite while matching.
    """

    id: str = Field(description="Stable evidence identifier")
    description: str = Field(description="Evidence text used for matching")


class RequirementMatch(BaseModel):
    """Model output for one requirement match decision.

    Attributes:
        requirement_id: Identifier of the requirement being assessed.
        status: Qualitative coverage label for reviewer-friendly display.
        score: Normalized score in the inclusive range ``[0.0, 1.0]``.
        evidence_ids: Supporting evidence identifiers selected by the model.
        evidence_quotes: Optional short quotations copied into the review surface.
        reasoning: Short explanation justifying the score and status.
    """

    requirement_id: str = Field(description="Requirement identifier")
    status: MatchStatus = Field(description="How well the requirement is covered")
    score: float = Field(ge=0.0, le=1.0, description="Normalized match score")
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Profile evidence ids that support this assessment",
    )
    evidence_quotes: list[str] = Field(
        default_factory=list,
        description="Short evidence snippets quoted by the model",
    )
    reasoning: str = Field(description="Short explanation for the score")

    @field_validator("evidence_ids", mode="before")
    @classmethod
    def _normalize_evidence_ids(cls, value: object) -> object:
        """Accept comma-separated evidence ids for backward-compatible inputs."""

        if value is None:
            return []
        if isinstance(value, str):
            parts = [part.strip() for part in value.split(",") if part.strip()]
            return parts
        return value


class MatchEnvelope(BaseModel):
    """Canonical structured output for the match step.

    Attributes:
        matches: Per-requirement assessments produced by the model.
        total_score: Aggregate score used for summary and coarse routing hints.
        decision_recommendation: Model recommendation before human review.
        summary_notes: Short global summary for the operator-facing surface.
    """

    matches: list[RequirementMatch]
    total_score: float = Field(ge=0.0, le=1.0)
    decision_recommendation: MatchRecommendation
    summary_notes: str


class ReviewItemDecision(BaseModel):
    """Human review decision for one requirement.

    Attributes:
        requirement_id: Requirement being reviewed.
        decision: Reviewer action for this requirement.
        note: Optional reviewer note.
        patch_evidence: Optional evidence patch used during regeneration.
    """

    requirement_id: str
    decision: ReviewDecision
    note: str = ""
    patch_evidence: ProfileEvidence | None = None


class ReviewPayload(BaseModel):
    """Structured review payload submitted by a UI or CLI.

    Attributes:
        source_state_hash: Hash binding the review to a specific match proposal.
        items: Per-requirement human decisions.
    """

    source_state_hash: str
    items: list[ReviewItemDecision]


class FeedbackItem(BaseModel):
    """Deterministic feedback item persisted between rounds.

    Attributes:
        requirement_id: Requirement affected by the feedback item.
        action: Deterministic normalized action consumed by regeneration logic.
        reviewer_note: Optional reviewer note after normalization.
        patch_evidence: Optional evidence patch forwarded to later rounds.
    """

    requirement_id: str
    action: Literal["proceed", "patch", "reject"]
    reviewer_note: str = ""
    patch_evidence: ProfileEvidence | None = None


class ReviewSurfaceItem(BaseModel):
    """JSON review row rendered for the UI layer.

    Attributes:
        requirement_id: Requirement identifier.
        requirement_text: Requirement text shown in the UI.
        priority: Optional upstream importance label.
        score: Model score for this requirement.
        status: Qualitative match status.
        evidence_ids: Evidence ids referenced by the model.
        evidence_texts: Resolved evidence descriptions for direct display.
        evidence_quotes: Short evidence snippets emitted by the model.
        reasoning: Model reasoning shown to the reviewer.
        in_regeneration_scope: Whether the row is actionable in the current round.
    """

    requirement_id: str
    requirement_text: str
    priority: str | None = None
    score: float = Field(ge=0.0, le=1.0)
    status: MatchStatus
    evidence_ids: list[str] = Field(default_factory=list)
    evidence_texts: list[str] = Field(default_factory=list)
    evidence_quotes: list[str] = Field(default_factory=list)
    reasoning: str
    in_regeneration_scope: bool = True


class ReviewSurface(BaseModel):
    """Persisted review payload displayed by Studio or a custom UI.

    Attributes:
        node: Logical node name associated with the review artifact.
        round_number: Immutable review round number.
        source_state_hash: Hash of the approved match payload for stale-review checks.
        recommendation: Model-level recommendation before human review.
        total_score: Aggregate score for the round.
        summary_notes: High-level operator-facing summary.
        items: Row-level review data.
        allowed_decisions: Allowed reviewer actions for the UI.
    """

    node: str = "match_skill"
    round_number: int
    source_state_hash: str
    recommendation: MatchRecommendation
    total_score: float = Field(ge=0.0, le=1.0)
    summary_notes: str
    items: list[ReviewSurfaceItem]
    allowed_decisions: tuple[ReviewDecision, ...] = (
        "approve",
        "request_regeneration",
        "reject",
    )
