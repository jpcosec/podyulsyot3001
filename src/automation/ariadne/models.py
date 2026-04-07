"""Ariadne Core Models — The Unified Semantic & Path Layer.

This module defines the backend-neutral models for automation:
1. Target Resolution (How to find elements)
2. Intent Vocabulary (What actions to perform)
3. Standardized Path (Linear sequences)
4. Semantic Layer (States, Tasks, and Goals)
5. Execution Contracts (JobPosting, ApplyMeta, etc.)
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


# --- Scrape Layer (Legacy/Portal Schema) ---


class ScrapePortalDefinition(BaseModel):
    """Motor-agnostic description of a portal's scrape interface."""

    source_name: str = Field(description="Unique portal identifier.")
    base_url: str = Field(description="Root URL for the portal.")
    supported_params: List[str] = Field(
        description="Query parameters supported by the scraper."
    )
    job_id_pattern: str = Field(description="Regex to extract unique job ID from URLs.")

    @field_validator("job_id_pattern")
    @classmethod
    def must_be_valid_regex(cls, v: str) -> str:
        re.compile(v)
        return v


class JobPosting(BaseModel):
    """Standardized extraction output contract for all scraping sources."""

    # Mandatory
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
        description="List of responsibilities or tasks. Extract as short action phrases.",
    )
    requirements: List[str] = Field(
        ..., min_length=1, description="List of requirements, profile or skills."
    )

    # Optional
    salary: Optional[str] = Field(
        default=None, description="Estimated salary or salary range."
    )
    remote_policy: Optional[str] = Field(
        default=None, description="Remote work policy (On-site, Hybrid, 100% Remote)."
    )
    benefits: List[str] = Field(
        default_factory=list, description="Extra benefits offered."
    )
    company_description: Optional[str] = Field(
        default=None, description="Short description of the company."
    )
    company_industry: Optional[str] = Field(
        default=None, description="Sector or industry."
    )
    company_size: Optional[str] = Field(default=None, description="Company size.")
    posted_date: Optional[str] = Field(
        default=None, description="Date of publication (ISO timestamp preferred)."
    )
    days_ago: Optional[str] = Field(
        default=None, description="Relative publication age."
    )
    application_deadline: Optional[str] = Field(
        default=None, description="Deadline to apply."
    )
    application_method: Optional[str] = Field(
        default=None, description="How to apply (e.g. 'email', 'external portal')."
    )
    application_url: Optional[str] = Field(
        default=None, description="Direct application URL or apply button target."
    )
    application_email: Optional[str] = Field(
        default=None, description="Application email address."
    )
    application_instructions: Optional[str] = Field(
        default=None, description="Short instructions on how to apply."
    )
    reference_number: Optional[str] = Field(
        default=None, description="Internal reference code for the posting."
    )
    contact_info: Optional[str] = Field(
        default=None, description="Email or contact person for application."
    )
    original_language: Optional[str] = Field(
        default=None, description="The detected ISO 639-1 language code."
    )


# --- Target Layer ---


class AriadneTarget(BaseModel):
    """Multi-strategy element descriptor. Each motor uses what it understands."""

    css: Optional[str] = Field(
        default=None, description="CSS selector for Crawl4AI/Playwright"
    )
    text: Optional[str] = Field(
        default=None, description="Fuzzy text match for BrowserOS"
    )
    image_template: Optional[str] = Field(
        default=None, description="OpenCV template path for Vision"
    )
    ocr_text: Optional[str] = Field(
        default=None, description="OCR text region for Vision fallback"
    )
    region: Optional[Dict[str, int]] = Field(
        default=None, description="Bounding box {x, y, w, h}"
    )


# --- Intent Layer ---


class AriadneIntent(str, Enum):
    """The 'What to do' — backend-neutral action vocabulary."""

    CLICK = "click"
    FILL = "fill"
    FILL_REACT = "fill_react_controlled"
    SELECT = "select"
    UPLOAD = "upload"
    UPLOAD_LETTER = "upload_letter"
    PRESS_KEY = "press_key"
    SCROLL = "scroll"
    WAIT = "wait"
    NAVIGATE = "navigate"


class AriadneAction(BaseModel):
    """An atomic interaction with a target."""

    intent: AriadneIntent
    target: Optional[AriadneTarget] = None
    value: Optional[str] = Field(
        default=None, description="Value with {{placeholders}}"
    )
    fallback: Optional[AriadneAction] = None
    optional: bool = False
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Motor-specific hyperparameters (e.g., fuzzy_threshold, js_code)",
    )


# --- Observation Layer ---


class AriadneObserve(BaseModel):
    """Predicate to identify a state or confirm a result."""

    required_elements: List[AriadneTarget] = Field(default_factory=list)
    forbidden_elements: List[AriadneTarget] = Field(default_factory=list)
    logical_op: Literal["AND", "OR"] = "AND"


# --- Semantic Layer ---


class AriadneState(BaseModel):
    """A semantic 'Room' in the portal (e.g., Login Page, Contact Info Modal)."""

    id: str
    description: str
    presence_predicate: AriadneObserve

    # Components that compose this page/state
    components: Dict[str, AriadneTarget] = Field(default_factory=dict)

    # Possible actions leading to other states
    transitions: Dict[str, str] = Field(
        default_factory=dict, description="Mapping of action_id -> next_state_id"
    )


class AriadneRecoveryPlan(BaseModel):
    """Standardized recovery steps for known blockers (e.g., Cookie Banners)."""

    trigger_predicate: AriadneObserve
    recovery_actions: List[AriadneAction]
    resume_strategy: Literal["RETRY_STEP", "RESTART_FLOW", "ABORT"] = "RETRY_STEP"


class AriadneTask(BaseModel):
    """The 'Mission' (e.g., Submit Application). Defines success/failure boundaries."""

    id: str
    goal: str
    entry_state: str

    success_states: List[str] = Field(
        description="State IDs that signal mission success"
    )
    failure_states: List[str] = Field(
        description="State IDs that signal terminal failure"
    )

    success_criteria: Dict[str, Any] = Field(
        default_factory=dict,
        description="Verification rules (e.g., {'text_match': 'Application sent'})",
    )

    # Recovery for blockers like captchas or popups
    blocker_recovery: List[AriadneRecoveryPlan] = Field(default_factory=list)


# --- Path Layer ---


class AriadneStep(BaseModel):
    """One sequential unit of a path traversal."""

    step_index: int
    name: str
    description: str

    # Semantic Context
    state_id: Optional[str] = None

    # Execution
    observe: AriadneObserve
    actions: List[AriadneAction]

    # Flow Control
    next_step_index: Optional[int] = None
    human_required: bool = False
    dry_run_stop: bool = False
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Step-level motor hyperparameters (e.g., wait_for_network, enhanced_snapshot)",
    )


class AriadnePath(BaseModel):
    """A linear 'Tape' through a task, used by deterministic replayers."""

    id: str
    task_id: str
    steps: List[AriadneStep]
    metadata: Dict[str, str] = Field(default_factory=dict)


# --- The Unified Map ---


class AriadnePortalMap(BaseModel):
    """The 'One Map' per portal flow, containing all semantics and paths."""

    portal_name: str = Field(
        description="Unique identifier for the portal (e.g., 'linkedin')."
    )
    base_url: str = Field(description="The starting URL for automation on this portal.")

    # Semantic Registry
    states: Dict[str, AriadneState] = Field(
        description="Registry of semantic states (rooms) identified by their unique ID."
    )
    tasks: Dict[str, AriadneTask] = Field(
        description="Registry of mission goals and their success/failure boundaries."
    )

    # Path Registry (Deterministic sequences)
    paths: Dict[str, AriadnePath] = Field(
        description="Registry of linear step sequences indexed by path ID."
    )

    # Global/Cross-State components
    global_components: Dict[str, AriadneTarget] = Field(
        default_factory=dict,
        description="Reusable targets that appear across multiple states (e.g., Logout button).",
    )


# --- Execution Contracts ---


class ApplicationRecord(BaseModel):
    """Persisted record of one apply attempt for a specific job."""

    source: str = Field(description="The portal source name.")
    job_id: str = Field(description="Unique identifier for the job.")
    job_title: str = Field(description="Title of the job applied for.")
    company_name: str = Field(description="Name of the company.")
    application_url: str = Field(description="URL used for the application.")
    cv_path: str = Field(description="Local path to the CV used.")
    letter_path: Optional[str] = Field(
        default=None, description="Local path to the cover letter if used."
    )
    fields_filled: List[str] = Field(
        default_factory=list,
        description="List of semantic fields/components interacted with.",
    )
    dry_run: bool = Field(description="Whether this was a dry-run.")
    submitted_at: Optional[str] = Field(
        default=None, description="ISO timestamp of submission."
    )
    confirmation_text: Optional[str] = Field(
        default=None, description="Success text fragment captured after submission."
    )


class ApplyMeta(BaseModel):
    """Small status artifact describing the outcome of an apply run."""

    status: Literal["submitted", "dry_run", "failed", "portal_changed"] = Field(
        description="Final outcome status."
    )
    timestamp: str = Field(description="ISO timestamp of the attempt.")
    error: Optional[str] = Field(default=None, description="Error message if failed.")


# Rebuild models to resolve forward references
AriadneAction.model_rebuild()
AriadneStep.model_rebuild()
AriadnePath.model_rebuild()
AriadnePortalMap.model_rebuild()
