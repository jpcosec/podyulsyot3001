---
type: model
domain: ariadne
source: src/automation/ariadne/models.py:121
---

# Pill: AriadneState

## Structure
Key fields in `AriadneState` (TypedDict):

| Field | Type | Notes |
|---|---|---|
| `job_id` | `str` | Active job identifier |
| `portal_name` | `str` | e.g., 'linkedin', 'stepstone' |
| `profile_data` | `Dict` | User profile / CV data |
| `job_data` | `Dict` | Target job description data |
| `path_id` | `Optional[str]` | Active navigation path |
| `current_mission_id` | `Optional[str]` | Current mission goal |
| `current_state_id` | `str` | Active Labyrinth node ID |
| `dom_elements` | `List[Dict]` | Last captured DOM snapshot |
| `current_url` | `str` | Last captured URL |
| `screenshot_b64` | `Optional[str]` | Base64 encoded screenshot |
| `session_memory` | `Dict` | Read-write mission scratchpad |
| `errors` | `List[str]` | Append-only error log |
| `history` | `List[AnyMessage]` | LangGraph message history |
| `portal_mode` | `str` | Active heuristic strategy |
| `patched_components` | `Dict` | JIT patches for Labyrinth |

## Usage
Nodes return partial dicts to update the state.
```python
return {"session_memory": {**state["session_memory"], "new": "val"}}
```

## Verify
`grep "class AriadneState" src/automation/ariadne/models.py`
