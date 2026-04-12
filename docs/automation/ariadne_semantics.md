# Ariadne 2.0: LangGraph Flight Controller

## 1. The Graph State (AriadneState)
The state is the immutable, serializable working memory that passes between nodes. It uses reducers for error accumulation and history.

```python
class AriadneState(TypedDict):
    # Identity
    job_id: str
    portal_name: str
    
    # Context (Static)
    profile_data: dict[str, Any]
    
    # Deterministic Navigation
    path_id: str | None
    current_step_index: int
    
    # JIT Browser Snapshot
    dom_elements: list[dict]
    current_url: str
    screenshot_b64: str | None
    
    # Memory & Reducers
    errors: Annotated[list[str], operator.add]
    history: Annotated[list[AnyMessage], add_messages]
    
    # Active Strategy
    portal_mode: str  # e.g., "stepstone_default"
```

## 2. Component Taxonomy (SOLID Segregation)

- **Executors (Slaves)**: Purely deterministic primitives (Crawl4AI, Playwright). They receive an exact target/coordinate and execute. If the target is missing, they throw an immediate error.
- **Tools (Resolvers)**: Stateless utilities. `VisionTool` (screenshot -> coordinates), `HintingTool` (injects alphanumeric markers).
- **Planners (Agents)**: `BrowserOSAgent`. Receives the `AriadneState` and decides the next semantic action.

## 3. Graph Topology (Cost-Optimized Cascade)

Ariadne is a cyclic `StateGraph` with 4 levels of fallback:

1.  **Node: Observe**: Captures the JIT state (URL, Accessibility Tree, Screenshot).
2.  **Node: ExecuteDeterministic**: Replays the `AriadneMap` for the current index. Calls the Executor.
3.  **Node: ApplyLocalHeuristics**: If the deterministic node fails, applies local rules from the `portal_mode`.
4.  **Node: LLMRescueAgent**: If heuristics fail, the VLM Agent infers the next action using Hints + DOM.
5.  **Node: HumanInTheLoop**: Native LangGraph breakpoint (`interrupt_before`).

### Conditional Routing Logic:
- **After Observe**: `goal_achieved` -> `END`; `danger_detected` -> `HITL`; else -> `ExecuteDeterministic`.
- **After Deterministic**: `errors` -> `ApplyLocalHeuristics`; else -> `Observe` (Next step).
- **After Heuristics**: `errors` -> `LLMRescueAgent`; else -> `ExecuteDeterministic` (Retry with patch).
- **After Agent**: `errors` or `give_up` -> `HITL`; else -> `Observe` (Progress check).

## 4. Native Persistence & Time-Travel
Using LangGraph's `Checkpointer` (Memory/Postgres), every execution is versioned. If the `LLMRescueAgent` makes a mistake, the system can perform an "Architectural Undo" and resume from the last valid `Observe` state.

---

## Ariadne Modes (Contextual Injection)

Ariadne uses a **Mode Pattern** inspired by Nyxt to manage portal-specific behavior without polluting the core. A "Mode" is a set of rules and heuristics injected based on the current URL.

- **`DefaultMode`**: Uses LLMs for all normalization and extraction.
- **`PortalMode` (e.g., `StepStoneMode`)**: Overrides defaults with high-speed, local rules for that specific domain (cleaning locations, detecting employment types).
