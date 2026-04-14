"""Recorder — silent assimilation node. Does not decide flow.

Reads state["trace"], updates Labyrinth and Thread for the current domain,
persists both to disk. Called after every successful execution turn.
Domain is derived from state["domain"] so cross-domain navigation is handled
automatically — each domain gets its own Labyrinth and Thread.
"""

from __future__ import annotations

from src.automation.contracts.state import AriadneState
from src.automation.ariadne.portal_registry import PortalRegistry


class RecorderNode:

    def __init__(self, registry: PortalRegistry) -> None:
        self._registry = registry

    async def __call__(self, state: AriadneState) -> dict:
        trace = state.get("trace", [])
        room_after = state.get("current_room_id")
        domain = state.get("domain", state.get("portal_name", ""))

        if not domain or not trace:
            return {}

        _, thread = self._registry.get(domain)
        for event in trace:
            if event.success and room_after:
                thread.add_step(event, room_after)

        self._registry.save(domain)
        return {}  # Recorder never mutates state — side effects only
