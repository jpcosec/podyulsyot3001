"""Job-side contracts: structured job knowledge and requirement deltas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from src.core.ai.generate_documents_v2.contracts.base import TextAnchor


class JobRequirement(BaseModel):
    """One requirement extracted from a job posting."""

    id: str
    text: str
    category: Literal["hard", "soft"] = "hard"
    priority: int = Field(ge=1, le=5, default=3)

    @field_validator("id", "text")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must be non-empty")
        return cleaned


class JobLogistics(BaseModel):
    """Non-technical job context: location, contract, relocation."""

    location: str | None = None
    remote: bool | None = None
    contract_type: str | None = None
    relocation: bool | None = None
    visa_sponsorship: bool | None = None


class CompanyData(BaseModel):
    """Company-side metadata for assembly and document headers."""

    name: str | None = None
    contact_person: str | None = None
    department: str | None = None


class JobKG(BaseModel):
    """Structured knowledge graph extracted from a raw job posting (J2)."""

    source_language: str | None = None
    job_title_original: str | None = None
    job_title_english: str | None = None
    hard_requirements: list[JobRequirement] = Field(default_factory=list)
    soft_context: list[JobRequirement] = Field(default_factory=list)
    logistics: JobLogistics = Field(default_factory=JobLogistics)
    company: CompanyData = Field(default_factory=CompanyData)
    salary_range: str | None = Field(
        default=None,
        description=(
            "Salary or pay-grade information as stated in the posting "
            "(e.g. 'EUR 70k–90k', 'Grade IC4', 'competitive'). "
            "Preserve the original wording; omit when not mentioned."
        ),
    )
    source_anchors: list[TextAnchor] = Field(default_factory=list)


class JobDelta(BaseModel):
    """Relevance filter for what to emphasize in this application (J3)."""

    must_highlight_skills: list[str] = Field(default_factory=list)
    ignored_requirements: list[str] = Field(default_factory=list)
    custom_instructions: str = ""
    soft_vibe_requirements: list[str] = Field(default_factory=list)
    logistics_flags: dict[str, bool] = Field(default_factory=dict)
