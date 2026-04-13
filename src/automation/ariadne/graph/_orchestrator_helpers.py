"""Internal helpers for orchestrator - moved here for better organization."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.automation.ariadne.contracts.base import SnapshotResult
from src.automation.ariadne.models import (
    AriadneEdge,
    AriadneMap,
    AriadneState,
    AriadneTarget,
)

from src.automation.ariadne.repository import MapRepository
from src.automation.ariadne.modes.registry import ModeRegistry


def _patched_component_key(state_id: str, component_name: str) -> str:
    """Namespace heuristic patches to the state they belong to."""
    return f"{state_id}:{component_name}"


def _target_text_matches(target: AriadneTarget, element: Dict[str, Any]) -> bool:
    """Return whether an element satisfies the target text constraint."""
    if not target.text:
        return True
    return target.text.lower() in element.get("text", "").lower()


def _target_css_matches(target: AriadneTarget, element: Dict[str, Any]) -> bool:
    """Return whether an element satisfies the target css constraint."""
    if not target.css:
        return True
    return element.get("css") == target.css or element.get("selector") == target.css


def _target_has_matchers(target: AriadneTarget) -> bool:
    """Return whether the target defines any matching criteria."""
    return bool(target.text or target.css)


def _target_present_in_snapshot(
    target: AriadneTarget, snapshot: SnapshotResult
) -> bool:
    """Return whether a target is present in the snapshot DOM."""
    for element in snapshot.dom_elements:
        if not _target_has_matchers(target):
            continue
        if _target_text_matches(target, element) and _target_css_matches(
            target, element
        ):
            return True
    return False


def _url_matches(predicate: Any, snapshot: SnapshotResult) -> bool:
    """Return whether the snapshot URL satisfies the predicate."""
    if not predicate.url_contains:
        return True
    return predicate.url_contains in snapshot.url


def _presence_results(
    targets: List[AriadneTarget], snapshot: SnapshotResult
) -> List[bool]:
    """Evaluate target presence against the snapshot."""
    return [_target_present_in_snapshot(target, snapshot) for target in targets]


def _forbidden_results(
    targets: List[AriadneTarget], snapshot: SnapshotResult
) -> List[bool]:
    """Evaluate forbidden targets against the snapshot."""
    return [not _target_present_in_snapshot(target, snapshot) for target in targets]


def _evaluate_presence(predicate: Any, snapshot: SnapshotResult) -> bool:
    """Evaluate whether a state is present based on URL and DOM signals."""
    if not _url_matches(predicate, snapshot):
        return False
    req_results = _presence_results(predicate.required_elements, snapshot)
    forb_results = _forbidden_results(predicate.forbidden_elements, snapshot)
    all_results = req_results + forb_results
    if not all_results:
        return True
    if predicate.logical_op == "AND":
        return all(all_results)
    return any(all_results)


async def _adapter_snapshot(executor: Any) -> SnapshotResult:
    """Read browser state from either the legacy executor or the new adapter API."""
    if hasattr(executor, "perceive"):
        return await executor.perceive()
    return await executor.take_snapshot()


async def _adapter_execute(executor: Any, command: Any) -> Any:
    """Run a motor command through the executor API."""
    return await executor.execute(command)


def _executor_not_found() -> Dict[str, Any]:
    """Return the standard missing-executor error payload."""
    return {
        "errors": [
            "ExecutorNotFoundError: No executor instance provided in config['configurable']['executor']"
        ]
    }


def _snapshot_updates(snapshot: SnapshotResult) -> Dict[str, Any]:
    """Build state updates from a snapshot."""
    return {
        "current_url": snapshot.url,
        "dom_elements": snapshot.dom_elements,
        "screenshot_b64": snapshot.screenshot_b64,
    }


async def _identify_state(
    state: AriadneState,
    config: Any,
    snapshot: SnapshotResult,
) -> tuple[AriadneMap | None, str | None]:
    """Resolve the current state id from injected cognition or repository data."""
    labyrinth = config.get("configurable", {}).get("labyrinth")
    if labyrinth is not None:
        return labyrinth.ariadne_map, await labyrinth.identify_room(snapshot)
    repo = MapRepository()
    ariadne_map = await repo.get_map_async(state["portal_name"])
    return ariadne_map, _identify_from_map(ariadne_map, snapshot)


def _identify_from_map(ariadne_map: AriadneMap, snapshot: SnapshotResult) -> str | None:
    """Resolve the first matching state from a loaded map."""
    for state_id, state_def in ariadne_map.states.items():
        if _evaluate_presence(state_def.presence_predicate, snapshot):
            return state_id
    return None


def _apply_identified_state(
    updates: Dict[str, Any],
    identified_state_id: str | None,
) -> None:
    """Store the identified state id and print the corresponding log."""
    if identified_state_id:
        updates["current_state_id"] = identified_state_id
        print(f"--- OBSERVE: Identified state '{identified_state_id}' ---")
        return
    print("--- OBSERVE: Could not identify any state from map ---")


def _danger_dom_text(snapshot: SnapshotResult) -> str:
    """Flatten DOM text for danger detection."""
    return " ".join(
        el.get("text", "") for el in snapshot.dom_elements if el.get("text")
    )


def _danger_signals(snapshot: SnapshotResult) -> Any:
    """Build danger inspection input from the snapshot."""
    from src.automation.ariadne.danger_contracts import ApplyDangerSignals

    return ApplyDangerSignals(
        dom_text=_danger_dom_text(snapshot),
        current_url=snapshot.url,
    )


def _update_danger_memory(
    updates: Dict[str, Any],
    state: AriadneState,
    danger_report: Any,
) -> None:
    """Persist danger findings into session memory."""
    if not danger_report.findings:
        return
    primary = danger_report.primary
    print(f"--- OBSERVE: Danger detected [{primary.code}]: {primary.message} ---")
    new_memory = state.get("session_memory", {}).copy()
    new_memory["danger_detected"] = True
    new_memory["danger_findings"] = [
        finding.model_dump() for finding in danger_report.findings
    ]
    updates["session_memory"] = new_memory


def _mark_goal_achieved(
    updates: Dict[str, Any],
    state: AriadneState,
    identified_state_id: str | None,
    ariadne_map: AriadneMap | None,
) -> None:
    """Mark session memory when a success state is reached."""
    if not identified_state_id or not ariadne_map:
        return
    if identified_state_id not in ariadne_map.success_states:
        return
    print(f"--- OBSERVE: Goal achieved (state: {identified_state_id}) ---")
    new_memory = updates.get("session_memory", state.get("session_memory", {})).copy()
    new_memory["goal_achieved"] = True
    updates["session_memory"] = new_memory


async def _record_observe_event(
    config: Any,
    state: AriadneState,
    updates: Dict[str, Any],
    snapshot: SnapshotResult,
) -> None:
    """Record the observe event payload."""
    payload = {
        "portal_name": state.get("portal_name"),
        "current_mission_id": state.get("current_mission_id"),
        "current_state_id": updates.get(
            "current_state_id", state.get("current_state_id")
        ),
        "current_url": snapshot.url,
        "session_memory": updates.get(
            "session_memory", state.get("session_memory", {})
        ),
    }
    await _record_graph_event(config, "observe", payload)


async def _observe_updates(
    state: AriadneState,
    config: Any,
    executor: Any,
) -> Dict[str, Any]:
    """Build observe-node state updates."""
    snapshot = await _adapter_snapshot(executor)
    updates = _snapshot_updates(snapshot)
    ariadne_map, identified_state_id = await _safe_identify_state(
        state, config, snapshot
    )
    _apply_identified_state(updates, identified_state_id)
    from src.automation.ariadne.modes.registry import ModeRegistry

    mode = ModeRegistry.get_mode_for_url(snapshot.url)
    danger_report = await mode.inspect_danger(_danger_signals(snapshot))
    _update_danger_memory(updates, state, danger_report)
    _mark_goal_achieved(updates, state, identified_state_id, ariadne_map)
    await _record_observe_event(config, state, updates, snapshot)
    return updates


async def _safe_identify_state(
    state: AriadneState,
    config: Any,
    snapshot: SnapshotResult,
) -> tuple[AriadneMap | None, str | None]:
    """Resolve the current state while tolerating map-matching failures."""
    try:
        return await _identify_state(state, config, snapshot)
    except Exception as e:
        print(f"--- OBSERVE: Map matching skipped: {str(e)} ---")
        return None, None


def _get_patched_target(
    target: str,
    from_state_id: str,
    state: AriadneState,
) -> AriadneTarget | None:
    """Check JIT Patches in State for target."""
    patched_components = state.get("patched_components", {})
    scoped_key = _patched_component_key(from_state_id, target)
    return patched_components.get(scoped_key)


def _get_map_component_target(
    target: str,
    from_state_id: str,
    ariadne_map: AriadneMap,
) -> AriadneTarget | None:
    """Check Map components for target."""
    definition = ariadne_map.states.get(from_state_id)
    if definition and target in definition.components:
        return definition.components[target]
    return None


def _resolve_target(
    target: Union[str, AriadneTarget],
    from_state_id: str,
    ariadne_map: AriadneMap,
    state: AriadneState,
) -> AriadneTarget:
    """Resolves a target (component name or explicit target) to an AriadneTarget."""
    if isinstance(target, AriadneTarget):
        return target

    patched = _get_patched_target(target, from_state_id, state)
    if patched:
        return patched

    map_target = _get_map_component_target(target, from_state_id, ariadne_map)
    if map_target:
        return map_target

    raise ValueError(
        f"Target component '{target}' not found in state patches or map definition for state '{from_state_id}'."
    )


def _element_matches_target(target: AriadneTarget, element: Dict[str, Any]) -> bool:
    """Check if an element matches target text and CSS constraints."""
    if target.text and target.text.lower() not in element.get("text", "").lower():
        return False
    if target.css and target.css not in element.get("selector", ""):
        return False
    return bool(target.text or target.css)


def _is_target_present_in_snapshot(
    target: AriadneTarget, dom_elements: List[Dict[str, Any]]
) -> bool:
    """Check if a single target exists in the provided DOM snapshot."""
    for element in dom_elements:
        if _element_matches_target(target, element):
            return True
    return False


def _resolve_selector(element: Dict[str, Any]) -> str:
    """Get selector from element."""
    return element.get("selector") or element.get("css") or ""


def _get_element_value(element: Dict[str, Any]) -> str:
    """Get value from element."""
    return element.get("text") or element.get("value") or _resolve_selector(element)


def _extract_from_dom(
    selector: str, dom_elements: List[Dict[str, Any]]
) -> Optional[str]:
    """Resolve a selector-like key against the current DOM snapshot."""
    for element in dom_elements:
        if selector and selector == _resolve_selector(element):
            return _get_element_value(element)
    return None


def _extract_single_value(
    key: str,
    selector: str,
    command_output: dict,
    dom_elements: List[Dict[str, Any]],
) -> Any:
    """Extract a single value from command output or DOM."""
    extracted_value = command_output.get(key)
    if extracted_value is None:
        extracted_value = _extract_from_dom(selector, dom_elements)
    return extracted_value


def _collect_extracted_memory(
    edge: AriadneEdge,
    result: Any,
    state: AriadneState,
) -> Dict[str, Any]:
    """Build session-memory updates from edge extraction rules and command output."""
    if not edge.extract:
        return {}

    extracted_memory: Dict[str, Any] = {}
    command_output = getattr(result, "extracted_data", {}) or {}
    dom_elements = state.get("dom_elements", [])

    for key, selector in edge.extract.items():
        extracted_value = _extract_single_value(
            key, selector, command_output, dom_elements
        )
        if extracted_value is not None:
            extracted_memory[key] = extracted_value

    return extracted_memory


async def _record_graph_event(
    config: Any,
    event_type: str,
    payload: Dict[str, Any],
) -> None:
    """Persist one graph event when recording context is available."""
    configurable = config.get("configurable", {})
    thread_id = configurable.get("thread_id")
    if not thread_id or not configurable.get("record_graph", False):
        return

    from src.automation.ariadne.capabilities.recording import GraphRecorder

    recording_dir = configurable.get("recording_dir", "data/ariadne/recordings")
    recorder = GraphRecorder(recording_dir)
    await recorder.record_event_async(thread_id, event_type, payload)


def _get_candidate_edges(
    ariadne_map: AriadneMap,
    current_state_id: str,
    current_mission_id: str,
) -> List[AriadneEdge]:
    """Find all possible outgoing edges from current state."""
    return [
        edge
        for edge in ariadne_map.edges
        if edge.from_state == current_state_id
        and (edge.mission_id is None or edge.mission_id == current_mission_id)
    ]


def _filter_valid_edges(
    candidate_edges: List[AriadneEdge],
    ariadne_map: AriadneMap,
    state: AriadneState,
    dom_elements: List[Dict[str, Any]],
) -> List[AriadneEdge]:
    """Evaluate which edges are currently 'live' based on the snapshot."""
    valid_edges = []
    for edge in candidate_edges:
        try:
            resolved_target = _resolve_target(
                edge.target, edge.from_state, ariadne_map, state
            )
            if _is_target_present_in_snapshot(resolved_target, dom_elements):
                valid_edges.append(edge)
        except ValueError:
            continue
    return valid_edges


def _can_expand_batch(
    first_edge: AriadneEdge,
    candidate_edges: List[AriadneEdge],
    current_state_id: str,
) -> bool:
    """Check if batch can be expanded."""
    return len(candidate_edges) > 1 and first_edge.to_state == current_state_id


def _add_batchable_edge(
    edge: AriadneEdge,
    batch: List[AriadneEdge],
    ariadne_map: AriadneMap,
    state: AriadneState,
    max_batch: int,
) -> List[AriadneEdge]:
    """Try to add an edge to the batch if it's batchable."""
    if len(batch) >= max_batch:
        return batch
    if edge.intent not in [AriadneIntent.FILL, AriadneIntent.SELECT]:
        return batch
    if edge.from_state != batch[0].to_state or edge == batch[0]:
        return batch
    try:
        res_target = _resolve_target(edge.target, edge.from_state, ariadne_map, state)
        dom_elements = state.get("dom_elements", [])
        if _is_target_present_in_snapshot(res_target, dom_elements):
            return batch + [edge]
    except ValueError:
        pass
    return batch


def _build_micro_batch(
    first_edge: AriadneEdge,
    candidate_edges: List[AriadneEdge],
    current_state_id: str,
    ariadne_map: AriadneMap,
    state: AriadneState,
    max_batch: int,
) -> List[AriadneEdge]:
    """Build a micro-batch starting with the first valid edge."""
    if not _can_expand_batch(first_edge, candidate_edges, current_state_id):
        return [first_edge]

    batch = [first_edge]
    for edge in candidate_edges:
        batch = _add_batchable_edge(edge, batch, ariadne_map, state, max_batch)
    return batch


def _sort_valid_edges(
    valid_edges: List[AriadneEdge],
    current_mission_id: str,
    ariadne_map: AriadneMap,
    state: AriadneState,
) -> List[AriadneEdge]:
    """Sort valid edges by mission match and specificity."""
    return sorted(
        valid_edges,
        key=lambda edge: _score_edge(edge, current_mission_id, ariadne_map, state),
        reverse=True,
    )


def _find_safe_sequence(
    current_state_id: str,
    ariadne_map: AriadneMap,
    state: AriadneState,
    max_batch: int = 5,
) -> List[AriadneEdge]:
    """Find the next valid edge or a safe batch of edges."""
    current_mission_id = state.get("current_mission_id")
    dom_elements = state.get("dom_elements", [])

    candidate_edges = _get_candidate_edges(
        ariadne_map, current_state_id, current_mission_id
    )
    if not candidate_edges:
        return []

    valid_edges = _filter_valid_edges(candidate_edges, ariadne_map, state, dom_elements)
    if not valid_edges:
        return []

    valid_edges_sorted = _sort_valid_edges(
        valid_edges, current_mission_id, ariadne_map, state
    )

    return _build_micro_batch(
        valid_edges_sorted[0],
        candidate_edges,
        current_state_id,
        ariadne_map,
        state,
        max_batch,
    )


def _score_edge(
    edge: AriadneEdge,
    current_mission_id: str | None,
    ariadne_map: AriadneMap,
    state: AriadneState,
) -> tuple:
    """Return a sort key for deterministic edge selection."""
    mission_match = 1 if edge.mission_id == current_mission_id else 0
    return (mission_match, _target_specificity(edge, ariadne_map, state))


def _target_specificity(
    edge: AriadneEdge,
    ariadne_map: AriadneMap,
    state: AriadneState,
) -> int:
    """Return a specificity score for an edge target."""
    try:
        resolved = _resolve_target(edge.target, edge.from_state, ariadne_map, state)
    except ValueError:
        return 0
    if resolved.css:
        return 3
    if resolved.hint:
        return 2
    if resolved.text:
        return 1
    return 0


def _deterministic_executor(config: Any) -> Any:
    """Return the configured deterministic executor or adapter."""
    return config.get("configurable", {}).get("executor")


async def _load_deterministic_map(
    state: AriadneState,
    config: Any,
) -> AriadneMap:
    """Load the active Ariadne map for deterministic execution."""
    labyrinth = config.get("configurable", {}).get("labyrinth")
    if labyrinth is not None:
        return labyrinth.ariadne_map
    repo = MapRepository()
    return await repo.get_map_async(state["portal_name"])


def _live_thread_batch(
    state: AriadneState,
    ariadne_map: AriadneMap,
    ariadne_thread: Any,
) -> list[AriadneEdge]:
    """Filter thread-provided transitions to the edges present in the snapshot."""
    batch = ariadne_thread.get_next_steps(state.get("current_state_id"))
    dom_elements = state.get("dom_elements", [])
    return [
        edge for edge in batch if _edge_present(edge, ariadne_map, state, dom_elements)
    ]


def _edge_present(
    edge: AriadneEdge,
    ariadne_map: AriadneMap,
    state: AriadneState,
    dom_elements: list[Dict[str, Any]],
) -> bool:
    """Return whether an edge target is present in the current DOM snapshot."""
    try:
        resolved_target = _resolve_target(
            edge.target, edge.from_state, ariadne_map, state
        )
    except ValueError:
        return False
    return _is_target_present_in_snapshot(resolved_target, dom_elements)


def _deterministic_batch(
    state: AriadneState,
    config: Any,
    ariadne_map: AriadneMap,
) -> list[AriadneEdge]:
    """Resolve the next deterministic edge batch."""
    ariadne_thread = config.get("configurable", {}).get("ariadne_thread")
    if ariadne_thread is None:
        return _find_safe_sequence(state.get("current_state_id"), ariadne_map, state)
    return _live_thread_batch(state, ariadne_map, ariadne_thread)


def _translation_error(error: Exception) -> Dict[str, Any]:
    """Wrap a translation failure in the expected graph payload."""
    return {"errors": [f"TranslationError: {str(error)}"]}


def _translate_batch_command(
    batch: list[AriadneEdge],
    translator: Any,
    ariadne_map: AriadneMap,
    state: AriadneState,
) -> Any:
    """Translate a multi-edge batch into one motor command."""
    resolved_batch = [
        (_resolve_target(e.target, e.from_state, ariadne_map, state), e) for e in batch
    ]
    intents = [(edge.intent, target, edge.value) for target, edge in resolved_batch]
    return translator.translate_batch(intents, state)


def _translate_single_command(
    edge: AriadneEdge,
    translator: Any,
    ariadne_map: AriadneMap,
    state: AriadneState,
) -> Any:
    """Translate a single edge into a motor command."""
    target = _resolve_target(edge.target, edge.from_state, ariadne_map, state)
    return translator.translate_intent(edge.intent, target, state, edge.value)


def _translate_command(
    batch: list[AriadneEdge],
    translator: Any,
    ariadne_map: AriadneMap,
    state: AriadneState,
) -> Any:
    """Translate the selected batch into a motor command."""
    from src.automation.ariadne.models import AriadneIntent

    if len(batch) > 1:
        print(f"--- JIT Batching {len(batch)} intents ---")
        return _translate_batch_command(batch, translator, ariadne_map, state)
    return _translate_single_command(batch[0], translator, ariadne_map, state)


def _execution_failed(result: Any) -> Dict[str, Any] | None:
    """Return an execution failure payload when the result is unsuccessful."""
    if result.status != "failed":
        return None
    return {"errors": [f"ExecutionFailed: {_execution_error_message(result)}"]}


def _execution_error_message(result: Any) -> str:
    """Build the execution failure message."""
    if result.failed_at_index is not None:
        return f"Batch failed at index {result.failed_at_index}: {result.error}"
    return result.error or "Unknown error"


def _deterministic_updates(
    state: AriadneState,
    batch: list[AriadneEdge],
    result: Any,
) -> Dict[str, Any]:
    """Build deterministic state updates from the execution result."""
    updates = {"current_state_id": batch[-1].to_state, "errors": []}
    session_memory = state.get("session_memory", {}).copy()
    if session_memory.get("heuristic_retries"):
        session_memory["heuristic_retries"] = 0
    extracted_memory = _collect_extracted_memory(batch[-1], result, state)
    if extracted_memory:
        session_memory.update(extracted_memory)
    if session_memory != state.get("session_memory", {}):
        updates["session_memory"] = session_memory
    return updates


async def _record_deterministic_event(
    config: Any,
    state: AriadneState,
    batch: list[AriadneEdge],
    result: Any,
    updates: Dict[str, Any],
) -> None:
    """Record a deterministic execution event."""
    payload = {
        "portal_name": state.get("portal_name"),
        "current_mission_id": state.get("current_mission_id"),
        "state_before": {
            "current_state_id": state.get("current_state_id"),
            "profile_data": state.get("profile_data", {}),
            "job_data": state.get("job_data", {}),
        },
        "selected_edges": [edge.model_dump(mode="json") for edge in batch],
        "result": {
            "status": result.status,
            "error": result.error,
            "failed_at_index": result.failed_at_index,
            "completed_count": result.completed_count,
            "extracted_data": result.extracted_data,
        },
        "state_after": updates,
    }
    await _record_graph_event(config, "execute_deterministic", payload)


def _observe_next_step(session_memory: dict) -> str:
    """Return the next route after observe when the goal is not achieved."""
    if session_memory.get("danger_detected"):
        return "human_in_the_loop"
    return "execute_deterministic"


def _agent_should_escalate(
    state: AriadneState,
    session_memory: dict,
    agent_failures: int,
) -> bool:
    """Return whether the agent route should escalate to HITL."""
    return bool(
        state.get("errors") or session_memory.get("give_up") or agent_failures >= 3
    )


def _print_agent_circuit_breaker(agent_failures: int) -> None:
    """Print the agent circuit-breaker message."""
    print(f"--- CIRCUIT BREAKER: {agent_failures} agent failures. Routing to HITL. ---")

def _build_workflow_nodes(workflow: Any) -> None:
    """Add all nodes to the workflow."""
    from src.automation.ariadne.graph.orchestrator import (
        observe_node,
        execute_deterministic_node,
        apply_local_heuristics_node,
        llm_rescue_agent_node,
        human_in_the_loop_node,
    )
    workflow.add_node("observe", observe_node)
    workflow.add_node("execute_deterministic", execute_deterministic_node)
    workflow.add_node("apply_local_heuristics", apply_local_heuristics_node)
    workflow.add_node("llm_rescue_agent", llm_rescue_agent_node)
    workflow.add_node("human_in_the_loop", human_in_the_loop_node)


def _add_workflow_edges(workflow: Any) -> None:
    """Add all edges to the workflow."""
    from langgraph.graph import END
    from src.automation.ariadne.graph.orchestrator import (
        route_after_observe,
        route_after_deterministic,
        route_after_heuristics,
        route_after_agent,
    )
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


async def _compile_workflow(workflow: Any, use_memory: bool, checkpoint_path: Path | str | None) -> Any:
    """Compile the workflow with the appropriate checkpointer."""
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    if use_memory:
        checkpointer = MemorySaver()
        return workflow.compile(
            checkpointer=checkpointer,
            interrupt_before=["human_in_the_loop"],
        )

    resolved_path = Path(checkpoint_path or "data/ariadne/checkpoints.db")
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(
        str(resolved_path)
    ) as checkpointer:
        return workflow.compile(
            checkpointer=checkpointer,
            interrupt_before=["human_in_the_loop"],
        )

def _resolve_mode(state: AriadneState) -> Any:
    """Resolve the mode for the current portal."""
    from src.automation.ariadne.modes.registry import ModeRegistry

    mode_id = state.get("portal_mode") or state.get("current_url")
    return ModeRegistry.get_mode_for_url(mode_id)


async def _load_state_definition(state: AriadneState) -> AriadneMap:
    """Load the AriadneMap for the current portal."""
    from src.automation.ariadne.repository import MapRepository

    repo = MapRepository()
    return await repo.get_map_async(state["portal_name"])


def _extract_component_patches(
    patched_definition: Any,
    original_definition: Any,
    current_state_id: str,
) -> dict:
    """Extract components that differ between patched and original."""
    new_patches = {}
    for key, target in patched_definition.components.items():
        if key not in original_definition.components or original_definition.components[key] != target:
            patch_key = _patched_component_key(current_state_id, key)
            new_patches[patch_key] = target
    return new_patches


def _get_state_definition(ariadne_map: AriadneMap, state_id: str) -> Any:
    """Get the state definition for a given state ID."""
    return ariadne_map.states.get(state_id)


async def _apply_heuristic_patches(
    definition: Any,
    current_state_id: str,
    state: AriadneState,
    mode: Any,
) -> Dict[str, Any]:
    """Apply heuristic patches and return result."""
    import copy

    patched_definition = await mode.apply_local_heuristics(
        copy.deepcopy(definition), runtime_state=state
    )

    new_patches = _extract_component_patches(
        patched_definition, definition, current_state_id
    )

    return _build_heuristic_result(new_patches, current_state_id, state)


def _build_heuristic_result(
    new_patches: dict,
    current_state_id: str,
    state: AriadneState,
) -> Dict[str, Any]:
    """Create the result dict from heuristic patches."""
    if new_patches:
        session_memory = state.get("session_memory", {}).copy()
        session_memory["heuristic_retries"] = (
            session_memory.get("heuristic_retries", 0) + 1
        )
        print(
            f"--- HEURISTICS: Patched {len(new_patches)} components for state '{current_state_id}' ---"
        )
        return {
            "patched_components": new_patches,
            "session_memory": session_memory,
            "errors": [],
        }

    print(f"--- HEURISTICS: No local patches found for state '{current_state_id}' ---")
    return {}
