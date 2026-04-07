"""Automation contracts for candidate profiles and apply context payloads.

This module defines the typed boundary shared by the CLI, storage layer, and
runtime orchestration when candidate profile data is injected into apply runs.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CandidateProfile(BaseModel):
    """Candidate profile data resolved for one apply run.

    Args:
        first_name: Candidate given name.
        last_name: Candidate family name.
        email: Preferred contact email.
        phone: Preferred contact phone number.
        phone_country_code: Phone country prefix when portals split the field.

    Returns:
        A validated candidate profile that preserves additional portal-specific
        fields for later reuse.
    """

    model_config = ConfigDict(extra="allow")

    first_name: str | None = Field(
        default=None,
        description="Candidate first name, for example 'Juan Pablo'.",
    )
    last_name: str | None = Field(
        default=None,
        description="Candidate last name, for example 'Ruiz'.",
    )
    email: str | None = Field(
        default=None,
        description="Candidate contact email, for example 'jp@example.com'.",
    )
    phone: str | None = Field(
        default=None,
        description="Candidate phone number in the preferred submit format.",
    )
    phone_country_code: str | None = Field(
        default=None,
        description="Optional phone country code when the portal asks separately.",
    )


class ApplyJobContext(BaseModel):
    """Subset of ingest data exposed to apply motors.

    Args:
        job_title: Job title shown in the listing.
        company_name: Employer name shown in the listing.
        application_url: URL used to open the apply flow.

    Returns:
        A normalized job context payload for execution.
    """

    job_title: str = Field(
        default="",
        description="Job title from ingest state, for example 'Backend Engineer'.",
    )
    company_name: str = Field(
        default="",
        description="Company name from ingest state, for example 'Acme GmbH'.",
    )
    application_url: str = Field(
        default="",
        description="Direct apply URL or fallback listing URL for the run.",
    )


class ExecutionContext(BaseModel):
    """Normalized apply context shared with motors.

    Args:
        profile: Candidate profile available for placeholder resolution.
        job: Job-level ingest context for the current application.
        cv_path: Local path to the CV used in the run.
        letter_path: Optional local path to the cover letter.

    Returns:
        A typed execution payload ready to be serialized for runtime use.
    """

    profile: CandidateProfile = Field(
        description="Candidate profile used to resolve runtime placeholders."
    )
    job: ApplyJobContext = Field(
        description="Job metadata required by apply motors during replay."
    )
    cv_path: str = Field(description="Filesystem path to the CV artifact.")
    letter_path: str | None = Field(
        default=None,
        description="Filesystem path to the cover letter artifact when provided.",
    )

    def to_runtime_dict(self) -> dict[str, Any]:
        """Return the execution payload in the dict shape motors consume.

        Args:
            None.

        Returns:
            A plain Python dict with normalized profile and job data.
        """

        return self.model_dump(mode="python")
