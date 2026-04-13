"""Delphi rescue actor."""

from __future__ import annotations

from typing import Any, Dict

from src.automation.ariadne.core.periphery import Motor, Sensor
from src.automation.ariadne.models import AriadneState


class Delphi:
    """LLM next-step chooser when deterministic guidance is missing."""

    def __init__(
        self,
        sensor: Sensor,
        motor: Motor,
        labyrinth: Any = None,
        llm_client: Any = None,
    ) -> None:
        self.sensor = sensor
        self.motor = motor
        self.labyrinth = labyrinth
        self.llm_client = llm_client

    async def __call__(
        self,
        state: AriadneState,
        config: Any | None = None,
    ) -> Dict[str, Any]:
        """Run the current transitional next-step chooser path."""
        from src.automation.ariadne.graph.orchestrator import llm_rescue_agent_node

        return await llm_rescue_agent_node(state, config or {})
