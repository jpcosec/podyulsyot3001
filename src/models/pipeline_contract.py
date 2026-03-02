from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.models.job import JobPosting


class EvidenceItem(BaseModel):
    id: str
    type: Literal[
        "cv_line",
        "role",
        "project",
        "publication",
        "education",
        "skill",
        "language",
    ]
    text: str
    source_ref: str = ""


class RequirementMapping(BaseModel):
    req_id: str
    priority: Literal["must", "nice"]
    coverage: Literal["full", "partial", "none"]
    evidence_ids: list[str]
    notes: str = ""


class ProposedClaim(BaseModel):
    id: str
    target_section: Literal[
        "summary",
        "experience",
        "education",
        "publications",
        "skills",
        "languages",
    ]
    target_subsection: str | None = None
    claim_text: str
    based_on_evidence_ids: list[str]
    inflation_level: Literal["none", "light", "high"] = "none"
    risk_level: Literal["low", "medium", "high"] = "low"
    evidence_gap: str = ""
    status: Literal["proposed", "approved", "rejected"] = "proposed"
    reviewer_notes: str = ""


class RenderConfig(BaseModel):
    ordering: list[str] = Field(
        default_factory=lambda: [
            "header",
            "summary",
            "education",
            "experience",
            "publications",
            "skills",
            "languages",
        ]
    )
    style_rules: dict[str, bool] = Field(
        default_factory=lambda: {
            "one_column": True,
            "no_tables": True,
            "no_icons": True,
        }
    )


class PipelineState(BaseModel):
    """Full state object that flows through MATCHER -> SELLER -> CHECKER."""

    job: JobPosting
    evidence_items: list[EvidenceItem]
    mapping: list[RequirementMapping]
    proposed_claims: list[ProposedClaim] = Field(default_factory=list)
    render: RenderConfig = Field(default_factory=RenderConfig)


class ReviewedClaim(BaseModel):
    req_id: str
    decision: Literal["approved", "edited", "rejected"]
    claim_text: str
    evidence_ids: list[str] = Field(default_factory=list)
    section: str = "summary"
    notes: str = ""


class ReviewedMapping(BaseModel):
    job_id: str
    status: Literal["proposed", "reviewed", "approved"] = "proposed"
    claims: list[ReviewedClaim] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    summary: str = ""
