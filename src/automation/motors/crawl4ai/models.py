# src/automation/motors/crawl4ai/models.py
"""C4AI motor data contracts.

Scrape-side: JobPosting — structured extraction output from a scrape run.
Apply-side:  FormSelectors, ApplicationRecord, ApplyMeta — apply flow I/O.

Both live here because they are produced and consumed exclusively within
the Crawl4AI motor.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ── Scrape side ──────────────────────────────────────────────────────────────

class JobPosting(BaseModel):
    """Standardized extraction output contract for all scraping sources."""

    # Mandatory
    job_title: str = Field(..., description="The official job title")
    company_name: str = Field(..., description="Name of the company, university, or institution")
    location: str = Field(..., description="City or primary location")
    employment_type: str = Field(..., description="Type of employment (e.g. Full-time, Part-time, Internship)")
    responsibilities: List[str] = Field(..., min_length=1, description="List of responsibilities or tasks")
    requirements: List[str] = Field(..., min_length=1, description="List of requirements, profile or skills")

    # Optional
    salary: Optional[str] = Field(default=None, description="Estimated salary or salary range")
    remote_policy: Optional[str] = Field(default=None, description="Remote work policy")
    benefits: List[str] = Field(default_factory=list, description="Extra benefits offered")
    company_description: Optional[str] = Field(default=None, description="Short description of the company")
    company_industry: Optional[str] = Field(default=None, description="Sector or industry")
    company_size: Optional[str] = Field(default=None, description="Company size")
    posted_date: Optional[str] = Field(default=None, description="Date of publication")
    days_ago: Optional[str] = Field(default=None, description="Relative publication age")
    application_deadline: Optional[str] = Field(default=None, description="Deadline to apply")
    application_method: Optional[str] = Field(default=None, description="How to apply")
    application_url: Optional[str] = Field(default=None, description="Direct application URL")
    application_email: Optional[str] = Field(default=None, description="Application email address")
    application_instructions: Optional[str] = Field(default=None, description="Short instructions on how to apply")
    reference_number: Optional[str] = Field(default=None, description="Internal reference code")
    contact_info: Optional[str] = Field(default=None, description="Email or contact person")
    original_language: Optional[str] = Field(default=None, description="Detected ISO 639-1 language code")


# ── Apply side ───────────────────────────────────────────────────────────────

class FormSelectors(BaseModel):
    """CSS selectors validated against the live DOM before interaction.

    Mandatory selectors: absence raises PortalStructureChangedError.
    Optional selectors: absence is logged as a warning and the interaction is skipped.
    """

    # Mandatory
    apply_button: str
    cv_upload: str
    submit_button: str
    success_indicator: str

    # Optional
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    letter_upload: str | None = None
    error_indicator: str | None = None
    cv_select_existing: str | None = None


class ApplicationRecord(BaseModel):
    """Persisted record of one apply attempt for a specific job."""

    source: str
    job_id: str
    job_title: str
    company_name: str
    application_url: str
    cv_path: str
    letter_path: str | None
    fields_filled: list[str]
    dry_run: bool
    submitted_at: str | None
    confirmation_text: str | None


class ApplyMeta(BaseModel):
    """Small status artifact describing the outcome of an apply run."""

    status: Literal["submitted", "dry_run", "failed", "portal_changed"]
    timestamp: str
    error: str | None = None
