---
type: model
domain: ariadne
source: src/automation/ariadne/models.py:121
---

# Pill: AriadneState

## Structure
Key fields agents read/write (`models.py:121`):

| Field | Type | Notes |
|---|---|---|
| `current_mission_id` | `Optional[str]` | Active mission gate |
| `current_state_id` | `str` | Current AriadneMap node |
| `dom_elements` | `List[Dict]` | Snapshot of interactive elements |
| `screenshot_b64` | `Optional[str]` | Base64; set after hint injection |
| `session_memory` | `Dict[str, Any]` | Scratchpad — holds counters + extractions |
| `errors` | `List[str]` | Append-only reducer — never overwrite |
| `history` | `List[AnyMessage]` | Append via `add_messages` reducer |

Key counters inside `session_memory`:
- `heuristic_retries` — incremented by heuristics node, triggers LLM at `>= 2`
- `agent_failures` — incremented by agent node, triggers HITL at `>= 3`

## Usage
Nodes return a **partial dict** — only changed fields. LangGraph merges it.

```python
async def my_node(state: AriadneState) -> Dict[str, Any]:
    new_memory = {**state.get("session_memory", {}), "my_key": "value"}
    return {
        "session_memory": new_memory,
        "errors": state.get("errors", []) + ["optional error"],
    }
```

## Verify
```bash
grep -n "class AriadneState" src/automation/ariadne/models.py
```
