"""Ariadne 2.0 Core Models — Graph-based Semantic Navigation.

This module defines the models for the Programmable Semantic Browser:
1. AriadneMap (The directed state graph)
2. AriadneStateDefinition (The state nodes)
3. AriadneEdge (The transitions)
4. AriadneTarget (Multi-strategy element identification)
5. AriadneState (The immutable working memory/LangGraph state)
6. Execution Contracts (Executors and Results)
"""

from __future__ import annotations

import operator
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict, Union

from langgraph.graph.message import AnyMessage, add_messages
from pydantic import BaseModel, Field


# --- Target Layer ---


class AriadneTarget(BaseModel):
    """Multi-strategy element descriptor with Priority for Hinting."""

    hint: Optional[str] = Field(
        default=None, description="Alphanumeric marker (e.g. 'AA', 'AB') injected JIT."
    )
    css: Optional[str] = Field(
        default=None, description="Fallback CSS selector."
    )
    text: Optional[str] = Field(
        default=None, description="Fuzzy text match."
    )
    vision: Optional[Dict[str, int]] = Field(
        default=None, description="Coordinates {x, y, w, h} from VisionTool."
    )


# --- Intent Layer ---


class AriadneIntent(str, Enum):
    """Semantic 'What to do' vocabulary."""

    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    UPLOAD = "upload"
    WAIT = "wait"
    PRESS = "press"
    EXTRACT = "extract"


# --- Observation Layer ---


class AriadneObserve(BaseModel):
    """Predicate to identify a State Node."""

    required_elements: List[AriadneTarget] = Field(default_factory=list)
    forbidden_elements: List[AriadneTarget] = Field(default_factory=list)
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
    current_state_id: str

    # JIT Browser Snapshot
    dom_elements: List[Dict[str, Any]]
    current_url: str
    screenshot_b64: Optional[str]

    # session_memory: Read-write memory for extractions (e.g. Application IDs)
    session_memory: Dict[str, Any]

    # Memory & Reducers
    errors: Annotated[List[str], operator.add]
    history: Annotated[List[AnyMessage], add_messages]

    # Active Strategy (Injected via URL context)
    portal_mode: str


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


# --- Execution Interfaces (JIT Payloads) ---


class MotorCommand(BaseModel):
    """Base class for JIT motor instructions."""

    pass


class BrowserOSCommand(MotorCommand):
    """Single MCP tool call for BrowserOS CLI."""

    tool: Literal["click", "fill", "upload", "press"]
    selector_text: str
    value: Optional[str] = None


class CrawlCommand(MotorCommand):
    """One or more C4A-Script actions for Crawl4AI."""

    c4a_script: str
    hooks: List[Dict[str, Any]] = Field(default_factory=list)


class ScriptCommand(MotorCommand):
    """Command to execute arbitrary JavaScript and extract results."""

    script: str


class ExecutionResult(BaseModel):
    """Outcome of a JIT execution."""

    status: Literal["success", "failed", "aborted"]
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    screenshot_path: Optional[str] = None


# Rebuild models to resolve forward references
AriadneMap.model_rebuild()
AriadneEdge.model_rebuild()
