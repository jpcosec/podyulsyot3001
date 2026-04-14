"""Sensor contract — read-only perception of the browser state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class SnapshotResult:
    """
    A single immutable observation of the browser at one point in time.

    Produced by Sensor.perceive(). Consumed by Theseus (room identification)
    and Delphi (raw HTML + screenshot for LLM reasoning). One snapshot per
    graph turn — never fetch twice in the same turn.
    """

    url: str
    html: str
    screenshot_b64: str | None = None  # base64 PNG — only when Delphi needs it
    links: list[str] = field(default_factory=list)  # internal URLs discovered
    status_code: int = 200


@runtime_checkable
class Sensor(Protocol):
    """Read-only view of the browser. Implementations must be async-safe."""

    async def perceive(self) -> SnapshotResult: ...
    async def is_healthy(self) -> bool: ...
