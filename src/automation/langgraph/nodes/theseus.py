"""Theseus — deterministic fast-path actor. Zero LLM cost.

Flow per turn:
  1. Identify room from snapshot (Labyrinth)
  2. Look up next step (Thread)
  3. Execute each item: Motor.act() for MotorCommand, Extractor.extract() for ExtractionAction
  4. Append TraceEvents and extracted_data to state
"""

from __future__ import annotations

import dataclasses
from typing import Optional

from src.automation.contracts.motor import Motor
from src.automation.contracts.extractor import Extractor
from src.automation.contracts.state import AriadneState
from src.automation.ariadne.labyrinth.labyrinth import Labyrinth
from src.automation.ariadne.thread.thread import AriadneThread
from src.automation.ariadne.thread.action import ExtractionAction


class TheseusNode:

    def __init__(
        self, motor: Motor, labyrinth: Labyrinth, thread: AriadneThread,
        extractor: Optional[Extractor] = None,
    ) -> None:
        self._motor = motor
        self._labyrinth = labyrinth
        self._thread = thread
        self._extractor = extractor

    async def __call__(self, state: AriadneState) -> dict:
        snapshot = state.get("snapshot")
        if not snapshot:
            return {"errors": ["TheseusError: no snapshot in state"]}
        room_id = self._labyrinth.identify_room(snapshot)
        if not room_id:
            return {"current_room_id": None}
        if self._is_terminal(room_id):
            return {"current_room_id": room_id, "is_mission_complete": True}
        step = self._thread.get_next_step(room_id)
        if not step:
            return {"current_room_id": room_id}
        return await self._execute_step(step, room_id, snapshot)

    async def _execute_step(self, step, room_id, snapshot) -> dict:
        trace, extracted = await self._run_actions(step, room_id, snapshot)
        errors = [e.error for e in trace if not e.success and e.error]
        result = {"current_room_id": room_id, "trace": trace, "errors": errors}
        if extracted:
            result["extracted_data"] = extracted
        return result

    async def _run_actions(self, step, room_id, snapshot) -> tuple:
        trace, extracted = [], []
        for item in step:
            if isinstance(item, ExtractionAction):
                extracted.extend(await self._extract(item, snapshot))
                continue
            event = await self._act(item, room_id)
            trace.append(event)
            if not event.success:
                break
        return trace, extracted

    async def _act(self, command, room_before: str):
        result = await self._motor.act(command)
        return dataclasses.replace(result.trace_event, room_before=room_before)

    async def _extract(self, action: ExtractionAction, snapshot) -> list[dict]:
        if not self._extractor:
            return []
        return await self._extractor.extract(action, snapshot)

    def _is_terminal(self, room_id: str) -> bool:
        room = self._labyrinth.get_room(room_id)
        return bool(room and room.state.is_terminal)
