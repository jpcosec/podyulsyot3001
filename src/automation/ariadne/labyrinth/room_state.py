"""RoomState — a visual variant of a URLNode.

One URLNode can have many RoomStates:
  home.anon, home.logged_in, home.with_cookie_modal, home.with_ad_overlay ...

Modal overlays are not a separate class — they're RoomStates with is_modal_overlay=True.
The Labyrinth stores them all. Broken states, 404s, and ad overlays are valid rooms.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from src.automation.contracts.sensor import SnapshotResult


@dataclass
class RoomState:
    """
    id:              globally unique, e.g. "home.with_cookie_modal"
    url_node_id:     parent URLNode
    predicate:       callable(SnapshotResult) -> bool — detects this state from the live snapshot
    is_modal_overlay: True if this state blocks the underlying page interaction
    is_terminal:     True if reaching this room ends the mission (success or dead-end)
    """

    id: str
    url_node_id: str
    predicate: "Callable[[SnapshotResult], bool]"
    is_modal_overlay: bool = False
    blocks_interaction: bool = False
    is_terminal: bool = False

    def matches(self, snapshot: "SnapshotResult") -> bool:
        return self.predicate(snapshot)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url_node_id": self.url_node_id,
            "is_modal_overlay": self.is_modal_overlay,
            "blocks_interaction": self.blocks_interaction,
            "is_terminal": self.is_terminal,
            # predicate is not serialized — it's registered at load time
        }

    @classmethod
    def from_dict(cls, data: dict, predicate: "Callable[[SnapshotResult], bool]") -> "RoomState":
        return cls(
            id=data["id"],
            url_node_id=data["url_node_id"],
            predicate=predicate,
            is_modal_overlay=data.get("is_modal_overlay", False),
            blocks_interaction=data.get("blocks_interaction", False),
            is_terminal=data.get("is_terminal", False),
        )
