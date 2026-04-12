# Ariadne 2.0: Architecture & State Graph

## 1. Overview
Ariadne 2.0 is a **Programmable Semantic Browser** built on LangGraph. It functions as a **Just-In-Time (JIT) Flight Controller** that orchestrates browser navigation through a directed graph of states. It replaces the previous linear step-recorder model with a dynamic, state-aware navigation engine.

## 2. The Graph State (`AriadneState`)
The state is the immutable, serializable working memory that passes between nodes. It handles all working memory, profile data, and dynamic extractions.

```python
from typing import Annotated, TypedDict, Any
import operator
from langgraph.graph.message import AnyMessage, add_messages

class AriadneState(TypedDict):
    # Identity
    job_id: str
    portal_name: str
    
    # Context (Static injection)
    profile_data: dict[str, Any]
    job_data: dict[str, Any]
    
    # Navigation Pointer
    path_id: str | None
    current_state_id: str
    
    # JIT Browser Snapshot
    dom_elements: list[dict]
    current_url: str
    screenshot_b64: str | None
    
    # session_memory: Read-write memory for extractions (e.g. Application IDs)
    session_memory: dict[str, Any]
    
    # Memory & Reducers
    errors: Annotated[list[str], operator.add]
    history: Annotated[list[AnyMessage], add_messages]
    
    # Active Strategy (Injected via URL context)
    portal_mode: str
```

## 3. Graph Topology (Cost-Optimized Cascade)
Ariadne is a cyclic `StateGraph` with 4 levels of fallback:

1.  **Node: Observe**: Captures the JIT state (URL, Accessibility Tree, Screenshot).
2.  **Node: ExecuteDeterministic**: Replays the `AriadneMap` for the current node. Calls the Executor.
3.  **Node: ApplyLocalHeuristics**: If the deterministic node fails, applies local rules from the active `portal_mode`.
4.  **Node: LLMRescueAgent**: If heuristics fail, the VLM Agent infers the next action using Link Hints + DOM.
5.  **Node: HumanInTheLoop**: Native LangGraph breakpoint (`interrupt_before`).

### Conditional Routing (Conditional Edges):
- **After Observe**: `goal_achieved` -> `END`; `danger_detected` -> `HumanInTheLoop`; else -> `ExecuteDeterministic`.
- **After Deterministic**: `errors` -> `ApplyLocalHeuristics`; else -> `Observe` (Next node).
- **After Heuristics**: `errors` -> `LLMRescueAgent`; else -> `ExecuteDeterministic` (Retry with patch).
- **After Agent**: `errors` or `give_up` -> `HumanInTheLoop`; else -> `Observe` (Progress check).

## 4. Common Language Models

### AriadneMap (Exploration Memory)
> **CRITICAL**: Maps are NOT hand-written JSON. They're built through exploration:
> 1. Crawl/Explore page → LLM traces action → HITL → Human guides → union of traces = map

```python
class AriadneMap(BaseModel):
    meta: AriadneMapMeta
    states: dict[str, AriadneStateDefinition] # Nodes (from traces)
    edges: list[AriadneEdge]                  # Transitions (from traces)
    success_states: list[str]
    failure_states: list[str]
```

### AriadneStateDefinition (Discovered Node)
```python
class AriadneStateDefinition(BaseModel):
    id: str
    description: str
    presence_predicate: AriadneObserve   # Logic to identify this node
    components: dict[str, AriadneTarget] # Named elements (from trace)
```

### AriadneEdge (Discovered Intent)
```python
class AriadneEdge(BaseModel):
    from_state: str
    to_state: str
    intent: AriadneIntent
    target: str | AriadneTarget
    value: str | None = None
    extract: dict[str, str] | None = None # key -> selector for blackboard write
```

## 5. Persistence & Time-Travel
Using LangGraph's **Checkpointer**, every execution is versioned.
- ** thread_id = job_id**: Ensures continuity.
- **Architectural Undo**: If the LLM Agent mis-navigates, the system can revert the state to the last valid `Observe` node and pass control to the human.
