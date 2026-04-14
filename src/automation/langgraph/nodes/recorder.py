"""Recorder — silent assimilation node. Does not decide flow.

Reads state["trace"], updates Labyrinth and Thread, persists both to disk.
Called after every successful execution turn (Theseus or Delphi).
"""

from __future__ import annotations

from src.automation.contracts.state import AriadneState
from src.automation.ariadne.labyrinth.labyrinth import Labyrinth
from src.automation.ariadne.thread.thread import AriadneThread


class RecorderNode:

    def __init__(self, labyrinth: Labyrinth, thread: AriadneThread) -> None:
        self._labyrinth = labyrinth
        self._thread = thread

    async def __call__(self, state: AriadneState) -> dict:
        trace = state.get("trace", [])
        room_after = state.get("current_room_id")

        for event in trace:
            if event.success and room_after:
                self._thread.add_step(event, room_after)

        if trace:
            self._thread.save()
            self._labyrinth.save()

        return {}  # Recorder never mutates state — side effects only
