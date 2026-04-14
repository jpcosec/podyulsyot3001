"""Observe — one DOM read per turn, shared by Theseus and Delphi.

Never called twice in the same turn. Theseus and Delphi read from
state["snapshot"], they do not call perceive() themselves.
Emits `domain` (netloc of current URL) so downstream nodes can load
the correct Labyrinth/Thread from PortalRegistry.
"""

from __future__ import annotations

from urllib.parse import urlparse

from src.automation.contracts.sensor import Sensor
from src.automation.contracts.state import AriadneState

_NEEDS_SCREENSHOT_AFTER_N_FAILURES = 1  # Delphi needs screenshot from the first cold-path attempt


class ObserveNode:

    def __init__(self, sensor: Sensor) -> None:
        self._sensor = sensor

    async def __call__(self, state: AriadneState) -> dict:
        if not await self._sensor.is_healthy():
            return {"errors": ["FatalError: sensor disconnected"]}

        with_screenshot = state.get("agent_failures", 0) >= _NEEDS_SCREENSHOT_AFTER_N_FAILURES
        snapshot = await self._sensor.perceive(with_screenshot=with_screenshot)
        domain = _domain_from_url(snapshot.url)
        return {"snapshot": snapshot, "domain": domain}


def _domain_from_url(url: str) -> str:
    netloc = urlparse(url).netloc
    return netloc.removeprefix("www.") or "unknown"
