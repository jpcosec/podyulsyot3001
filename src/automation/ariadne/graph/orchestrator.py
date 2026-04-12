"""LangGraph StateGraph Controller for Ariadne 2.0.

This module implements the core JIT Flight Controller that orchestrates
browser navigation using a cyclic graph with a 4-level fallback cascade.
"""

import asyncio
import copy
from typing import Any, Dict, List, Literal, Optional, Union

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langchain_core.runnables import RunnableConfig

from src.automation.adapters.translators.registry import TranslatorRegistry
from src.automation.ariadne.graph.nodes.agent import LangGraphBrowserOSAgent
from src.automation.ariadne.contracts.base import (
    SnapshotResult,
)
from src.automation.ariadne.models import (
    AriadneEdge,
    AriadneIntent,
    AriadneMap,
    AriadneObserve,
    AriadneState,
    AriadneTarget,
)
from src.automation.ariadne.repository import MapRepository
from src.automation.ariadne.modes.registry import ModeRegistry
from src.automation.ariadne.danger_contracts import ApplyDangerSignals


def _patched_component_key(state_id: str, component_name: str) -> str:
    """Namespace heuristic patches to the state they belong to."""
    return f"{state_id}:{component_name}"


# --- Node Functions ---


def _evaluate_presence(predicate: AriadneObserve, snapshot: SnapshotResult) -> bool:
    """Evaluates if a state is present based on the snapshot (URL and DOM)."""

    def is_target_present(target: AriadneTarget) -> bool:
        # For a target to be present, ALL specified criteria (text, css)
        # must match at least one DOM element.
        for el in snapshot.dom_elements:
            match = True
            if target.text and target.text.lower() not in el.get("text", "").lower():
                match = False
            if (
                target.css
                and el.get("css") != target.css
                and el.get("selector") != target.css
            ):
                match = False

            # If at least one criteria was specified and it matched
            if match and (target.text or target.css):
                return True
        return False

    # 1. URL Matching
    if predicate.url_contains and predicate.url_contains not in snapshot.url:
        return False

    # 2. Element Matching
    req_results = [is_target_present(t) for t in predicate.required_elements]
    forb_results = [not is_target_present(t) for t in predicate.forbidden_elements]

    all_results = req_results + forb_results
    if not all_results:
        return True

    if predicate.logical_op == "AND":
        return all(all_results)
    return any(all_results)


async def observe_node(state: AriadneState, config: RunnableConfig) -> Dict[str, Any]:
    """Captures the JIT state (URL, Accessibility Tree, Screenshot) via the active Executor."""
    print("--- NODE: Observe ---")
    executor = config.get("configurable", {}).get("executor")

    if not executor:
        return {
            "errors": [
                "ExecutorNotFoundError: No executor instance provided in config['configurable']['executor']"
            ]
        }

    try:
        snapshot = await executor.take_snapshot()

        updates = {
            "current_url": snapshot.url,
            "dom_elements": snapshot.dom_elements,
            "screenshot_b64": snapshot.screenshot_b64,
        }

        # 1. State Identification
        repo = MapRepository()
        ariadne_map = None
        identified_state_id = None
        try:
            ariadne_map = repo.get_map(state["portal_name"])
            for state_id, state_def in ariadne_map.states.items():
                if _evaluate_presence(state_def.presence_predicate, snapshot):
                    identified_state_id = state_id
                    break

            if identified_state_id:
                updates["current_state_id"] = identified_state_id
                print(f"--- OBSERVE: Identified state '{identified_state_id}' ---")
            else:
                print("--- OBSERVE: Could not identify any state from map ---")
        except Exception as e:
            print(f"--- OBSERVE: Map matching skipped: {str(e)} ---")

        # 2. Danger Detection (CAPTCHAs, Security Blocks)
        mode = ModeRegistry.get_mode_for_url(snapshot.url)
        all_text = " ".join(
            [el.get("text", "") for el in snapshot.dom_elements if el.get("text")]
        )

        danger_signals = ApplyDangerSignals(
            dom_text=all_text,
            current_url=snapshot.url,
        )

        danger_report = mode.inspect_danger(danger_signals)
        if danger_report.findings:
            primary = danger_report.primary
            print(
                f"--- OBSERVE: Danger detected [{primary.code}]: {primary.message} ---"
            )

            new_memory = state.get("session_memory", {}).copy()
            new_memory["danger_detected"] = True
            new_memory["danger_findings"] = [
                f.model_dump() for f in danger_report.findings
            ]
            updates["session_memory"] = new_memory

        # 3. Goal Achievement Check
        if (
            identified_state_id
            and ariadne_map
            and identified_state_id in ariadne_map.success_states
        ):
            print(f"--- OBSERVE: Goal achieved (state: {identified_state_id}) ---")
            new_memory = updates.get(
                "session_memory", state.get("session_memory", {})
            ).copy()
            new_memory["goal_achieved"] = True
            updates["session_memory"] = new_memory

        return updates

    except Exception as e:
        return {"errors": [f"ObservationError: {str(e)}"]}


def _resolve_target(
    target: Union[str, AriadneTarget],
    from_state_id: str,
    ariadne_map: AriadneMap,
    state: AriadneState,
) -> AriadneTarget:
    """Resolves a target (component name or explicit target) to an AriadneTarget.

    Checks:
    1. JIT Patches in state['patched_components']
    2. Map components in definition for from_state_id
    """
    if isinstance(target, AriadneTarget):
        return target

    # 1. Check JIT Patches in State
    patched_components = state.get("patched_components", {})
    scoped_key = _patched_component_key(from_state_id, target)
    if scoped_key in patched_components:
        return patched_components[scoped_key]

    # 2. Check Map components
    definition = ariadne_map.states.get(from_state_id)
    if definition and target in definition.components:
        return definition.components[target]

    raise ValueError(
        f"Target component '{target}' not found in state patches or map definition for state '{from_state_id}'."
    )


def _is_target_present_in_snapshot(
    target: AriadneTarget, dom_elements: List[Dict[str, Any]]
) -> bool:
    """Checks if a single target exists in the provided DOM snapshot."""
    for el in dom_elements:
        match = True
        # Text and CSS must ALL match for a single element
        if target.text and target.text.lower() not in el.get("text", "").lower():
            match = False
        if target.css and target.css not in el.get("selector", ""):
            match = False

        if match and (target.text or target.css):
            return True
    return False


def _find_safe_sequence(
    current_state_id: str,
    ariadne_map: AriadneMap,
    state: AriadneState,
    max_batch: int = 5,
) -> List[AriadneEdge]:
    """
    Dynamically evaluates and finds the next valid edge or a safe batch of edges.

    An edge is valid if its target exists in the current snapshot.
    """
    dom_elements = state.get("dom_elements", [])

    # Find all possible outgoing edges
    candidate_edges = [e for e in ariadne_map.edges if e.from_state == current_state_id]

    # Evaluate which edges are currently "live" based on the snapshot
    valid_edges = []
    for edge in candidate_edges:
        try:
            resolved_target = _resolve_target(
                edge.target, edge.from_state, ariadne_map, state
            )
            if _is_target_present_in_snapshot(resolved_target, dom_elements):
                valid_edges.append(edge)
        except ValueError:
            # Target component name couldn't be resolved, so it's not present
            continue

    if not valid_edges:
        return []

    # TODO: Add mission-based priority logic here if multiple edges are valid.
    # For now, we take the first valid edge.
    first_edge = valid_edges[0]

    # Try to build a micro-batch starting with the first valid edge
    batch = [first_edge]
    cursor = first_edge.to_state

    if len(candidate_edges) > 1 and cursor == current_state_id:
        # Simple micro-batching: only look for more actions in the same state
        for edge in candidate_edges:
            if edge.from_state == cursor and edge != first_edge:
                if edge.intent in [AriadneIntent.FILL, AriadneIntent.SELECT]:
                    try:
                        res_target = _resolve_target(
                            edge.target, edge.from_state, ariadne_map, state
                        )
                        if _is_target_present_in_snapshot(res_target, dom_elements):
                            batch.append(edge)
                            if len(batch) >= max_batch:
                                break
                    except ValueError:
                        continue

    return batch


async def execute_deterministic_node(
    state: AriadneState, config: RunnableConfig
) -> Dict[str, Any]:
    """Replays the AriadneMap for the current node state with Micro-Batching and atomic fallback."""
    print("--- NODE: Execute Deterministic ---")

    executor = config.get("configurable", {}).get("executor")
    if not executor:
        return {
            "errors": [
                "ExecutorNotFoundError: No executor instance provided in config."
            ]
        }

    repo = MapRepository()
    try:
        ariadne_map = repo.get_map(state["portal_name"])
    except Exception as e:
        return {"errors": [f"MapLoadError: {str(e)}"]}

    current_state_id = state.get("current_state_id")
    batch = _find_safe_sequence(current_state_id, ariadne_map, state)
    if not batch:
        return {
            "errors": [
                f"NoTransitionError: No valid, live edge found from state '{current_state_id}'"
            ]
        }

    motor_name = config.get("configurable", {}).get("motor_name", "crawl4ai")
    translator = TranslatorRegistry.get_translator_by_name(motor_name)

    try:
        if len(batch) > 1:
            print(f"--- JIT Batching {len(batch)} intents ---")
            resolved_batch = [
                (_resolve_target(e.target, e.from_state, ariadne_map, state), e)
                for e in batch
            ]
            command = translator.translate_batch(
                [(e.intent, target, e.value) for target, e in resolved_batch], state
            )
        else:
            edge = batch[0]
            res_target = _resolve_target(
                edge.target, edge.from_state, ariadne_map, state
            )
            command = translator.translate_intent(
                edge.intent, res_target, state, edge.value
            )
    except Exception as e:
        return {"errors": [f"TranslationError: {str(e)}"]}

    print(f"--- Dispatching Command: {command} ---")
    try:
        result = await executor.execute(command)

        if result.status == "failed":
            # Micro-batch failure detection
            if (
                result.failed_at_index is not None
                and result.failed_at_index >= 0
                and len(batch) > 1
            ):
                fail_idx = result.failed_at_index
                print(
                    f"--- Batch failed at index {fail_idx}. Retrying remaining actions atomically. ---"
                )

                # Retry remaining actions one-by-one
                remaining_batch = batch[fail_idx:]
                for i, edge in enumerate(remaining_batch):
                    print(f"--- Retrying action {fail_idx + i}: {edge.intent} ---")
                    try:
                        res_target = _resolve_target(
                            edge.target, edge.from_state, ariadne_map, state
                        )
                        atomic_cmd = translator.translate_intent(
                            edge.intent, res_target, state, edge.value
                        )
                        atomic_result = await executor.execute(atomic_cmd)

                        if atomic_result.status == "failed":
                            error_msg = f"Atomic retry failed for action {fail_idx + i}: {atomic_result.error}"
                            return {"errors": [f"ExecutionFailed: {error_msg}"]}
                    except Exception as e:
                        return {"errors": [f"ExecutionError on retry: {str(e)}"]}

                # If all retries succeed, the state is the one from the last successful action of the *original* batch
                return {"current_state_id": batch[-1].to_state, "errors": []}
            else:
                return {
                    "errors": [f"ExecutionFailed: {result.error or 'Unknown error'}"]
                }

    except Exception as e:
        return {"errors": [f"ExecutionError: {str(e)}"]}

    return {"current_state_id": batch[-1].to_state, "errors": []}


async def apply_local_heuristics_node(
    state: AriadneState, config: RunnableConfig
) -> Dict[str, Any]:
    """Applies local rules from the active portal_mode (e.g. 'easy_apply')."""
    print("--- NODE: Apply Local Heuristics ---")

    # 1. Resolve PortalMode
    from src.automation.ariadne.modes.registry import ModeRegistry

    mode_id = state.get("portal_mode") or state.get("current_url")
    mode = ModeRegistry.get_mode_for_url(mode_id)

    # 2. Load Map to get current state definition
    repo = MapRepository()
    try:
        ariadne_map = repo.get_map(state["portal_name"])
    except Exception as e:
        return {"errors": [f"MapLoadError: {str(e)}"]}

    current_state_id = state.get("current_state_id")
    definition = ariadne_map.states.get(current_state_id)
    if not definition:
        return {"errors": [f"StateDefinitionNotFoundError: {current_state_id}"]}

    # 3. Apply heuristics (using a deep copy to be safe)
    patched_definition = mode.apply_local_heuristics(
        copy.deepcopy(definition), runtime_state=state
    )

    # 4. Extract new patches (components that differ from the original map)
    new_patches = {}
    for key, target in patched_definition.components.items():
        if key not in definition.components or definition.components[key] != target:
            patch_key = _patched_component_key(current_state_id, key)
            new_patches[patch_key] = target

    if new_patches:
        print(
            f"--- HEURISTICS: Patched {len(new_patches)} components for state '{current_state_id}' ---"
        )
        # Clear errors if we found patches to attempt retry
        return {"patched_components": new_patches, "errors": []}

    print(f"--- HEURISTICS: No local patches found for state '{current_state_id}' ---")
    return {}


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
        print(
            f"--- CIRCUIT BREAKER: {agent_failures} agent failures. Routing to HITL. ---"
        )
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
    return workflow.compile(checkpointer=memory, interrupt_before=["human_in_the_loop"])
