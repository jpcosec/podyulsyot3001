"""Theseus — deterministic fast-path actor. Zero LLM cost.

Flow per turn:
  1. Identify room from snapshot (Labyrinth)
  2. Look up next step (Thread)
  3. Execute each command (Motor)
  4. Append TraceEvents to state
"""

from __future__ import annotations

import dataclasses

from src.automation.contracts.motor import Motor
from src.automation.contracts.state import AriadneState
from src.automation.ariadne.labyrinth.labyrinth import Labyrinth
from src.automation.ariadne.thread.thread import AriadneThread


class TheseusNode:

    def __init__(self, motor: Motor, labyrinth: Labyrinth, thread: AriadneThread) -> None:
        self._motor = motor
        self._labyrinth = labyrinth
        self._thread = thread

    async def __call__(self, state: AriadneState) -> dict:
        snapshot = state.get("snapshot")
        if not snapshot:
            return {"errors": ["TheseusError: no snapshot in state"]}

        room_id = self._labyrinth.identify_room(snapshot)
        if not room_id:
            return {"current_room_id": None}

        if self._is_terminal(room_id):
            return {"current_room_id": room_id, "is_mission_complete": True}

        commands = self._thread.get_next_step(room_id)
        if not commands:
            return {"current_room_id": room_id}  # room known, no step → cold path

        trace_events = await self._execute_commands(commands, room_id)
        errors = [e.error for e in trace_events if not e.success and e.error]
        return {
            "current_room_id": room_id,
            "trace": trace_events,
            "errors": errors,
        }

    def _is_terminal(self, room_id: str) -> bool:
        room = self._labyrinth.get_room(room_id)
        return bool(room and room.state.is_terminal)

    async def _execute_commands(self, commands, room_before: str) -> list:
        events = []
        for command in commands:
            result = await self._motor.act(command)
            event = dataclasses.replace(result.trace_event, room_before=room_before)
            events.append(event)
            if not result.success:
                break  # abort sequence on first failure
        return events
