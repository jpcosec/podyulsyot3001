"""Motor contract — write-only execution of actions on the browser."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable


@dataclass(frozen=True)
class MotorCommand:
    """
    A single primitive instruction to the browser.

    Intentionally low-level — one selector, one operation.
    Higher-level action composition (TransitionAction sequences) happens
    in the Thread layer, not here.
    """

    operation: Literal["navigate", "click", "fill", "submit", "scroll", "extract", "wait"]
    selector: str
    value: str | None = None          # for fill / extract schema id
    wait_for: str | None = None       # CSS or JS condition to wait after acting
    session_id: str | None = None     # propagated from AriadneState


@dataclass(frozen=True)
class TraceEvent:
    """
    A record of one executed command. Appended to AriadneState.trace.
    Consumed by Recorder to expand Labyrinth and Thread.
    """

    command: MotorCommand
    success: bool
    room_before: str | None = None    # room_id before the action
    room_after: str | None = None     # room_id after (None until Observe confirms)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionResult:
    """What Motor.act() returns after running a MotorCommand."""

    success: bool
    trace_event: TraceEvent
    error: str | None = None


@runtime_checkable
class Motor(Protocol):
    """Write-only interface to the browser. Never reads state."""

    async def act(self, command: MotorCommand) -> ExecutionResult: ...
