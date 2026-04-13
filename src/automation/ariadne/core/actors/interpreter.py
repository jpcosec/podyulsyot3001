"""Interpreter actor."""

from __future__ import annotations

from typing import Any, Dict

from src.automation.ariadne.core.cognition import (
    AriadneThread,
    Labyrinth,
    MapNotFoundError,
)
from src.automation.ariadne.models import AriadneState


class Interpreter:
    """Entry actor that resolves instructions into mission ids."""

    def __init__(
        self,
        labyrinth: Labyrinth,
        thread: AriadneThread,
    ) -> None:
        self.labyrinth = labyrinth
        self.thread = thread

    async def __call__(self, state: AriadneState) -> Dict[str, Any]:
        """Resolve the mission id for the current instruction."""
        instruction = state.get("instruction") or state.get("current_mission_id")
        if not instruction:
            return {}

        available = self.thread.available_missions()
        if instruction in available:
            return {"current_mission_id": instruction}

        if not available:
            raise MapNotFoundError(
                f"No missions available for portal '{state.get('portal_name', 'unknown')}'."
            )

        return {"current_mission_id": available[0]}
