"""PortalRegistry — lazy-load (Labyrinth, AriadneThread) per domain.

Shared by TheseusNode and RecorderNode so both operate on the same live objects.
Domains are auto-created on first access — no pre-configuration needed.
"""

from __future__ import annotations

from src.automation.ariadne.labyrinth.labyrinth import Labyrinth
from src.automation.ariadne.thread.thread import AriadneThread


class PortalRegistry:

    def __init__(self, mission_id: str) -> None:
        self._mission_id = mission_id
        self._portals: dict[str, tuple[Labyrinth, AriadneThread]] = {}

    def get(self, domain: str) -> tuple[Labyrinth, AriadneThread]:
        if domain not in self._portals:
            self._portals[domain] = (
                Labyrinth.load(domain),
                AriadneThread.load(domain, self._mission_id),
            )
        return self._portals[domain]

    def save(self, domain: str) -> None:
        if domain in self._portals:
            labyrinth, thread = self._portals[domain]
            labyrinth.save()
            thread.save()
