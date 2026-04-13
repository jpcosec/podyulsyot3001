"""Theseus workflow builder."""

from langgraph.graph import END, StateGraph

from src.automation.ariadne.models import AriadneState


def build_workflow(
    observe_handler,
    deterministic_handler,
    heuristics_handler,
    agent_handler,
    hitl_handler,
) -> StateGraph:
    """Build the complete workflow."""
    workflow = StateGraph(AriadneState)
    _add_nodes(
        workflow,
        observe_handler,
        deterministic_handler,
        heuristics_handler,
        agent_handler,
        hitl_handler,
    )
    _add_edges(workflow)
    return workflow


def _add_nodes(
    workflow,
    observe_handler,
    deterministic_handler,
    heuristics_handler,
    agent_handler,
    hitl_handler,
) -> None:
    """Register graph nodes."""
    workflow.add_node("observe", observe_handler)
    workflow.add_node("execute_deterministic", deterministic_handler)
    workflow.add_node("apply_local_heuristics", heuristics_handler)
    workflow.add_node("llm_rescue_agent", agent_handler)
    workflow.add_node("human_in_the_loop", hitl_handler)
    workflow.set_entry_point("observe")


def _add_edges(workflow: StateGraph) -> None:
    """Register graph edges."""
    from src.automation.ariadne.graph.orchestrator import (
        route_after_observe,
        route_after_deterministic,
        route_after_heuristics,
        route_after_agent,
    )

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
