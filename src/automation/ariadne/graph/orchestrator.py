"""LangGraph StateGraph Controller for Ariadne 2.0.

This module implements the core JIT Flight Controller that orchestrates
browser navigation using a cyclic graph with a 4-level fallback cascade.
"""

import asyncio
import copy
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, StateGraph
from langchain_core.runnables import RunnableConfig

from src.automation.ariadne.models import AriadneState
from src.automation.ariadne.contracts.base import SnapshotResult
from src.automation.adapters.translators.registry import TranslatorRegistry
from src.automation.ariadne.graph.nodes.agent import LangGraphBrowserOSAgent
from src.automation.ariadne.repository import MapRepository


MAX_HEURISTIC_RETRIES = 2

from src.automation.ariadne.graph._orchestrator_helpers import (
    _adapter_execute,
    _adapter_snapshot,
    _apply_identified_state,
    _collect_extracted_memory,
    _danger_signals,
    _deterministic_batch,
    _deterministic_executor,
    _deterministic_updates,
    _executor_not_found,
    _filter_valid_edges,
    _find_safe_sequence,
    _get_candidate_edges,
    _load_deterministic_map,
    _mark_goal_achieved,
    _observe_updates,
    _observe_next_step,
    _record_deterministic_event,
    _record_graph_event,
    _resolve_target,
    _safe_identify_state,
    _score_edge,
    _snapshot_updates,
    _target_specificity,
    _translate_command,
    _translation_error,
    _update_danger_memory,
    _execution_failed,
    _execution_error_message,
    _agent_should_escalate,
    _print_agent_circuit_breaker,
)


async def observe_node(state: AriadneState, config: RunnableConfig) -> Dict[str, Any]:
    """Captures the JIT state (URL, Accessibility Tree, Screenshot) via the active Executor."""
    print("--- NODE: Observe ---")
    executor = config.get("configurable", {}).get("executor")

    if not executor:
        return _executor_not_found()

    try:
        return await _observe_updates(state, config, executor)
    except Exception as e:
        return {"errors": [f"ObservationError: {str(e)}"]}


async def execute_deterministic_node(
    state: AriadneState, config: RunnableConfig
) -> Dict[str, Any]:
    """Replays the AriadneMap for the current node state with Micro-Batching and atomic fallback."""
    print("--- NODE: Execute Deterministic ---")

    executor = _deterministic_executor(config)
    if not executor:
        return {
            "errors": [
                "ExecutorNotFoundError: No executor instance provided in config."
            ]
        }
    try:
        ariadne_map = await _load_deterministic_map(state, config)
    except Exception as e:
        return {"errors": [f"MapLoadError: {str(e)}"]}

    current_state_id = state.get("current_state_id")
    batch = _deterministic_batch(state, config, ariadne_map)
    if not batch:
        return {
            "errors": [
                f"NoTransitionError: No valid, live edge found from state '{current_state_id}'"
            ]
        }

    motor_name = config.get("configurable", {}).get("motor_name", "crawl4ai")
    translator = TranslatorRegistry.get_translator_by_name(motor_name)

    try:
        command = _translate_command(batch, translator, ariadne_map, state)
    except Exception as e:
        return _translation_error(e)

    print(f"--- Dispatching Command: {command} ---")
    try:
        result = await _adapter_execute(executor, command)
        failure = _execution_failed(result)
        if failure is not None:
            return failure
    except Exception as e:
        return {"errors": [f"ExecutionError: {str(e)}"]}

    updates = _deterministic_updates(state, batch, result)
    await _record_deterministic_event(config, state, batch, result, updates)
    return updates


async def apply_local_heuristics_node(
    state: AriadneState, config: RunnableConfig
) -> Dict[str, Any]:
    """Applies local rules from the active portal_mode (e.g. 'easy_apply')."""
    print("--- NODE: Apply Local Heuristics ---")

    from src.automation.ariadne.graph._orchestrator_helpers import (
        _resolve_mode,
        _load_state_definition,
        _get_state_definition,
        _apply_heuristic_patches,
    )

    mode = _resolve_mode(state)
    ariadne_map = await _load_state_definition(state)
    current_state_id = state.get("current_state_id")
    definition = _get_state_definition(ariadne_map, current_state_id)

    if not definition:
        return {"errors": [f"StateDefinitionNotFoundError: {current_state_id}"]}

    return await _apply_heuristic_patches(definition, current_state_id, state, mode)


async def llm_rescue_agent_node(
    state: AriadneState, config: RunnableConfig
) -> Dict[str, Any]:
    """Infers the next action using Link Hints + DOM via VLM Agent (Direct MCP)."""
    print("--- NODE: LLM Rescue Agent (Direct MCP) ---")
    agent = LangGraphBrowserOSAgent()
    return await agent.run(state)


async def human_in_the_loop_node(
    state: AriadneState, config: RunnableConfig
) -> Dict[str, Any]:
    """Native LangGraph breakpoint (interrupt_before)."""
    print("--- NODE: Human In The Loop ---")
    new_memory = state.get("session_memory", {}).copy()
    new_memory["human_intervention"] = True
    return {"session_memory": new_memory}


def route_after_observe(state: AriadneState) -> str:
    """Routing logic after observation."""
    session_memory = state.get("session_memory", {})
    if session_memory.get("goal_achieved"):
        return END
    return _observe_next_step(session_memory)


def route_after_deterministic(state: AriadneState) -> str:
    """Routing logic after deterministic execution."""
    if state.get("errors"):
        return "apply_local_heuristics"

    return "observe"


def route_after_heuristics(state: AriadneState) -> str:
    """Routing logic after heuristics application."""
    heuristic_retries = state.get("session_memory", {}).get("heuristic_retries", 0)
    if state.get("errors") or heuristic_retries >= MAX_HEURISTIC_RETRIES:
        return "llm_rescue_agent"

    return "execute_deterministic"


def route_after_agent(state: AriadneState) -> str:
    """Routing logic after LLM Agent execution with Circuit Breaker."""
    session_memory = state.get("session_memory", {})
    agent_failures = session_memory.get("agent_failures", 0)

    if _agent_should_escalate(state, session_memory, agent_failures):
        _print_agent_circuit_breaker(agent_failures)
        return "human_in_the_loop"
    return "observe"


@asynccontextmanager
async def create_ariadne_graph(
    checkpoint_path: Path | str | None = None,
    use_memory: bool = False,
):
    """Compile the Ariadne 2.0 StateGraph with persistent HITL checkpoints."""
    from src.automation.ariadne.graph._orchestrator_helpers import (
        _build_workflow_nodes,
        _add_workflow_edges,
        _compile_workflow,
    )

    workflow = StateGraph(AriadneState)
    _build_workflow_nodes(workflow)
    _add_workflow_edges(workflow)
    compiled = await _compile_workflow(workflow, use_memory, checkpoint_path)
    yield compiled
