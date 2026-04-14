"""AriadneState — the LangGraph state dict.

Pure data. No live objects. Adapters, Labyrinth, and Thread are
constructor-injected into actors, never placed here.
"""

from __future__ import annotations

from typing import Annotated, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

from src.automation.contracts.sensor import SnapshotResult
from src.automation.contracts.motor import TraceEvent


def _append(existing: list, new: list) -> list:
    """Reducer: append-only lists (errors, trace, extracted_data)."""
    return existing + new


class AriadneState(TypedDict):
    # --- Seeded by Interpreter ---
    instruction: str
    mission_id: str
    portal_name: str

    # --- Written by Observe ---
    snapshot: SnapshotResult | None

    # --- Written by Theseus / Delphi ---
    current_room_id: str | None

    # --- Extraction accumulator (append-only) ---
    extracted_data: Annotated[list[dict[str, Any]], _append]

    # --- Execution trace (append-only) — consumed by Recorder ---
    trace: Annotated[list[TraceEvent], _append]

    # --- Circuit breaker ---
    agent_failures: int

    # --- Terminal flag — set by Theseus when current room is_terminal ---
    is_mission_complete: bool

    # --- Error log (append-only) ---
    errors: Annotated[list[str], _append]
