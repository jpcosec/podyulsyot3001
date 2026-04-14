"""Interpreter — resolves a raw instruction into mission_id + portal_name.

Entry point of the graph. Seeds the state before any browser interaction.
"""

from __future__ import annotations

from src.automation.contracts.state import AriadneState


class InterpreterNode:
    """
    For now: parses instruction as "portal_name/mission_id".
    Replace with LLM-based resolution when instruction format grows complex.
    """

    async def __call__(self, state: AriadneState) -> dict:
        instruction = state.get("instruction", "")
        portal_name, mission_id = _parse(instruction)
        return {
            "portal_name": portal_name,
            "mission_id": mission_id,
            "current_room_id": None,
            "snapshot": None,
            "agent_failures": 0,
        }


def _parse(instruction: str) -> tuple[str, str]:
    """Expects 'portal_name/mission_id'. Falls back gracefully."""
    parts = instruction.strip().split("/", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return instruction.strip(), "default"
