"""Tests for mission-driven Ariadne path filtering."""

from src.automation.ariadne.contracts.base import AriadneIntent, AriadneTarget
from src.automation.ariadne.graph.orchestrator import _find_safe_sequence
from src.automation.ariadne.models import (
    AriadneEdge,
    AriadneMap,
    AriadneMapMeta,
    AriadneObserve,
    AriadneStateDefinition,
)


def test_find_safe_sequence_filters_edges_by_current_mission():
    """Only edges matching the active mission should be considered."""
    ariadne_map = AriadneMap(
        meta=AriadneMapMeta(source="linkedin", flow="multi"),
        states={
            "start": AriadneStateDefinition(
                id="start",
                description="Start",
                presence_predicate=AriadneObserve(required_elements=[]),
                components={
                    "apply": AriadneTarget(css="#apply"),
                    "skip": AriadneTarget(css="#skip"),
                },
            ),
            "apply_state": AriadneStateDefinition(
                id="apply_state",
                description="Apply",
                presence_predicate=AriadneObserve(required_elements=[]),
            ),
            "skip_state": AriadneStateDefinition(
                id="skip_state",
                description="Skip",
                presence_predicate=AriadneObserve(required_elements=[]),
            ),
        },
        edges=[
            AriadneEdge(
                from_state="start",
                to_state="skip_state",
                mission_id="skip_flow",
                intent=AriadneIntent.CLICK,
                target="skip",
            ),
            AriadneEdge(
                from_state="start",
                to_state="apply_state",
                mission_id="easy_apply",
                intent=AriadneIntent.CLICK,
                target="apply",
            ),
        ],
        success_states=["apply_state", "skip_state"],
        failure_states=[],
    )

    state = {
        "current_state_id": "start",
        "current_mission_id": "easy_apply",
        "dom_elements": [{"selector": "#apply"}, {"selector": "#skip"}],
        "patched_components": {},
    }

    batch = _find_safe_sequence("start", ariadne_map, state)

    assert len(batch) == 1
    assert batch[0].mission_id == "easy_apply"
    assert batch[0].to_state == "apply_state"


def test_find_safe_sequence_allows_shared_edges_without_mission_id():
    """Shared edges should stay available even when a mission is active."""
    ariadne_map = AriadneMap(
        meta=AriadneMapMeta(source="linkedin", flow="shared"),
        states={
            "start": AriadneStateDefinition(
                id="start",
                description="Start",
                presence_predicate=AriadneObserve(required_elements=[]),
                components={"next": AriadneTarget(css="#next")},
            ),
            "next_state": AriadneStateDefinition(
                id="next_state",
                description="Next",
                presence_predicate=AriadneObserve(required_elements=[]),
            ),
        },
        edges=[
            AriadneEdge(
                from_state="start",
                to_state="next_state",
                intent=AriadneIntent.CLICK,
                target="next",
            )
        ],
        success_states=["next_state"],
        failure_states=[],
    )

    state = {
        "current_state_id": "start",
        "current_mission_id": "discovery",
        "dom_elements": [{"selector": "#next"}],
        "patched_components": {},
    }

    batch = _find_safe_sequence("start", ariadne_map, state)

    assert len(batch) == 1
    assert batch[0].mission_id is None
