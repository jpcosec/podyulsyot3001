"""Ariadne 2.0 Base Contracts — Primitive JIT Interfaces.

This module defines the backend-neutral protocols and primitive data models
for the Ariadne 2.0 architecture. These are the ONLY models that Executors
are allowed to import to maintain Dependency Inversion.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Protocol, Union

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


class SnapshotResult(BaseModel):
    """JIT Browser State (URL, DOM, Screenshot)."""

    url: str
    dom_elements: List[Dict[str, Any]] = Field(default_factory=list)
    screenshot_b64: Optional[str] = None


class ExecutionResult(BaseModel):
    """Outcome of a JIT execution."""

    status: Literal["success", "failed", "aborted"]
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    screenshot_path: Optional[str] = None


# --- Segregated Protocols ---


class Executor(Protocol):
    """Factory for executing JIT commands."""

    async def execute(self, command: MotorCommand) -> ExecutionResult:
        """Runs a JIT command or batch and returns the outcome."""
        ...

    async def take_snapshot(self) -> SnapshotResult:
        """Captures the current browser state."""
        ...


class Planner(Protocol):
    """Autonomous agent that proposes recovery actions."""

    async def plan_action(self, state: Any) -> Any:
        """Decides the next semantic action when the graph path is lost."""
        ...


class HintingTool(Protocol):
    """Capability to inject alphanumeric overlays on the DOM."""

    async def inject_hints(self, executor: Executor) -> Dict[str, Any]:
        """Injects hints and returns the ID-to-metadata mapping."""
        ...
