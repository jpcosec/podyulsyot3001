"""Labyrinth — exhaustive atlas of all known rooms in a portal.

No edges. Does not know about missions or routes.
Broken states, 404s, and ad overlays are stored — all are context for Delphi.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.automation.contracts.sensor import SnapshotResult
from src.automation.ariadne.labyrinth.url_node import URLNode
from src.automation.ariadne.labyrinth.room_state import RoomState
from src.automation.ariadne.labyrinth.skeleton import Skeleton

DATA_ROOT = Path("data/portals")


@dataclass
class Room:
    url_node: URLNode
    state: RoomState
    skeleton: Skeleton


class Labyrinth:
    """Atlas of (URLNode, RoomState) → Skeleton for one portal."""

    def __init__(self, portal_name: str) -> None:
        self.portal_name = portal_name
        self._rooms: dict[str, Room] = {}  # room_id → Room

    # ── Identification ───────────────────────────────────────────────────────

    def identify_room(self, snapshot: SnapshotResult) -> str | None:
        """Return the room_id that matches the snapshot, or None if unknown."""
        candidates = [
            room for room in self._rooms.values()
            if room.url_node.match(snapshot.url)
        ]
        for room in candidates:
            if room.state.matches(snapshot):
                return room.state.id
        return None

    # ── Expansion ────────────────────────────────────────────────────────────

    def expand(self, url_node: URLNode, state: RoomState, skeleton: Skeleton) -> None:
        """Add or overwrite a room. Called by Recorder when Delphi discovers a new room."""
        self._rooms[state.id] = Room(url_node=url_node, state=state, skeleton=skeleton)

    def get_room(self, room_id: str) -> Room | None:
        return self._rooms.get(room_id)

    def known_dead_ends(self) -> list[str]:
        """Room IDs that are terminal non-success states — useful context for Delphi."""
        return [r.state.id for r in self._rooms.values() if r.state.is_terminal]

    # ── Persistence ──────────────────────────────────────────────────────────

    def save(self) -> None:
        path = _portal_path(self.portal_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._to_dict(), indent=2))

    def _to_dict(self) -> dict:
        return {
            "portal_name": self.portal_name,
            "rooms": {rid: _room_to_dict(r) for rid, r in self._rooms.items()},
        }

    @classmethod
    def load(cls, portal_name: str) -> "Labyrinth":
        """Load from disk. Returns empty Labyrinth if file doesn't exist yet."""
        labyrinth = cls(portal_name)
        path = _portal_path(portal_name)
        if not path.exists():
            return labyrinth
        data = json.loads(path.read_text())
        for room_id, room_data in data.get("rooms", {}).items():
            labyrinth._rooms[room_id] = _room_from_dict(room_data)
        return labyrinth


def _portal_path(portal_name: str) -> Path:
    return DATA_ROOT / portal_name / "labyrinth.json"


def _room_to_dict(room: Room) -> dict:
    return {
        "url_node": room.url_node.to_dict(),
        "state": room.state.to_dict(),
        "skeleton": room.skeleton.to_dict(),
    }


def _room_from_dict(data: dict) -> Room:
    url_node = URLNode.from_dict(data["url_node"])
    skeleton = Skeleton.from_dict(data["skeleton"])
    # Predicates are not serializable. Fallback: match by URL only.
    # Re-register real predicates after load if finer detection is needed.
    state = RoomState.from_dict(
        data["state"],
        predicate=lambda snapshot, node=url_node: node.match(snapshot.url),
    )
    return Room(url_node=url_node, state=state, skeleton=skeleton)
