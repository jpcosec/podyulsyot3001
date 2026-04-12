"""LangGraph StateGraph Controller for Ariadne 2.0.

This module implements the core JIT Flight Controller that orchestrates 
browser navigation using a cyclic graph with a 4-level fallback cascade.
"""

import asyncio
from typing import Any, Dict, List, Literal, Optional, Union

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langchain_core.runnables import RunnableConfig

from src.automation.ariadne.graph.nodes.agent import LangGraphBrowserOSAgent
from src.automation.ariadne.contracts.base import (
    CrawlCommand,
    ExecutionResult,
)
from src.automation.ariadne.models import (
    AriadneEdge,
    AriadneIntent,
    AriadneMap,
    AriadneState,
    AriadneTarget,
)
from src.automation.ariadne.repository import MapRepository
from src.automation.ariadne.translators.registry import TranslatorRegistry


# --- Node Functions ---


async def observe_node(state: AriadneState, config: RunnableConfig) -> Dict[str, Any]:
    """Captures the JIT state (URL, Accessibility Tree, Screenshot) via the active Executor."""
    print("--- NODE: Observe ---")
    executor = config.get("configurable", {}).get("executor")
    
    if not executor:
        return {
            "errors": ["ExecutorNotFoundError: No executor instance provided in config['configurable']['executor']"]
        }

    try:
        snapshot = await executor.take_snapshot()
        return {
            "current_url": snapshot.url,
            "dom_elements": snapshot.dom_elements,
            "screenshot_b64": snapshot.screenshot_b64,
        }
    except Exception as e:
        return {
            "errors": [f"ObservationError: {str(e)}"]
        }


def _find_safe_sequence(
    current_state_id: str, 
    ariadne_map: AriadneMap, 
    max_batch: int = 5
) -> List[AriadneEdge]:
    """Scans the graph for consecutive deterministic edges from the same state."""
    batch = []
    cursor = current_state_id
    
    for edge in ariadne_map.edges:
        if edge.from_state == cursor:
            # Only batch deterministic, non-waiting intents
            if edge.intent in [AriadneIntent.FILL, AriadneIntent.SELECT, AriadneIntent.CLICK]:
                batch.append(edge)
                cursor = edge.to_state
                if len(batch) >= max_batch or cursor != current_state_id:
                    # Stop if we hit limit or move to a different state
                    break
    return batch


async def execute_deterministic_node(state: AriadneState, config: RunnableConfig) -> Dict[str, Any]:
    """Replays the AriadneMap for the current node state with Micro-Batching."""
    print("--- NODE: Execute Deterministic ---")
    
    # 1. Resolve Executor
    executor = config.get("configurable", {}).get("executor")
    if not executor:
        return {"errors": ["ExecutorNotFoundError: No executor instance provided in config."]}

    # 2. Load Map
    repo = MapRepository()
    try:
        ariadne_map = repo.get_map(state["portal_name"])
    except Exception as e:
        return {"errors": [f"MapLoadError: {str(e)}"]}

    current_state_id = state.get("current_state_id")
    
    # 3. Identify Safe Sequence
    batch = _find_safe_sequence(current_state_id, ariadne_map)
    if not batch:
        return {"errors": [f"NoTransitionError: No edge found from {current_state_id}"]}

    # 4. Resolve Translator based on a provided hint or default
    motor_name = config.get("configurable", {}).get("motor_name", "crawl4ai")
    translator = TranslatorRegistry.get_translator_by_name(motor_name)

    # 5. Translate JIT (Atomic or Batch)
    if len(batch) > 1:
        print(f"--- JIT Batching {len(batch)} intents ---")
        batch_tuples = [(e.intent, e.target, e.value) for e in batch]
        command = translator.translate_batch(batch_tuples, state)
    else:
        edge = batch[0]
        command = translator.translate_intent(edge.intent, edge.target, state, edge.value)

    # 6. Dispatch to Executor
    print(f"--- Dispatching Command: {command} ---")
    try:
        result = await executor.execute(command)
        if result.status == "failed":
            return {
                "errors": [f"ExecutionFailed: {result.error or 'Unknown error'}"]
            }
    except Exception as e:
        return {
            "errors": [f"ExecutionError: {str(e)}"]
        }

    return {
        "current_state_id": batch[-1].to_state,
        "errors": []
    }


async def apply_local_heuristics_node(state: AriadneState, config: RunnableConfig) -> Dict[str, Any]:
    """Applies local rules from the active portal_mode (e.g. 'easy_apply')."""
    # TODO: Implement mode-based patching
    print("--- NODE: Apply Local Heuristics ---")
    return {}


async def llm_rescue_agent_node(state: AriadneState, config: RunnableConfig) -> Dict[str, Any]:
    """Infers the next action using Link Hints + DOM via VLM Agent (Direct MCP)."""
    print("--- NODE: LLM Rescue Agent (Direct MCP) ---")
    agent = LangGraphBrowserOSAgent()
    return await agent.run(state)


async def human_in_the_loop_node(state: AriadneState, config: RunnableConfig) -> Dict[str, Any]:
    """Native LangGraph breakpoint (interrupt_before)."""
    print("--- NODE: Human In The Loop ---")
    new_memory = state.get("session_memory", {}).copy()
    new_memory["human_intervention"] = True
    return {"session_memory": new_memory}


# --- Conditional Routing Functions ---


def route_after_observe(state: AriadneState) -> str:
    """Routing logic after observation."""
    session_memory = state.get("session_memory", {})
    if session_memory.get("goal_achieved"):
        return END
    
    if session_memory.get("danger_detected"):
        return "human_in_the_loop"
    
    return "execute_deterministic"


def route_after_deterministic(state: AriadneState) -> str:
    """Routing logic after deterministic execution."""
    if state.get("errors"):
        return "apply_local_heuristics"
    
    return "observe"


def route_after_heuristics(state: AriadneState) -> str:
    """Routing logic after heuristics application."""
    if state.get("errors"):
        return "llm_rescue_agent"
    
    return "execute_deterministic"


def route_after_agent(state: AriadneState) -> str:
    """Routing logic after LLM Agent execution with Circuit Breaker."""
    session_memory = state.get("session_memory", {})
    agent_failures = session_memory.get("agent_failures", 0)
    
    if state.get("errors") or session_memory.get("give_up") or agent_failures >= 3:
        print(f"--- CIRCUIT BREAKER: {agent_failures} agent failures. Routing to HITL. ---")
        return "human_in_the_loop"
    
    return "observe"


# --- Graph Construction ---


def create_ariadne_graph():
    """Compiles the Ariadne 2.0 StateGraph with memory and HITL."""
    workflow = StateGraph(AriadneState)

    workflow.add_node("observe", observe_node)
    workflow.add_node("execute_deterministic", execute_deterministic_node)
    workflow.add_node("apply_local_heuristics", apply_local_heuristics_node)
    workflow.add_node("llm_rescue_agent", llm_rescue_agent_node)
    workflow.add_node("human_in_the_loop", human_in_the_loop_node)

    workflow.set_entry_point("observe")

    workflow.add_conditional_edges(
        "observe",
        route_after_observe,
        {
            "execute_deterministic": "execute_deterministic",
            "human_in_the_loop": "human_in_the_loop",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "execute_deterministic",
        route_after_deterministic,
        {
            "apply_local_heuristics": "apply_local_heuristics",
            "observe": "observe"
        }
    )

    workflow.add_conditional_edges(
        "apply_local_heuristics",
        route_after_heuristics,
        {
            "llm_rescue_agent": "llm_rescue_agent",
            "execute_deterministic": "execute_deterministic"
        }
    )

    workflow.add_conditional_edges(
        "llm_rescue_agent",
        route_after_agent,
        {
            "human_in_the_loop": "human_in_the_loop",
            "observe": "observe"
        }
    )

    workflow.add_edge("human_in_the_loop", "observe")

    memory = MemorySaver()
    return workflow.compile(
        checkpointer=memory,
        interrupt_before=["human_in_the_loop"]
    )
