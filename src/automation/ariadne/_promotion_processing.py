"""Promotion - event processing helpers."""

from typing import Any

from src.automation.ariadne.io import write_json
from src.automation.ariadne.models import (
    AriadneEdge,
    AriadneMap,
    AriadneMapMeta,
    AriadneObserve,
    AriadneStateDefinition,
)


def build_state(state_id: str) -> AriadneStateDefinition:
    """Build a state definition for promotion."""
    return AriadneStateDefinition(
        id=state_id,
        description=f"Promoted state {state_id}",
        presence_predicate=AriadneObserve(required_elements=[]),
    )


def substitute_placeholders(
    value: str | None,
    profile_data: dict[str, Any],
    job_data: dict[str, Any],
) -> str | None:
    """Substitute actual values with placeholders."""
    if value is None:
        return None
    for key, candidate in {**profile_data, **job_data}.items():
        if candidate is not None and value == str(candidate):
            return f"{{{{{key}}}}}"
    return value


def process_events(
    deterministic_events: list[dict],
    build_state_fn,
    substitute_fn,
) -> tuple[dict[str, AriadneStateDefinition], list[AriadneEdge], list[str]]:
    """Process deterministic events into states, edges, and success states."""
    states: dict[str, AriadneStateDefinition] = {}
    edges: list[AriadneEdge] = []
    success_states: list[str] = []

    for event in deterministic_events:
        payload = event["payload"]
        state_before = payload.get("state_before") or {}
        current_state_id = state_before.get("current_state_id")
        if current_state_id and current_state_id not in states:
            states[current_state_id] = build_state_fn(current_state_id)

        for edge_data in payload.get("selected_edges", []):
            to_state = edge_data["to_state"]
            if to_state not in states:
                states[to_state] = build_state_fn(to_state)
            edges.append(
                AriadneEdge(
                    from_state=edge_data["from_state"],
                    to_state=to_state,
                    mission_id=edge_data.get("mission_id"),
                    intent=edge_data["intent"],
                    target=edge_data["target"],
                    value=substitute_fn(
                        edge_data.get("value"),
                        state_before.get("profile_data", {}),
                        state_before.get("job_data", {}),
                    ),
                    extract=edge_data.get("extract"),
                )
            )
            success_states = [to_state]

    return states, edges, success_states


def write_map(recorder_base_dir, thread_id: str, ariadne_map: AriadneMap) -> Any:
    """Write the promoted map to disk."""
    from pathlib import Path

    output_path = Path(recorder_base_dir) / thread_id / "normalized_map.json"
    return write_json(output_path, ariadne_map.model_dump(mode="json"), indent=2)
