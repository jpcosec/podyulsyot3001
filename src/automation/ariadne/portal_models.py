"""Ariadne portal schema — motor-agnostic portal intent models.

These models express WHAT a portal offers and expects. Motors translate
these definitions into their own execution language (CSS selectors,
C4A-Script, BrowserOS tool calls, etc.).
"""
from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, field_validator


class FieldType(str, Enum):
    """Motor-agnostic form field types."""

    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    FILE_PDF = "file_pdf"


class FormField(BaseModel):
    """One form field in motor-agnostic terms."""

    name: str
    label: str
    required: bool
    field_type: FieldType


class ApplyStep(BaseModel):
    """One step in an application flow, motor-agnostic."""

    name: str
    description: str
    fields: list[FormField]
    dry_run_stop: bool = False


class ApplyPortalDefinition(BaseModel):
    """Motor-agnostic description of a portal's apply flow."""

    source_name: str
    base_url: str
    entry_description: str
    steps: list[ApplyStep]


class ScrapePortalDefinition(BaseModel):
    """Motor-agnostic description of a portal's scrape interface."""

    source_name: str
    base_url: str
    supported_params: list[str]
    job_id_pattern: str

    @field_validator("job_id_pattern")
    @classmethod
    def must_be_valid_regex(cls, v: str) -> str:
        re.compile(v)
        return v
