# Interpreter Node: LangGraph Entry Point for Natural Language Instructions

**Explanation:** The graph entry point must be a dedicated node that resolves a natural language instruction to a `mission_id` before any navigation happens. Currently the graph starts blind at `observe`.

**Reference:** `src/automation/ariadne/graph/orchestrator.py:618`, `src/automation/ariadne/models.py`, `src/automation/ariadne/graph/nodes/`

**Status:** Not started. Node file does not exist.

### 📦 Required Context Pills
- [Node Implementation Pattern](../context/node-pattern.md)
- [Structured Output Pattern (VLM/LLM)](../context/structured-output-pattern.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Log Tags & Observability](../context/log-tags.md)
- [Gemini Flash Default LLM](../context/gemini-flash-default.md)
- [LangGraph Flight Controller](../context/ariadne-langgraph.md)

### 🚫 Non-Negotiable Constraints (Laws of Physics)

1. **Law 1 (No Blocking I/O):** The `parse_instruction_node` must be fully `async`. Use `await repo.get_map_async(portal_name)`. Do not use `open()` or synchronous `json.load()`.
2. **Law 4 (Finite Routing):** The interpreter must always return a valid `current_mission_id`. If resolution fails, it must fall back to a safe default (e.g., `"discovery"`) rather than erroring out and breaking the graph.
3. **DIP Enforcement:** `interpreter.py` must only import from `ariadne/` domain layers (`models.py`, `repository.py`, `config.py`). Imports from `src/automation/motors/` are strictly prohibited.

**Why it's wrong:** `workflow.set_entry_point("observe")` skips intent resolution entirely. `AriadneState` has no `instruction` field, so there is no way to carry user intent through the graph. The agent node hardcodes `"Goal: Continue the application process."` regardless of what the user asked.

**Real fix:**
1. Add `instruction: str` to `AriadneState` in `models.py`.
2. Create `src/automation/ariadne/graph/nodes/interpreter.py` with `parse_instruction_node`.
3. Fast path: if `instruction` exactly matches a known `mission_id` in the map, return it directly.
4. Slow path: call Gemini Flash with structured output (`MissionResolution` Pydantic model) to map intent → `mission_id` + `dry_run` flag.
5. In `orchestrator.py`: `workflow.add_node("parse_instruction", parse_instruction_node)`, change `set_entry_point` to `"parse_instruction"`, add `add_edge("parse_instruction", "observe")`.

**Don't:** Put instruction parsing logic inside `main.py` or `observe_node` — it must be a first-class LangGraph node so it's recorded, testable, and skippable in tests.

**Steps:**
1. Add `instruction: str` to `AriadneState`.
2. Create `interpreter.py` with `MissionResolution` Pydantic schema and `parse_instruction_node`.
3. Wire into orchestrator.
4. Update `main.py` initial state to include `"instruction": args.instruction`.
5. Write unit test for the fast path (exact `mission_id` match, no LLM call).

**Reference implementation:**

`src/automation/ariadne/models.py` — add to top of `AriadneState`:
```python
class AriadneState(TypedDict):
    instruction: str  # natural language order from the user
    job_id: str
    portal_name: str
    # ... rest unchanged
```

`src/automation/ariadne/graph/nodes/interpreter.py` — create new file:
```python
"""Instruction parser node for Ariadne 2.0."""

from typing import Any, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from src.automation.ariadne.models import AriadneState
from src.automation.ariadne.repository import MapRepository
from src.automation.ariadne.config import get_gemini_model


class MissionResolution(BaseModel):
    mission_id: str = Field(description="The exact mission_id found in the map.")
    dry_run: bool = Field(description="True if the user implicitly asked to not submit/finish.")


async def parse_instruction_node(state: AriadneState) -> Dict[str, Any]:
    """Interprets natural language and maps it to a mission_id from the static map."""
    print("--- NODE: Parse Instruction ---")

    instruction = state.get("instruction", "").strip()
    portal_name = state.get("portal_name")

    repo = MapRepository()
    try:
        ariadne_map = await repo.get_map_async(portal_name)
        available_missions = list(set(
            edge.mission_id for edge in ariadne_map.edges if edge.mission_id
        ))
    except Exception:
        available_missions = ["discovery", "easy_apply"]

    # Fast path: exact mission_id match
    if instruction in available_missions:
        print(f"--- INTERPRETER: Exact mission detected '{instruction}' ---")
        return {"current_mission_id": instruction}

    # Slow path: LLM intent resolution
    print(f"--- INTERPRETER: Resolving intent '{instruction}' ---")
    llm = ChatGoogleGenerativeAI(model=get_gemini_model()).with_structured_output(MissionResolution)

    prompt = (
        f"The user wants to perform the following action on portal '{portal_name}': '{instruction}'.\n"
        f"Available missions on this portal: {available_missions}.\n"
        "Map the user's intent to the correct mission and determine if it's a dry-run."
    )

    try:
        resolution = await llm.ainvoke(prompt)
        new_memory = state.get("session_memory", {}).copy()
        new_memory["dry_run"] = resolution.dry_run
        print(f"--- INTERPRETER: Resolved to '{resolution.mission_id}' (dry_run={resolution.dry_run}) ---")
        return {"current_mission_id": resolution.mission_id, "session_memory": new_memory}
    except Exception as e:
        print(f"--- INTERPRETER ERROR: {e}. Falling back ---")
        return {"current_mission_id": available_missions[0] if available_missions else "easy_apply"}
```

`src/automation/ariadne/graph/orchestrator.py` — changes to `create_ariadne_graph`:
```python
from src.automation.ariadne.graph.nodes.interpreter import parse_instruction_node

# Inside create_ariadne_graph():
workflow.add_node("parse_instruction", parse_instruction_node)
workflow.add_node("observe", observe_node)
# ... rest of add_node calls unchanged

workflow.set_entry_point("parse_instruction")       # was: "observe"
workflow.add_edge("parse_instruction", "observe")   # new edge
# ... rest of add_conditional_edges unchanged
```

**Note:** Use `get_map_async()` (not `get_map()`), consistent with `observe_node`.
