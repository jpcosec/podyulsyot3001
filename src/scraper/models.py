"""Scraper Models — Standardized extraction output contracts."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class JobPosting(BaseModel):
    """Standardized extraction output contract for all scraping sources."""

    # Mandatory
    job_title: str = Field(..., description="The official job title")
    company_name: str = Field(
        ..., description="Name of the company, university, or institution"
    )
    location: str = Field(..., description="City or primary location")
    employment_type: str = Field(
        ..., description="Type of employment (e.g. Full-time, Part-time, Internship)"
    )
    responsibilities: List[str] = Field(
        default_factory=list,
        description="List of responsibilities or tasks.",
    )
    requirements: List[str] = Field(
        default_factory=list, description="List of requirements, profile or skills."
    )

    @field_validator("requirements")
    @classmethod
    def must_have_some_content(cls, v: List[str], info: Any) -> List[str]:
        responsibilities = info.data.get("responsibilities", [])
        if not v and not responsibilities:
            raise ValueError("JobPosting must have at least one responsibility or requirement.")
        return v

    # Optional
    salary: Optional[str] = Field(default=None)
    remote_policy: Optional[str] = Field(default=None)
    benefits: List[str] = Field(default_factory=list)
    company_description: Optional[str] = Field(default=None)
    company_industry: Optional[str] = Field(default=None)
    company_size: Optional[str] = Field(default=None)
    posted_date: Optional[str] = Field(default=None)
    days_ago: Optional[str] = Field(default=None)
    application_deadline: Optional[str] = Field(default=None)
    application_method: Optional[str] = Field(default=None)
    application_url: Optional[str] = Field(default=None)
    application_email: Optional[str] = Field(default=None)
    application_instructions: Optional[str] = Field(default=None)
    reference_number: Optional[str] = Field(default=None)
    contact_info: Optional[str] = Field(default=None)
    original_language: Optional[str] = Field(default=None)
