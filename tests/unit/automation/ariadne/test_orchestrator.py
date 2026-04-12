"""Tests for the Ariadne 2.0 StateGraph Orchestrator."""

import pytest
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from src.automation.ariadne.graph.orchestrator import (
    create_ariadne_graph,
    observe_node,
    human_in_the_loop_node,
    route_after_observe,
    route_after_deterministic,
    route_after_heuristics,
    route_after_agent
)
from src.automation.ariadne.models import AriadneState


def test_graph_compilation():
    """Verify that the graph compiles without errors."""
    graph = create_ariadne_graph()
    assert graph is not None
    assert "observe" in graph.nodes
    assert "execute_deterministic" in graph.nodes
    assert "human_in_the_loop" in graph.nodes


@pytest.mark.asyncio
async def test_graph_success_path():
    """Verify the success path (goal_achieved) terminates immediately after observe."""
    graph = create_ariadne_graph()
    
    initial_state = {
        "job_id": "test-success",
        "portal_name": "test-portal",
        "profile_data": {},
        "job_data": {},
        "path_id": None,
        "current_state_id": "start",
        "dom_elements": [],
        "current_url": "",
        "screenshot_b64": None,
        "session_memory": {"goal_achieved": True},
        "errors": [],
        "history": [],
        "portal_mode": "default"
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
    
    workflow.add_conditional_edges("observe", route_after_observe, {"execute_deterministic": "execute_deterministic", "human_in_the_loop": "human_in_the_loop", END: END})
    workflow.add_conditional_edges("execute_deterministic", route_after_deterministic, {"apply_local_heuristics": "apply_local_heuristics", "observe": "observe"})
    workflow.add_conditional_edges("apply_local_heuristics", route_after_heuristics, {"llm_rescue_agent": "llm_rescue_agent", "execute_deterministic": "execute_deterministic"})
    workflow.add_conditional_edges("llm_rescue_agent", route_after_agent, {"human_in_the_loop": "human_in_the_loop", "observe": "observe"})
    workflow.add_edge("human_in_the_loop", "observe")
    
    memory = MemorySaver()
    compiled_graph = workflow.compile(checkpointer=memory, interrupt_before=["human_in_the_loop"])

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
        "portal_mode": "default"
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
