"""Segregated Motor Protocols for Ariadne 2.0.

This module defines the Just-In-Time (JIT) interfaces for navigation and execution,
satisfying the Interface Segregation Principle (ISP) and Dependency Inversion Principle (DIP).
"""

from __future__ import annotations

import operator
from typing import (
    Annotated,
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    TypedDict,
    Union,
    runtime_checkable,
)

from langgraph.graph.message import AnyMessage, add_messages

from src.automation.ariadne.models import (
    AriadneEdge,
    AriadneState,
    AriadneTarget,
    ExecutionResult,
    MotorCommand,
)


@runtime_checkable
class Executor(Protocol):
    """Protocol for 'dumb slave' execution units."""

    async def execute(self, command: MotorCommand) -> ExecutionResult:
        """Execute a JIT motor instruction."""
        ...


@runtime_checkable
class Planner(Protocol):
    """Protocol for intelligence units that interpret state and decide actions."""

    async def plan_action(self, state: AriadneState) -> List[AriadneEdge]:
        """Infer the next semantic action(s) based on current state."""
        ...


@runtime_checkable
class VisionTool(Protocol):
    """Protocol for coordinate-based element identification."""

    async def locate(
        self, target: AriadneTarget, screenshot_b64: str
    ) -> Optional[Dict[str, int]]:
        """Identify coordinates {x, y, w, h} for a target using Vision."""
        ...


@runtime_checkable
class HintingTool(Protocol):
    """Protocol for alphanumeric marker injection and resolution."""

    async def inject_hints(self) -> Dict[str, str]:
        """Inject alphanumeric markers into the DOM and return marker -> ID map."""
        ...

    async def resolve_hint(self, hint: str) -> Optional[AriadneTarget]:
        """Translate a marker (e.g. 'AA') back into a semantic target."""
        ...
