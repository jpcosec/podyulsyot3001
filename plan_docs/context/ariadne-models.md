---
type: model
domain: ariadne
source: src/automation/ariadne/models.py:121
lifecycle: current
---

# Pill: AriadneState

## Structure
Key fields in `AriadneState` (TypedDict) at `models.py:121`:

| Field | Type | Notes |
|---|---|---|
| `job_id` | `str` | Active job identifier |
| `portal_name` | `str` | e.g., 'linkedin', 'stepstone' |
| `profile_data` | `Dict` | User profile data |
| `job_data` | `Dict` | Job-specific data (CV path, etc) |
| `path_id` | `Optional[str]` | Active navigation path trace |
| `current_mission_id` | `Optional[str]` | Goal to resolve (e.g., 'easy_apply') |
| `current_state_id` | `str` | Last identified Labyrinth node |
| `dom_elements` | `List[Dict]` | Last captured DOM snapshot |
| `current_url` | `str` | Last captured browser URL |
| `screenshot_b64` | `Optional[str]` | Base64 encoded screenshot |
| `session_memory` | `Dict` | Mission scratchpad |
| `errors` | `List[str]` | Append-only error reducer |
| `history` | `List[AnyMessage]` | LangGraph message history |
| `portal_mode` | `str` | Active heuristic profile |
| `patched_components` | `Dict` | JIT patches (state_id:name) |

## Usage
Nodes return partial dicts for state merging.

## Verify
`grep -n "class AriadneState" src/automation/ariadne/models.py`
