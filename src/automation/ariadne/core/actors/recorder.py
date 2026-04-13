"""Recorder actor."""

from __future__ import annotations

from typing import Any, Dict

from src.automation.ariadne.capabilities.recording import GraphRecorder
from src.automation.ariadne.core.cognition import AriadneThread, Labyrinth
from src.automation.ariadne.models import AriadneState
from src.automation.ariadne.promotion import AriadnePromoter


class Recorder:
    """Recorder actor for trace persistence and promotion."""

    def __init__(
        self,
        labyrinth: Labyrinth,
        thread: AriadneThread,
        recorder: GraphRecorder | None = None,
        promoter: AriadnePromoter | None = None,
    ) -> None:
        self.labyrinth = labyrinth
        self.thread = thread
        self.recorder = recorder or GraphRecorder()
        self.promoter = promoter or AriadnePromoter()

    async def __call__(
        self,
        state: AriadneState,
        config: Any | None = None,
    ) -> Dict[str, Any]:
        """Persist a lightweight graph event if recording is enabled."""
        configurable = (config or {}).get("configurable", {})
        if not configurable.get("record_graph"):
            return {}

        thread_id = configurable.get("thread_id")
        if not thread_id:
            return {}

        payload = {
            "portal_name": state.get("portal_name"),
            "current_mission_id": state.get("current_mission_id"),
            "current_state_id": state.get("current_state_id"),
            "errors": state.get("errors", []),
        }
        await self.recorder.record_event_async(thread_id, "graph_state", payload)
        return {}

    def promote(self, thread_id: str):
        """Promote a recorded thread into a draft map."""
        return self.promoter.promote_thread(thread_id)
