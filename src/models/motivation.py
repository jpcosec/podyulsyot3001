from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class FitSignal(BaseModel):
    requirement: str
    evidence: str
    coverage: Literal["full", "partial"]


class MotivationLetterOutput(BaseModel):
    """Output contract matching the prompt specification."""

    subject: str
    salutation: str
    fit_signals: list[FitSignal]
    risk_notes: list[str] = Field(default_factory=list)
    letter_markdown: str


class EmailDraftOutput(BaseModel):
    """Agent-generated email draft."""

    to: str
    subject: str
    salutation: str
    body: str
    closing: str
    sender_name: str
    sender_email: str = ""
    sender_phone: str = ""
