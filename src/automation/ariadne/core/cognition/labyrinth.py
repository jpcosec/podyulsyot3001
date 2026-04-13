"""Labyrinth topology model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.automation.ariadne.contracts.base import AriadneTarget, SnapshotResult
from src.automation.ariadne.exceptions import MapNotFoundError
from src.automation.ariadne.models import AriadneMap, AriadneObserve
from src.automation.ariadne.repository import MapRepository


def _matches_target(target: AriadneTarget, snapshot: SnapshotResult) -> bool:
    elements = snapshot.dom_elements or []
    for element in elements:
        if target.css and element.get("css") == target.css:
            return True
        if target.text and target.text.lower() in str(element.get("text", "")).lower():
            return True
    return False


def _matches_observe(predicate: AriadneObserve, snapshot: SnapshotResult) -> bool:
    if predicate.url_contains and predicate.url_contains not in snapshot.url:
        return False

    required = [
        _matches_target(target, snapshot) for target in predicate.required_elements
    ]
    forbidden = [
        _matches_target(target, snapshot) for target in predicate.forbidden_elements
    ]

    if any(forbidden):
        return False
    if not required:
        return True
    if predicate.logical_op == "AND":
        return all(required)
    return any(required)


@dataclass(slots=True)
class Labyrinth:
    """Topological memory over Ariadne state definitions."""

    ariadne_map: AriadneMap

    async def identify_room(self, snapshot: SnapshotResult) -> Optional[str]:
        """Return the first room whose predicate matches the current snapshot."""
        for state_id, state_def in self.ariadne_map.states.items():
            if _matches_observe(state_def.presence_predicate, snapshot):
                return state_id
        return None

    def expand(self, room_data: Any) -> None:
        """Store a newly discovered room definition in the loaded map."""
        if hasattr(room_data, "id"):
            self.ariadne_map.states[room_data.id] = room_data

    @classmethod
    async def load_from_db(
        cls,
        portal_name: str,
        map_type: str = "easy_apply",
        repository: MapRepository | None = None,
    ) -> "Labyrinth":
        """Load the portal topology from persistent storage."""
        repo = repository or MapRepository()
        try:
            ariadne_map = await repo.get_map_async(portal_name, map_type=map_type)
        except FileNotFoundError as exc:
            raise MapNotFoundError(str(exc)) from exc
        return cls(ariadne_map=ariadne_map)
