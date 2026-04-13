"""AriadneThread mission transitions."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from src.automation.ariadne.exceptions import MapNotFoundError
from src.automation.ariadne.io import read_json_async
from src.automation.ariadne.models import AriadneEdge, AriadneMap


@dataclass(slots=True)
class AriadneThread:
    """Mission-scoped deterministic transitions."""

    edges: list[AriadneEdge] = field(default_factory=list)
    mission_id: Optional[str] = None

    def get_next_step(self, current_room_id: str) -> Optional[AriadneEdge]:
        """Return the first eligible transition for the current room."""
        for edge in self._eligible_edges(current_room_id):
            return edge
        return None

    def get_next_steps(self, current_room_id: str) -> list[AriadneEdge]:
        """Return all eligible transitions for the current room."""
        return list(self._eligible_edges(current_room_id))

    def add_step(self, edge: AriadneEdge) -> None:
        """Record a new successful transition for this mission."""
        self.edges.append(edge)

    def available_missions(self) -> list[str]:
        """List known mission ids for the loaded thread."""
        missions = {edge.mission_id for edge in self.edges if edge.mission_id}
        return sorted(missions)

    @classmethod
    async def load_from_db(
        cls,
        portal_name: str,
        mission_id: Optional[str] = None,
        map_type: str = "easy_apply",
        base_dir: Path | str | None = None,
    ) -> "AriadneThread":
        """Load mission transitions from persistent storage without MapRepository."""
        root = Path(base_dir) if base_dir else Path(__file__).parent.parent.parent.parent / "portals"
        map_path = root / portal_name / "maps" / f"{map_type}.json"

        try:
            map_payload = await read_json_async(map_path)
            ariadne_map = await asyncio.to_thread(AriadneMap.model_validate, map_payload)
        except FileNotFoundError as exc:
            raise MapNotFoundError(f"Thread map not found at {map_path}") from exc

        edges = [
            edge
            for edge in ariadne_map.edges
            if mission_id in (None, "", edge.mission_id)
        ]
        return cls(edges=edges, mission_id=mission_id)

    def _eligible_edges(self, current_room_id: str) -> Iterable[AriadneEdge]:
        for edge in self.edges:
            if edge.from_state != current_room_id:
                continue
            if self.mission_id and edge.mission_id not in (None, self.mission_id):
                continue
            yield edge
