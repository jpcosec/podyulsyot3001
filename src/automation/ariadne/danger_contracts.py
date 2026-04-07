"""Danger detection contracts for apply-time safety guards.

These models define the shared signal bundle and normalized findings used by
apply-time danger detection across Ariadne and the deterministic motors.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DangerAction = Literal["pause", "abort"]
DangerSource = Literal["dom_text", "screenshot", "routing", "submission_state"]


class ApplyDangerSignals(BaseModel):
    """Collected evidence that can reveal risky apply-flow states."""

    dom_text: str | None = Field(
        default=None,
        description="Visible DOM or snapshot text captured from the live page.",
    )
    screenshot_text: str | None = Field(
        default=None,
        description="OCR or operator-extracted text captured from a screenshot.",
    )
    current_url: str | None = Field(
        default=None,
        description="Current browser URL observed during the apply run.",
    )
    application_url: str | None = Field(
        default=None,
        description="Expected onsite application URL for the current apply run.",
    )
    route_outcome: str | None = Field(
        default=None,
        description="Resolved routing outcome before execution begins.",
    )
    route_reason: str | None = Field(
        default=None,
        description="Human-readable explanation attached to the routing decision.",
    )
    already_submitted: bool = Field(
        default=False,
        description="Whether storage already marks the job as successfully submitted.",
    )


class ApplyDangerFinding(BaseModel):
    """One normalized danger signal derived from apply-time evidence."""

    code: str = Field(description="Stable machine-readable danger code.")
    source: DangerSource = Field(description="Signal source that produced the match.")
    recommended_action: DangerAction = Field(
        description="Default control action suggested for this danger."
    )
    message: str = Field(description="Operator-readable explanation of the risk.")
    matched_text: str | None = Field(
        default=None,
        description="Specific text fragment that triggered the detector, when available.",
    )


class ApplyDangerReport(BaseModel):
    """Normalized set of danger findings for one apply-time inspection."""

    findings: list[ApplyDangerFinding] = Field(
        default_factory=list,
        description="All normalized findings detected for the current page or route.",
    )

    @property
    def primary(self) -> ApplyDangerFinding | None:
        """Return the highest-priority finding, if any."""
        return self.findings[0] if self.findings else None
