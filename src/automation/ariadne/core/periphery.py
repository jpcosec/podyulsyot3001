"""Ariadne 2.0 Periphery — I/O Protocols and Adapters.

This module defines the boundaries between the cognitive layer (Ariadne)
and the physical world (The Browser). It uses Protocols to enforce
Dependency Inversion.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from src.automation.ariadne.contracts.base import (
    ExecutionResult,
    MotorCommand,
    SnapshotResult,
)


@runtime_checkable
class Sensor(Protocol):
    """Read-only browser perception contract.

    Abstract Methods:
    - perceive() -> SnapshotResult
    - is_healthy() -> bool
    """

    async def perceive(self) -> SnapshotResult:
        """Captures the current browser state (URL, DOM, Screenshot)."""
        ...

    async def is_healthy(self) -> bool:
        """Checks if the sensor is connected and responsive."""
        ...


@runtime_checkable
class Motor(Protocol):
    """Write-only browser mutation contract.

    Abstract Methods:
    - act(command: MotorCommand) -> ExecutionResult
    - is_healthy() -> bool
    """

    async def act(self, command: MotorCommand) -> ExecutionResult:
        """Executes a primitive action on the browser."""
        ...

    async def is_healthy(self) -> bool:
        """Checks if the motor is connected and responsive."""
        ...


class BrowserAdapter(ABC, Sensor, Motor):
    """Unified browser interface combining Sensor and Motor with lifecycle.

    Abstract Methods:
    - perceive() -> SnapshotResult
    - act(command: MotorCommand) -> ExecutionResult
    - is_healthy() -> bool
    - __aenter__() -> BrowserAdapter
    - __aexit__(exc_type, exc_val, exc_tb) -> None
    """

    @abstractmethod
    async def __aenter__(self) -> BrowserAdapter:
        """Initialize the browser session."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the browser session."""
        pass

    @abstractmethod
    async def perceive(self) -> SnapshotResult:
        """Captures the current browser state."""
        pass

    @abstractmethod
    async def act(self, command: MotorCommand) -> ExecutionResult:
        """Executes a primitive action."""
        pass

    async def is_healthy(self) -> bool:
        """Default health check implementation using a ping/poll strategy."""
        return True
