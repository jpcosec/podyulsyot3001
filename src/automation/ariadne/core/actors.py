"""Ariadne 2.0 Actors — LangGraph Node Handlers.

This module contains the functional actors (Theseus, Delphi, Recorder,
Interpreter) that represent the cognitive nodes of the Ariadne graph.
"""

from __future__ import annotations

from typing import Any, Dict

from src.automation.ariadne.core.cognition import AriadneThread, Labyrinth
from src.automation.ariadne.core.periphery import Motor, Sensor
from src.automation.ariadne.models import AriadneState


class Theseus:
    """The deterministic, low-cost executor actor.

    Responsibilities:
    - Perceive the current room via Sensor and Labyrinth.
    - Ask AriadneThread for the next mission-scoped step.
    - Execute the step via Motor.
    """

    def __init__(
        self,
        sensor: Sensor,
        motor: Motor,
        labyrinth: Labyrinth,
        thread: AriadneThread,
    ) -> None:
        """Initialize Theseus with its dependencies."""
        self.sensor = sensor
        self.motor = motor
        self.labyrinth = labyrinth
        self.thread = thread

    async def __call__(self, state: AriadneState) -> Dict[str, Any]:
        """Executes the deterministic path for the current state."""
        raise NotImplementedError("Theseus implementation is pending.")


class Delphi:
    """The LLM-based rescue and exploration actor.

    Responsibilities:
    - Use Vision/Reasoning to recover when Theseus is lost.
    - Choose high-level actions based on semantic clues.
    """

    def __init__(
        self,
        sensor: Sensor,
        motor: Motor,
        llm_client: Any = None,
    ) -> None:
        """Initialize Delphi with its dependencies."""
        self.sensor = sensor
        self.motor = motor
        self.llm_client = llm_client

    async def __call__(self, state: AriadneState) -> Dict[str, Any]:
        """Executes the LLM-driven rescue path."""
        raise NotImplementedError("Delphi implementation is pending.")


class Recorder:
    """The learning and assimilation actor.

    Responsibilities:
    - Observe outcomes of actions taken by Theseus or Delphi.
    - Update Labyrinth and AriadneThread with new discoveries.
    """

    def __init__(
        self,
        labyrinth: Labyrinth,
        thread: AriadneThread,
        trace_file: Any = None,
    ) -> None:
        """Initialize Recorder with its dependencies."""
        self.labyrinth = labyrinth
        self.thread = thread
        self.trace_file = trace_file

    async def __call__(self, state: AriadneState) -> Dict[str, Any]:
        """Assimilates the recent execution outcome into memory."""
        raise NotImplementedError("Recorder implementation is pending.")


class Interpreter:
    """The cognitive entry point of the Ariadne graph.

    Responsibilities:
    - Translate user instruction into mission_id.
    - Initialize AriadneState for the mission.
    """

    def __init__(
        self,
        labyrinth: Labyrinth,
        thread: AriadneThread,
    ) -> None:
        """Initialize Interpreter with its dependencies."""
        self.labyrinth = labyrinth
        self.thread = thread

    async def __call__(self, state: AriadneState) -> Dict[str, Any]:
        """Maps user intent to a specific mission and thread."""
        raise NotImplementedError("Interpreter implementation is pending.")
