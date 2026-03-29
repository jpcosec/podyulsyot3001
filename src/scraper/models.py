"""Unified data contract for job postings across all scraping sources.

The schema is split into two tiers:
- MANDATORY (Intersection): Fields present in ALL portals. Pydantic will
  raise ValidationError if any of these are missing.
- OPTIONAL (Union): Fields that enrich the data but may naturally be absent
  on some portals (e.g., TU Berlin has no salary estimate).
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class JobPosting(BaseModel):
    """Standardized Job Posting Contract.

    Used as the extraction target for both LLM and CSS strategies.
    The Field descriptions serve double duty: they document the schema
    AND guide the LLM extractor when it needs to reason about content.
    """

    # ---------------------------------------------------------
    # MANDATORY FIELDS (The Intersection)
    # ---------------------------------------------------------
    job_title: str = Field(..., description="The official job title")
    company_name: str = Field(
        ..., description="Name of the company, university, or institution"
    )
    location: str = Field(..., description="City or primary location")
    employment_type: str = Field(
        ..., description="Type of employment (e.g. Full-time, Part-time, Internship)"
    )
    responsibilities: List[str] = Field(
        ...,
        min_length=1,
        description="List of responsibilities or tasks ('Deine Aufgaben', 'Your Impact')",
    )
    requirements: List[str] = Field(
        ...,
        min_length=1,
        description="List of requirements, profile or skills ('Dein Profil', 'Skills & Experience')",
    )

    # ---------------------------------------------------------
    # OPTIONAL FIELDS (The Union)
    # ---------------------------------------------------------
    salary: Optional[str] = Field(
        default=None,
        description="Estimated salary or salary range (e.g. '€70,000 – €91,500' or 'TV-L 13')",
    )
    remote_policy: Optional[str] = Field(
        default=None,
        description="Remote work policy (On-site, Hybrid, 100% Remote, Homeoffice möglich)",
    )
    benefits: List[str] = Field(
        default_factory=list,
        description="Extra benefits offered (vacation, equipment, training, etc.)",
    )
    company_description: Optional[str] = Field(
        default=None,
        description="Short description of the company ('Über uns', 'About the company')",
    )
    company_industry: Optional[str] = Field(
        default=None, description="Sector or industry (e.g. 'IT & Tech', 'Consulting')"
    )
    company_size: Optional[str] = Field(
        default=None, description="Company size (e.g. '1001-5000 employees')"
    )
    posted_date: str = Field(
        ...,
        description="Date of publication or time elapsed (e.g. 'vor 1 Woche', '26.03.2026')",
    )
    application_deadline: Optional[str] = Field(
        default=None, description="Deadline to apply"
    )
    # TODO(future): validate whether application routing belongs in scrape-time contract or a later interpretation step — see future_docs/issues/application_routing_extraction.md
    application_method: Optional[str] = Field(
        default=None,
        description="How to apply when explicitly stated (e.g. 'email', 'external portal', 'company portal', 'XING Easy Apply')",
    )
    application_url: Optional[str] = Field(
        default=None,
        description="Direct application URL or apply button target when available",
    )
    application_email: Optional[str] = Field(
        default=None,
        description="Application email address when the posting asks candidates to apply by email",
    )
    application_instructions: Optional[str] = Field(
        default=None,
        description="Short instructions on how to apply (e.g. 'Send CV by email', 'Apply via company portal')",
    )
    reference_number: Optional[str] = Field(
        default=None, description="Internal reference code for the posting"
    )
    contact_info: Optional[str] = Field(
        default=None, description="Email or contact person for application"
    )
    original_language: Optional[str] = Field(
        default=None,
        description="The detected ISO 639-1 language code (e.g. 'de', 'en', 'es')",
    )
