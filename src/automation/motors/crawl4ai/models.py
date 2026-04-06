# src/automation/motors/crawl4ai/models.py
"""C4AI motor data contracts.

Scrape-side: JobPosting — structured extraction output from a scrape run.
Apply-side:  FormSelectors, ApplicationRecord, ApplyMeta — apply flow I/O.

Both live here because they are produced and consumed exclusively within
the Crawl4AI motor.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ── Scrape side ──────────────────────────────────────────────────────────────

class JobPosting(BaseModel):
    """Standardized extraction output contract for all scraping sources.

    The Field descriptions serve double duty: they document the schema
    AND guide the LLM extractor when it needs to reason about content.
    """

    # Mandatory
    job_title: str = Field(..., description="The official job title")
    company_name: str = Field(..., description="Name of the company, university, or institution")
    location: str = Field(..., description="City or primary location")
    employment_type: str = Field(..., description="Type of employment (e.g. Full-time, Part-time, Internship)")
    responsibilities: list[str] = Field(
        ..., min_length=1, description="List of responsibilities or tasks ('Deine Aufgaben', 'Your Impact')"
    )
    requirements: list[str] = Field(
        ..., min_length=1, description="List of requirements, profile or skills ('Dein Profil', 'Skills & Experience')"
    )

    # Optional
    salary: str | None = Field(
        default=None, description="Estimated salary or salary range (e.g. '€70,000 – €91,500' or 'TV-L 13')"
    )
    remote_policy: str | None = Field(
        default=None, description="Remote work policy (On-site, Hybrid, 100% Remote, Homeoffice möglich)"
    )
    benefits: list[str] = Field(default_factory=list, description="Extra benefits offered (vacation, equipment, training, etc.)")
    company_description: str | None = Field(
        default=None, description="Short description of the company ('Über uns', 'About the company')"
    )
    company_industry: str | None = Field(default=None, description="Sector or industry (e.g. 'IT & Tech', 'Consulting')")
    company_size: str | None = Field(default=None, description="Company size (e.g. '1001-5000 employees')")
    posted_date: str | None = Field(
        default=None, description="Date of publication when available (e.g. '26.03.2026' or an ISO timestamp after postprocessing)"
    )
    days_ago: str | None = Field(
        default=None, description="Relative publication age when available (e.g. '5 days ago', 'vor 1 Woche')"
    )
    application_deadline: str | None = Field(default=None, description="Deadline to apply")
    # TODO(future): validate whether application routing belongs in scrape-time contract or a later interpretation step — see plan_docs/issues/scraper/application_routing_extraction.md
    application_method: str | None = Field(
        default=None, description="How to apply when explicitly stated (e.g. 'email', 'external portal', 'company portal', 'XING Easy Apply')"
    )
    application_url: str | None = Field(
        default=None, description="Direct application URL or apply button target when available"
    )
    application_email: str | None = Field(
        default=None, description="Application email address when the posting asks candidates to apply by email"
    )
    application_instructions: str | None = Field(
        default=None, description="Short instructions on how to apply (e.g. 'Send CV by email', 'Apply via company portal')"
    )
    reference_number: str | None = Field(default=None, description="Internal reference code for the posting")
    contact_info: str | None = Field(default=None, description="Email or contact person for application")
    original_language: str | None = Field(
        default=None, description="The detected ISO 639-1 language code (e.g. 'de', 'en', 'es')"
    )


# ── Apply side ───────────────────────────────────────────────────────────────

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
