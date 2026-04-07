"""Portal routing contracts shared by portal-specific routing modules.

This module defines the small routing DTO that portal packages return after
inspecting enriched ingest state. The result tells Ariadne whether the apply
run should continue on the portal, hand off to an external ATS, or stop for
an email-based workflow.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PortalRoutingResult(BaseModel):
    """Decision produced by a portal routing module for one job."""

    outcome: Literal["onsite", "external_url", "email", "unsupported"] = Field(
        description="Resolved routing outcome for the current job."
    )
    path_id: str | None = Field(
        default=None,
        description="Ariadne path to execute when the outcome stays onsite.",
    )
    application_url: str | None = Field(
        default=None,
        description="Resolved URL that should be opened for the apply flow.",
    )
    application_email: str | None = Field(
        default=None,
        description="Resolved email address when the job requests email submission.",
    )
    reason: str = Field(
        description="Human-readable explanation of why the route was selected."
    )
    diagnostics: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured hints explaining the portal-specific route decision.",
    )
