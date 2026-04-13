"""Labyrinth topology model."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.automation.ariadne.contracts.base import AriadneTarget, SnapshotResult
from src.automation.ariadne.exceptions import MapNotFoundError
from src.automation.ariadne.io import read_json_async
from src.automation.ariadne.models import AriadneMap, AriadneObserve


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
        base_dir: Path | str | None = None,
    ) -> "Labyrinth":
        """Load the portal topology from persistent storage without MapRepository."""
        # Portals are in src/automation/portals/
        root = Path(base_dir) if base_dir else Path(__file__).parent.parent.parent.parent / "portals"
        map_path = root / portal_name / "maps" / f"{map_type}.json"

        try:
            map_payload = await read_json_async(map_path)
            # Use to_thread for heavy model validation
            ariadne_map = await asyncio.to_thread(AriadneMap.model_validate, map_payload)
            return cls(ariadne_map=ariadne_map)
        except FileNotFoundError as exc:
            raise MapNotFoundError(f"Labyrinth map not found at {map_path}") from exc
