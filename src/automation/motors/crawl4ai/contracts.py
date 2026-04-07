"""Typed discovery contracts for Crawl4AI scrape adapters.

This module defines the listing-side payload captured during discovery before a
detail page is crawled and validated into a canonical job posting.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DiscoveryListingData(BaseModel):
    """Normalized teaser fields collected from a listing surface.

    Args:
        job_title: Listing-card title shown before visiting the detail page.
        company_name: Employer name shown in listing results.
        location: Listing-card location teaser.
        salary: Listing-card salary teaser when present.
        employment_type: Listing-card contract or workload label.
        posted_date: Relative or absolute publication timestamp from discovery.

    Returns:
        A validated teaser payload that still allows extra source-specific keys.
    """

    model_config = ConfigDict(extra="allow")

    job_title: str | None = Field(
        default=None,
        description="Listing-card title text for the job posting.",
    )
    company_name: str | None = Field(
        default=None,
        description="Employer name captured from the listing card when present.",
    )
    location: str | None = Field(
        default=None,
        description="Location teaser shown in the listing result.",
    )
    salary: str | None = Field(
        default=None,
        description="Salary teaser shown in the listing result.",
    )
    employment_type: str | None = Field(
        default=None,
        description="Employment-type teaser such as 'Full-time' or 'Internship'.",
    )
    posted_date: str | None = Field(
        default=None,
        description="Relative or absolute publication date captured during discovery.",
    )


class ScrapeDiscoveryEntry(BaseModel):
    """Structured discovery evidence for one job listing.

    Args:
        url: Canonical detail-page URL to crawl next.
        job_id: Stable identifier extracted from the listing URL.
        listing_position: Zero-based position of the card within discovery results.
        search_url: Listing URL that produced this job candidate.
        listing_snippet: Human-readable teaser text preserved for `listing_case.md`.
        listing_data: Structured teaser fields captured from the listing surface.
        listing_link: Raw link object from Crawl4AI when available.
        source_metadata: Additional source-specific context needed for later merges.

    Returns:
        A validated, job-scoped listing payload used to persist discovery artifacts.
    """

    model_config = ConfigDict(extra="allow")

    url: str = Field(description="Canonical detail-page URL for the job posting.")
    job_id: str = Field(
        description="Stable job identifier extracted from the listing URL."
    )
    listing_position: int | None = Field(
        default=None,
        description="Zero-based position of the listing card within the result page.",
    )
    search_url: str | None = Field(
        default=None,
        description="Listing-results URL that produced this discovery entry.",
    )
    listing_snippet: str | None = Field(
        default=None,
        description="Teaser text preserved as job-scoped listing evidence.",
    )
    listing_data: DiscoveryListingData = Field(
        default_factory=DiscoveryListingData,
        description="Structured listing-card teaser fields captured before detail extraction.",
    )
    listing_link: dict[str, Any] | None = Field(
        default=None,
        description="Raw link payload from Crawl4AI for traceability when available.",
    )
    source_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional source-specific metadata required for deterministic merges.",
    )
