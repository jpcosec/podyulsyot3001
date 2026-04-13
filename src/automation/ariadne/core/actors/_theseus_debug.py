"""Theseus debug output helpers."""

from typing import Any, Dict


def should_stop_after_observe(
    merged_state: Dict[str, Any], updates: Dict[str, Any]
) -> bool:
    """Return whether the flow should stop after observe."""
    session_memory = merged_state.get("session_memory", {})
    if session_memory.get("goal_achieved") or session_memory.get("danger_detected"):
        return True
    return bool(updates.get("errors"))


def print_streamed_updates(chunk: dict) -> None:
    """Print streamed node updates."""
    for node_name, state_update in chunk.items():
        print_node(node_name)
        print_errors(state_update)
        print_state(state_update)


def print_node(node_name: str) -> None:
    """Print one node name."""
    print(f"[⚡] Node: {node_name}")


def print_errors(state_update: dict) -> None:
    """Print node errors."""
    for err in state_update.get("errors", []):
        print(f"    [⚠️] ERROR: {err}")


def print_state(state_update: dict) -> None:
    """Print active map state."""
    if "current_state_id" in state_update:
        print(f"    [⚡] Map State: {state_update['current_state_id']}")
