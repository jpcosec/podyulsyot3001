"""Automation contracts for candidate profiles and apply context payloads."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class CandidateProfile(BaseModel):
    """Candidate profile data resolved for one apply run."""

    model_config = ConfigDict(extra="allow")

    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    email: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    phone_country_code: str | None = Field(default=None)
