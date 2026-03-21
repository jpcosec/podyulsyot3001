"""Contracts for the extract_understand node."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TextSpan(BaseModel):
    start_line: int | None = None
    end_line: int | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    preview_snippet: str | None = None


class JobRequirement(BaseModel):
    id: str
    text: str
    priority: Literal["must", "nice"]
    text_span: TextSpan | None = None


class JobConstraint(BaseModel):
    constraint_type: str
    description: str


class ContactInfo(BaseModel):
    name: str | None = None
    email: str | None = None


class JobUnderstandingExtract(BaseModel):
    job_title: str
    analysis_notes: str = Field(
        ...,
        description="Logical extraction rationale written in English.",
    )
    requirements: list[JobRequirement]
    constraints: list[JobConstraint]
    risk_areas: list[str] = Field(default_factory=list)
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    salary_grade: str | None = None
