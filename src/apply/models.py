"""Pydantic models for the apply module.

Spec reference: docs/superpowers/specs/2026-03-30-apply-module-design.md Section 3
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class FormSelectors(BaseModel):
    """CSS selectors the adapter validates against the live DOM before interaction.

    Mandatory selectors (apply_button, cv_upload, submit_button, success_indicator):
    absence raises PortalStructureChangedError.

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
    cv_select_existing: str | None = None  # portals that prefer selecting a saved CV


class ApplicationRecord(BaseModel):
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
    status: Literal["submitted", "dry_run", "failed", "portal_changed"]
    timestamp: str
    error: str | None = None
