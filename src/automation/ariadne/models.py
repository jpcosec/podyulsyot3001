"""Ariadne 2.0 Core Models — Graph-based Semantic Navigation.

This module defines the models for the Programmable Semantic Browser:
1. AriadneMap (The directed state graph)
2. AriadneStateDefinition (The state nodes)
3. AriadneEdge (The transitions)
4. AriadneState (The immutable working memory/LangGraph state)
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict, Union

from langgraph.graph.message import AnyMessage, add_messages
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.automation.ariadne.contracts.base import (
    AriadneIntent,
    AriadneTarget,
)


# --- Extraction Models ---


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
        default_factory=list,
        description="List of responsibilities or tasks.",
    )
    requirements: List[str] = Field(
        default_factory=list, description="List of requirements, profile or skills."
    )

    @field_validator("requirements")
    @classmethod
    def must_have_some_content(cls, v: List[str], info: Any) -> List[str]:
        responsibilities = info.data.get("responsibilities", [])
        if not v and not responsibilities:
            raise ValueError(
                "JobPosting must have at least one responsibility or requirement."
            )
        return v

    # Optional
    salary: Optional[str] = Field(default=None)
    remote_policy: Optional[str] = Field(default=None)
    benefits: List[str] = Field(default_factory=list)
    company_description: Optional[str] = Field(default=None)
    company_industry: Optional[str] = Field(default=None)
    company_size: Optional[str] = Field(default=None)
    posted_date: Optional[str] = Field(default=None)
    days_ago: Optional[str] = Field(default=None)
    application_deadline: Optional[str] = Field(default=None)
    application_method: Optional[str] = Field(default=None)
    application_url: Optional[str] = Field(default=None)
    application_email: Optional[str] = Field(default=None)
    application_instructions: Optional[str] = Field(default=None)
    reference_number: Optional[str] = Field(default=None)
    contact_info: Optional[str] = Field(default=None)
    original_language: Optional[str] = Field(default=None)


# --- Observation Layer ---


class AriadneObserve(BaseModel):
    """Predicate to identify a State Node."""

    required_elements: List[AriadneTarget] = Field(default_factory=list)
    forbidden_elements: List[AriadneTarget] = Field(default_factory=list)
    url_contains: Optional[str] = Field(
        default=None, description="Current URL must contain this substring."
    )
    logical_op: Literal["AND", "OR"] = "AND"


# --- State Graph Models ---


class AriadneStateDefinition(BaseModel):
    """A Node in the Directed State Graph."""

    id: str
    description: str
    presence_predicate: AriadneObserve
    components: Dict[str, AriadneTarget] = Field(default_factory=dict)


class AriadneEdge(BaseModel):
    """A directed Transition between States."""

    from_state: str
    to_state: str
    mission_id: Optional[str] = Field(
        default=None,
        description="Optional mission gate for this edge, such as 'easy_apply' or 'discovery'.",
    )
    intent: AriadneIntent
    target: Union[str, AriadneTarget]  # Component name or explicit target
    value: Optional[str] = Field(
        default=None, description="Value with {{placeholders}} from AriadneState."
    )
    extract: Optional[Dict[str, str]] = Field(
        default=None, description="Map of key -> selector for session_memory writes."
    )


class AriadneState(TypedDict):
    """The immutable, serializable working memory of the Ariadne Graph."""

    # Identity
    job_id: str
    portal_name: str

    # Context (Static injection)
    profile_data: Dict[str, Any]
    job_data: Dict[str, Any]

    # Navigation Pointer
    path_id: Optional[str]
    current_mission_id: Optional[str]
    current_state_id: str

    # JIT Browser Snapshot
    dom_elements: List[Dict[str, Any]]
    current_url: str
    screenshot_b64: Optional[str]

    # session_memory: Read-write memory for extractions (e.g. Application IDs)
    session_memory: Dict[str, Any]

    # Memory & Reducers
    errors: List[str]
    history: Annotated[List[AnyMessage], add_messages]

    # Active Strategy (Injected via URL context)
    portal_mode: str

    # JIT Patches (keyed as "state_id:component_name")
    patched_components: Annotated[Dict[str, AriadneTarget], operator.ior]


class AriadneMapMeta(BaseModel):
    """Metadata for an AriadneMap."""

    source: str
    flow: str
    version: str = "v1"
    status: Literal["draft", "verified", "canonical"] = "draft"


class AriadneMap(BaseModel):
    """The directed State Graph representing a portal flow."""

    meta: AriadneMapMeta
    states: Dict[str, AriadneStateDefinition] = Field(
        description="Registry of state nodes identified by their unique ID."
    )
    edges: List[AriadneEdge] = Field(
        description="List of directed transitions between states."
    )
    success_states: List[str] = Field(
        description="State IDs that signal mission success."
    )
    failure_states: List[str] = Field(
        description="State IDs that signal terminal failure."
    )


# Rebuild models to resolve forward references
AriadneMap.model_rebuild()
AriadneEdge.model_rebuild()
