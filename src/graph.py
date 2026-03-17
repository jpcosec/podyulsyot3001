"""LangGraph application assembly for PhD 2.0."""

# TODO: IS THIS USING LANGRAPH?
from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, Mapping, Sequence

from src.core.graph.state import GraphState, ReviewDecision, build_thread_id

NodeHandler = Callable[[GraphState], Mapping[str, Any]]

END_NODE = "__END__"

DEFAULT_ENTRY_POINT = "scrape"

DEFAULT_LINEAR_EDGES: tuple[tuple[str, str], ...] = (
    ("scrape", "translate_if_needed"),
    ("translate_if_needed", "extract_understand"),
    ("extract_understand", "match"),
    ("match", "review_match"),
    (
        "build_application_context",
        "review_application_context",
    ),  # TODO: what does this step do? please make the code more explicit here
    ("generate_documents", "generate_motivation_letter"),
    ("generate_motivation_letter", "review_motivation_letter"),
    ("tailor_cv", "review_cv"),
    ("draft_email", "review_email"),
    ("render", "package"),
)

DEFAULT_REVIEW_TRANSITIONS: dict[str, dict[str, str]] = {
    "review_match": {
        "approve": "build_application_context",
        "request_regeneration": "match",
        "reject": END_NODE,
    },
    "review_application_context": {
        "approve": "generate_documents",
        "request_regeneration": "build_application_context",
        "reject": END_NODE,
    },
    "review_motivation_letter": {
        "approve": "tailor_cv",
        "request_regeneration": "generate_motivation_letter",
        "reject": END_NODE,
    },
    "review_cv": {
        "approve": "draft_email",
        "request_regeneration": "tailor_cv",
        "reject": END_NODE,
    },
    "review_email": {
        "approve": "render",
        "request_regeneration": "draft_email",
        "reject": END_NODE,
    },
}

DEFAULT_INTERRUPT_BEFORE: tuple[str, ...] = tuple(DEFAULT_REVIEW_TRANSITIONS.keys())

PREP_MATCH_LINEAR_EDGES: tuple[tuple[str, str], ...] = (
    ("scrape", "translate_if_needed"),
    ("translate_if_needed", "extract_understand"),
    ("extract_understand", "match"),
    ("match", "review_match"),
    ("generate_documents", "package"),
)

PREP_MATCH_REVIEW_TRANSITIONS: dict[str, dict[str, str]] = {
    "review_match": {
        "approve": "generate_documents",
        "request_regeneration": "match",
        "reject": END_NODE,
    }
}


def create_app(
    node_registry: Mapping[str, NodeHandler],
    *,
    checkpointer: Any | None = None,
    entry_point: str = DEFAULT_ENTRY_POINT,
    linear_edges: Sequence[tuple[str, str]] = DEFAULT_LINEAR_EDGES,
    review_transitions: Mapping[str, Mapping[str, str]] = DEFAULT_REVIEW_TRANSITIONS,
    interrupt_before: Sequence[str] = DEFAULT_INTERRUPT_BEFORE,
):
    """Build and compile LangGraph workflow from node handlers."""
    _validate_graph_inputs(node_registry, entry_point, linear_edges, review_transitions)

    state_graph_cls, end_token = _load_langgraph_primitives()
    workflow = state_graph_cls(GraphState)

    for node_name, node_fn in node_registry.items():
        workflow.add_node(node_name, node_fn)

    workflow.set_entry_point(entry_point)

    for src, dst in linear_edges:
        workflow.add_edge(src, dst)

    workflow.add_edge("package", end_token)

    for review_node, decision_map in review_transitions.items():
        transitions = {
            decision: (end_token if next_node == END_NODE else next_node)
            for decision, next_node in decision_map.items()
        }
        workflow.add_conditional_edges(
            review_node,
            _route_review_decision,
            transitions,
        )

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=list(interrupt_before),
    )


def create_prep_match_app(
    *,
    checkpointer: Any | None = None,
    interrupt_before: Sequence[str] = ("review_match",),
):
    """Build graph app for scrape -> translate -> extract -> match -> review_match -> generate_documents."""
    return create_app(
        node_registry=build_prep_match_node_registry(),
        checkpointer=checkpointer,
        entry_point="scrape",
        linear_edges=PREP_MATCH_LINEAR_EDGES,
        review_transitions=PREP_MATCH_REVIEW_TRANSITIONS,
        interrupt_before=interrupt_before,
    )


def run_prep_match(
    initial_state: GraphState, *, resume: bool = False, checkpointer: Any | None = None
):
    """Execute prep-match flow with canonical thread identity."""
    app = create_prep_match_app(checkpointer=checkpointer)
    config = {
        "configurable": {
            "thread_id": build_thread_id(
                initial_state["source"], initial_state["job_id"]
            ),
        }
    }
    payload = None if resume else dict(initial_state)
    return app.invoke(payload, config=config)


def build_prep_match_node_registry() -> dict[str, NodeHandler]:
    """Return node handlers for prep-match and post-approval document generation."""
    from src.nodes.scrape.logic import run_logic as scrape_node
    from src.nodes.translate_if_needed.logic import (
        run_logic as translate_if_needed_node,
    )
    from src.nodes.extract_understand.logic import run_logic as extract_node
    from src.nodes.match.logic import run_logic as match_node
    from src.nodes.review_match.logic import run_logic as review_match_node
    from src.nodes.generate_documents.logic import run_logic as generate_documents_node

    return {
        "scrape": scrape_node,
        "translate_if_needed": translate_if_needed_node,
        "extract_understand": extract_node,
        "match": match_node,
        "review_match": review_match_node,
        "generate_documents": generate_documents_node,
        "package": _package_terminal_node,
    }


def _package_terminal_node(state: GraphState) -> Mapping[str, Any]:
    return {
        **dict(state),
        "current_node": "package",
        "status": "completed",
    }


def _route_review_decision(state: GraphState) -> ReviewDecision:
    decision = state.get("review_decision")
    if decision not in {"approve", "request_regeneration", "reject"}:
        raise ValueError("review_decision must be approve/request_regeneration/reject")
    return decision


def _validate_graph_inputs(
    node_registry: Mapping[str, NodeHandler],
    entry_point: str,
    linear_edges: Sequence[tuple[str, str]],
    review_transitions: Mapping[str, Mapping[str, str]],
) -> None:
    required_nodes: set[str] = {entry_point, "package"}

    for src, dst in linear_edges:
        required_nodes.add(src)
        required_nodes.add(dst)

    for review_node, transitions in review_transitions.items():
        required_nodes.add(review_node)
        for next_node in transitions.values():
            if next_node != END_NODE:
                required_nodes.add(next_node)

    missing = sorted(name for name in required_nodes if name not in node_registry)
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"node_registry missing required nodes: {joined}")


def _load_langgraph_primitives() -> tuple[Any, Any]:
    try:
        graph_module = import_module("langgraph.graph")
    except ModuleNotFoundError as exc:
        raise RuntimeError("langgraph is required to compile graph app") from exc

    return graph_module.StateGraph, graph_module.END
