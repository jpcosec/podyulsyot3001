"""Promotion utilities for Ariadne graph recordings."""

from __future__ import annotations

from pathlib import Path

from src.automation.ariadne.capabilities.recording import GraphRecorder
from src.automation.ariadne.models import AriadneMap
from src.automation.ariadne._promotion_events import (
    load_deterministic_events,
    extract_metadata,
)
from src.automation.ariadne._promotion_processing import (
    process_events,
    build_state,
    substitute_placeholders,
    write_map,
)


class AriadnePromoter:
    """Turn recorded Ariadne traces into draft map candidates."""

    def __init__(self, base_dir: Path | str = "data/ariadne/recordings") -> None:
        self.recorder = GraphRecorder(base_dir)

    def promote_thread(self, thread_id: str) -> AriadneMap:
        """Build and persist a draft AriadneMap from a recorded thread."""
        deterministic_events = load_deterministic_events(self.recorder, thread_id)
        portal_name, mission_id = extract_metadata(deterministic_events)

        states, edges, success_states = process_events(
            deterministic_events,
            build_state,
            substitute_placeholders,
        )

        promoted_map = AriadneMap(
            meta=AriadneMapMeta(source=portal_name, flow=mission_id, status="draft"),
            states=states,
            edges=edges,
            success_states=success_states,
            failure_states=[],
        )
        write_map(self.recorder.base_dir, thread_id, promoted_map)
        return promoted_map
