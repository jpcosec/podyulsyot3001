"""AriadneThread mission transitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from src.automation.ariadne.exceptions import MapNotFoundError
from src.automation.ariadne.models import AriadneEdge
from src.automation.ariadne.repository import MapRepository


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
        repository: MapRepository | None = None,
    ) -> "AriadneThread":
        """Load mission transitions from persistent storage."""
        repo = repository or MapRepository()
        try:
            ariadne_map = await repo.get_map_async(portal_name, map_type=map_type)
        except FileNotFoundError as exc:
            raise MapNotFoundError(str(exc)) from exc

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
