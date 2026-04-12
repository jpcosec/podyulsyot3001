"""Promotion utilities for Ariadne graph recordings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.automation.ariadne.capabilities.recording import GraphRecorder
from src.automation.ariadne.models import (
    AriadneEdge,
    AriadneMap,
    AriadneMapMeta,
    AriadneObserve,
    AriadneStateDefinition,
)


class AriadnePromoter:
    """Turn recorded Ariadne traces into draft map candidates."""

    def __init__(self, base_dir: Path | str = "data/ariadne/recordings") -> None:
        self.recorder = GraphRecorder(base_dir)

    def promote_thread(self, thread_id: str) -> AriadneMap:
        """Build and persist a draft AriadneMap from a recorded thread."""
        events = self.recorder.load_events(thread_id)
        if not events:
            raise FileNotFoundError(f"No recording found for thread '{thread_id}'.")

        deterministic_events = [
            event
            for event in events
            if event.get("event_type") == "execute_deterministic"
        ]
        if not deterministic_events:
            raise ValueError(
                f"No deterministic events recorded for thread '{thread_id}'."
            )

        first_payload = deterministic_events[0]["payload"]
        portal_name = first_payload.get("portal_name", "unknown")
        mission_id = first_payload.get("current_mission_id") or "promoted"

        states: dict[str, AriadneStateDefinition] = {}
        edges: list[AriadneEdge] = []
        success_states: list[str] = []

        for event in deterministic_events:
            payload = event["payload"]
            state_before = payload.get("state_before") or {}
            current_state_id = state_before.get("current_state_id")
            if current_state_id and current_state_id not in states:
                states[current_state_id] = self._build_state(current_state_id)

            for edge_data in payload.get("selected_edges", []):
                to_state = edge_data["to_state"]
                if to_state not in states:
                    states[to_state] = self._build_state(to_state)
                edges.append(
                    AriadneEdge(
                        from_state=edge_data["from_state"],
                        to_state=to_state,
                        mission_id=edge_data.get("mission_id"),
                        intent=edge_data["intent"],
                        target=edge_data["target"],
                        value=self._substitute_placeholders(
                            edge_data.get("value"),
                            state_before.get("profile_data", {}),
                            state_before.get("job_data", {}),
                        ),
                        extract=edge_data.get("extract"),
                    )
                )
                success_states = [to_state]

        promoted_map = AriadneMap(
            meta=AriadneMapMeta(source=portal_name, flow=mission_id, status="draft"),
            states=states,
            edges=edges,
            success_states=success_states,
            failure_states=[],
        )
        self._write_map(thread_id, promoted_map)
        return promoted_map

    def _build_state(self, state_id: str) -> AriadneStateDefinition:
        return AriadneStateDefinition(
            id=state_id,
            description=f"Promoted state {state_id}",
            presence_predicate=AriadneObserve(required_elements=[]),
        )

    def _substitute_placeholders(
        self,
        value: str | None,
        profile_data: dict[str, Any],
        job_data: dict[str, Any],
    ) -> str | None:
        if value is None:
            return None

        for key, candidate in {**profile_data, **job_data}.items():
            if candidate is not None and value == str(candidate):
                return f"{{{{{key}}}}}"
        return value

    def _write_map(self, thread_id: str, ariadne_map: AriadneMap) -> Path:
        session_dir = self.recorder.base_dir / thread_id
        session_dir.mkdir(parents=True, exist_ok=True)
        output_path = session_dir / "normalized_map.json"
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(ariadne_map.model_dump(mode="json"), handle, indent=2)
        return output_path
