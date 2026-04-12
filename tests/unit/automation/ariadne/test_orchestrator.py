"""Tests for the Ariadne 2.0 StateGraph Orchestrator."""

import pytest
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from src.automation.ariadne.graph.orchestrator import (
    _find_safe_sequence,
    create_ariadne_graph,
    observe_node,
    human_in_the_loop_node,
    route_after_observe,
    route_after_deterministic,
    route_after_heuristics,
    route_after_agent,
)
from src.automation.ariadne.models import AriadneState


@pytest.mark.asyncio
async def test_graph_compilation():
    """Verify that the graph compiles without errors."""
    async with create_ariadne_graph(use_memory=True) as graph:
        assert graph is not None
        assert "observe" in graph.nodes
        assert "execute_deterministic" in graph.nodes
        assert "human_in_the_loop" in graph.nodes


@pytest.mark.asyncio
async def test_graph_success_path():
    """Verify the success path (goal_achieved) terminates immediately after observe."""
    async with create_ariadne_graph(use_memory=True) as graph:
        initial_state = {
            "job_id": "test-success",
            "portal_name": "test-portal",
            "profile_data": {},
            "job_data": {},
            "path_id": None,
            "current_mission_id": None,
            "current_state_id": "start",
            "dom_elements": [],
            "current_url": "",
            "screenshot_b64": None,
            "session_memory": {"goal_achieved": True},
            "errors": [],
            "history": [],
            "portal_mode": "default",
            "patched_components": {},
        }

        config = {"configurable": {"thread_id": "test-success-thread"}}

        events = []
        async for event in graph.astream(initial_state, config):
            events.append(event)

        assert len(events) == 1
        assert "observe" in events[0]


@pytest.mark.asyncio
async def test_graph_fallback_cascade_to_hitl():
    """Verify the 4-level fallback cascade reaches HITL when all levels fail."""

    # We need to reconstruct a failing graph for this test
    async def fail_node(state, config=None):
        return {"errors": ["Simulated failure"]}

    workflow = StateGraph(AriadneState)
    workflow.add_node("observe", observe_node)
    workflow.add_node("execute_deterministic", fail_node)
    workflow.add_node("apply_local_heuristics", fail_node)
    workflow.add_node("llm_rescue_agent", fail_node)
    workflow.add_node("human_in_the_loop", human_in_the_loop_node)

    workflow.set_entry_point("observe")

    workflow.add_conditional_edges(
        "observe",
        route_after_observe,
        {
            "execute_deterministic": "execute_deterministic",
            "human_in_the_loop": "human_in_the_loop",
            END: END,
        },
    )
    workflow.add_conditional_edges(
        "execute_deterministic",
        route_after_deterministic,
        {"apply_local_heuristics": "apply_local_heuristics", "observe": "observe"},
    )
    workflow.add_conditional_edges(
        "apply_local_heuristics",
        route_after_heuristics,
        {
            "llm_rescue_agent": "llm_rescue_agent",
            "execute_deterministic": "execute_deterministic",
        },
    )
    workflow.add_conditional_edges(
        "llm_rescue_agent",
        route_after_agent,
        {"human_in_the_loop": "human_in_the_loop", "observe": "observe"},
    )
    workflow.add_edge("human_in_the_loop", "observe")

    memory = MemorySaver()
    compiled_graph = workflow.compile(
        checkpointer=memory, interrupt_before=["human_in_the_loop"]
    )

    initial_state = {
        "job_id": "test-fallback",
        "portal_name": "test-portal",
        "profile_data": {},
        "job_data": {},
        "path_id": None,
        "current_state_id": "start",
        "dom_elements": [],
        "current_url": "",
        "screenshot_b64": None,
        "session_memory": {},
        "errors": [],
        "history": [],
        "portal_mode": "default",
    }
    config = {"configurable": {"thread_id": "test-fallback-thread"}}

    events = []
    async for event in compiled_graph.astream(initial_state, config):
        events.append(event)

    # Observe -> ExecuteDeterministic -> Heuristics -> Agent -> Interrupt
    node_names = [list(event.keys())[0] for event in events]
    assert "observe" in node_names
    assert "execute_deterministic" in node_names
    assert "apply_local_heuristics" in node_names
    assert "llm_rescue_agent" in node_names

    snapshot = await compiled_graph.aget_state(config)
    assert "human_in_the_loop" in snapshot.next


@pytest.mark.asyncio
async def test_graph_persists_state_in_sqlite(tmp_path):
    """Persistent graphs should retain state across compiled instances."""
    checkpoint_path = tmp_path / "checkpoints.db"
    initial_state = {
        "job_id": "test-persist",
        "portal_name": "test-portal",
        "profile_data": {},
        "job_data": {},
        "path_id": None,
        "current_mission_id": None,
        "current_state_id": "start",
        "dom_elements": [],
        "current_url": "",
        "screenshot_b64": None,
        "session_memory": {"goal_achieved": True},
        "errors": [],
        "history": [],
        "portal_mode": "default",
        "patched_components": {},
    }
    config = {"configurable": {"thread_id": "test-persist-thread"}}

    async with create_ariadne_graph(checkpoint_path=checkpoint_path) as first_graph:
        async for _ in first_graph.astream(initial_state, config):
            pass

    assert checkpoint_path.exists()

    async with create_ariadne_graph(checkpoint_path=checkpoint_path) as second_graph:
        snapshot = await second_graph.aget_state(config)

        assert snapshot.values["session_memory"]["goal_achieved"] is True


def test_find_safe_sequence_selects_css_over_text():
    """Edge with CSS selector should be prioritized over text-only fallback."""
    from src.automation.ariadne.models import (
        AriadneMap,
        AriadneMapMeta,
        AriadneStateDefinition,
        AriadneEdge,
        AriadneIntent,
        AriadneObserve,
    )
    from src.automation.ariadne.contracts.base import AriadneTarget

    # Define a simple map with two edges from same state
    # Edge 1: text-only target (lower priority)
    # Edge 2: CSS selector target (higher priority)
    edge_text = AriadneEdge(
        from_state="state_a",
        to_state="state_b",
        intent=AriadneIntent.CLICK,
        target=AriadneTarget(text="Submit"),
    )
    edge_css = AriadneEdge(
        from_state="state_a",
        to_state="state_c",
        intent=AriadneIntent.CLICK,
        target=AriadneTarget(css=".submit-btn"),
    )

    ariadne_map = AriadneMap(
        meta=AriadneMapMeta(source="test", flow="test"),
        states={
            "state_a": AriadneStateDefinition(
                id="state_a",
                description="State A",
                presence_predicate=AriadneObserve(url_contains=""),
                components={},
            ),
            "state_b": AriadneStateDefinition(
                id="state_b",
                description="State B",
                presence_predicate=AriadneObserve(url_contains=""),
                components={},
            ),
            "state_c": AriadneStateDefinition(
                id="state_c",
                description="State C",
                presence_predicate=AriadneObserve(url_contains=""),
                components={},
            ),
        },
        edges=[edge_text, edge_css],
        success_states=["state_c"],
        failure_states=[],
    )

    # DOM has an element matching both targets
    dom_elements = [
        {"text": "Submit", "selector": ".submit-btn"},
    ]

    state: AriadneState = {
        "job_id": "test",
        "portal_name": "test-portal",
        "profile_data": {},
        "job_data": {},
        "path_id": None,
        "current_mission_id": None,
        "current_state_id": "state_a",
        "dom_elements": dom_elements,
        "current_url": "",
        "screenshot_b64": None,
        "session_memory": {},
        "errors": [],
        "history": [],
        "portal_mode": "default",
        "patched_components": {},
    }

    result = _find_safe_sequence("state_a", ariadne_map, state)

    # Should select CSS-based edge (state_c) over text-only (state_b)
    assert len(result) == 1
    assert result[0].to_state == "state_c"


def test_find_safe_sequence_selects_mission_matching_edge():
    """Edge with matching mission_id should be prioritized over generic edge."""
    from src.automation.ariadne.models import (
        AriadneMap,
        AriadneMapMeta,
        AriadneStateDefinition,
        AriadneEdge,
        AriadneIntent,
        AriadneObserve,
    )
    from src.automation.ariadne.contracts.base import AriadneTarget

    # Edge 1: generic (no mission)
    edge_generic = AriadneEdge(
        from_state="state_a",
        to_state="state_b",
        intent=AriadneIntent.CLICK,
        target=AriadneTarget(css=".btn"),
    )
    # Edge 2: mission-specific
    edge_mission = AriadneEdge(
        from_state="state_a",
        to_state="state_c",
        intent=AriadneIntent.CLICK,
        target=AriadneTarget(css=".btn"),
        mission_id="easy_apply",
    )

    ariadne_map = AriadneMap(
        meta=AriadneMapMeta(source="test", flow="test"),
        states={
            "state_a": AriadneStateDefinition(
                id="state_a",
                description="State A",
                presence_predicate=AriadneObserve(url_contains=""),
                components={},
            ),
            "state_b": AriadneStateDefinition(
                id="state_b",
                description="State B",
                presence_predicate=AriadneObserve(url_contains=""),
                components={},
            ),
            "state_c": AriadneStateDefinition(
                id="state_c",
                description="State C",
                presence_predicate=AriadneObserve(url_contains=""),
                components={},
            ),
        },
        edges=[edge_generic, edge_mission],
        success_states=["state_c"],
        failure_states=[],
    )

    dom_elements = [{"text": "click", "selector": ".btn"}]

    # Current mission is "easy_apply" - should prefer mission-specific edge
    state: AriadneState = {
        "job_id": "test",
        "portal_name": "test-portal",
        "profile_data": {},
        "job_data": {},
        "path_id": None,
        "current_mission_id": "easy_apply",
        "current_state_id": "state_a",
        "dom_elements": dom_elements,
        "current_url": "",
        "screenshot_b64": None,
        "session_memory": {},
        "errors": [],
        "history": [],
        "portal_mode": "default",
        "patched_components": {},
    }

    result = _find_safe_sequence("state_a", ariadne_map, state)

    # Should select mission-specific edge (state_c) over generic (state_b)
    assert len(result) == 1
    assert result[0].to_state == "state_c"


def test_find_safe_sequence_selects_hint_over_text():
    """Edge with hint should be prioritized over text-only fallback when both are valid."""
    from src.automation.ariadne.models import (
        AriadneMap,
        AriadneMapMeta,
        AriadneStateDefinition,
        AriadneEdge,
        AriadneIntent,
        AriadneObserve,
    )
    from src.automation.ariadne.contracts.base import AriadneTarget

    # Edge 1: text-only target
    edge_text = AriadneEdge(
        from_state="state_a",
        to_state="state_b",
        intent=AriadneIntent.CLICK,
        target=AriadneTarget(text="Next"),
    )
    # Edge 2: hint + css target (higher priority than text-only)
    edge_hint = AriadneEdge(
        from_state="state_a",
        to_state="state_c",
        intent=AriadneIntent.CLICK,
        target=AriadneTarget(hint="AA", css="button.next-btn"),
    )

    ariadne_map = AriadneMap(
        meta=AriadneMapMeta(source="test", flow="test"),
        states={
            "state_a": AriadneStateDefinition(
                id="state_a",
                description="State A",
                presence_predicate=AriadneObserve(url_contains=""),
                components={},
            ),
            "state_b": AriadneStateDefinition(
                id="state_b",
                description="State B",
                presence_predicate=AriadneObserve(url_contains=""),
                components={},
            ),
            "state_c": AriadneStateDefinition(
                id="state_c",
                description="State C",
                presence_predicate=AriadneObserve(url_contains=""),
                components={},
            ),
        },
        edges=[edge_text, edge_hint],
        success_states=["state_c"],
        failure_states=[],
    )

    # DOM has element matching both targets
    dom_elements = [{"text": "Next", "selector": "button.next-btn"}]

    state: AriadneState = {
        "job_id": "test",
        "portal_name": "test-portal",
        "profile_data": {},
        "job_data": {},
        "path_id": None,
        "current_mission_id": None,
        "current_state_id": "state_a",
        "dom_elements": dom_elements,
        "current_url": "",
        "screenshot_b64": None,
        "session_memory": {},
        "errors": [],
        "history": [],
        "portal_mode": "default",
        "patched_components": {},
    }

    result = _find_safe_sequence("state_a", ariadne_map, state)

    # Should select hint+css edge (state_c) over text-only (state_b)
    assert len(result) == 1
    assert result[0].to_state == "state_c"
