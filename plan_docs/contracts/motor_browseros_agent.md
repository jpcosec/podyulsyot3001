# BrowserOS Agent Motor Contracts

Date: 2026-04-05
Status: design-only

## Purpose

Contracts for the BrowserOS Agent motor. This motor is special: it doesn't
consume Ariadne paths via a translator — it produces them via the recording
pipeline. These contracts define the agent session interface and what the
recording pipeline receives.

For the BrowserOS `/chat` SSE stream contract specifically, see
`plan_docs/contracts/browseros_level2_trace.md`.

## Session contracts

### AgentSessionConfig

Configuration to start an agent recording session.

```python
class AgentSessionConfig(BaseModel):
    source: str                      # portal name
    entry_url: str                   # where to start navigating
    profile_data: dict               # candidate profile for {{placeholder}} detection
    job_data: dict | None = None     # job context for {{placeholder}} detection
    max_steps: int | None = None     # agent step limit
    recording_enabled: bool = True   # should the recording pipeline attach?
```

### AgentSessionResult

Outcome of an agent session.

```python
class AgentSessionResult(BaseModel):
    session_id: str
    status: Literal["completed", "aborted", "failed"]
    steps_executed: int
    hitl_interactions: int           # how many times the agent asked for human help
    recording_path: Path | None      # path to draft AriadnePath (if recording was enabled)
    error: str | None = None
```

## Recording pipeline input

These contracts define what the recording pipeline receives from the MCP proxy
during an agent session.

Direct BrowserOS `/chat` stream capture is specified separately in
`plan_docs/contracts/browseros_level2_trace.md`.

### McpProxyEvent

One intercepted MCP tool call (request + response pair).

```python
class McpProxyEvent(BaseModel):
    timestamp: str                   # ISO timestamp
    request_id: int
    tool_name: str                   # BrowserOS MCP tool name
    arguments: dict                  # tool call arguments
    result: dict | None = None       # tool call result (None if call failed)
    error: str | None = None         # error message if call failed
    duration_ms: int | None = None   # round-trip time
```

### McpProxySnapshot

A parsed snapshot captured during the session (from `take_snapshot` calls).

```python
class McpProxySnapshot(BaseModel):
    timestamp: str
    request_id: int                  # which McpProxyEvent produced this
    elements: list[SnapshotElement]  # parsed element list
```

Uses the existing `SnapshotElement` dataclass from `src/apply/browseros_client.py`:
```python
@dataclass(frozen=True)
class SnapshotElement:
    element_id: int
    element_type: str
    text: str
    raw_line: str
```

### HitlEvent

A human-in-the-loop interaction during an agent session.

```python
class HitlEvent(BaseModel):
    timestamp: str
    interact_type: Literal["confirm", "input", "select", "request_help"]
    help_type: str | None = None     # "request_login", "request_assistance" (for request_help)
    prompt: str                      # what the agent asked
    response: str | bool | list[str] | None = None  # what the human answered
    resolved: bool = True            # did the human resolve the issue?
```

## Agent script contracts

### AgentScript

Metadata for an OpenBrowser agent script deployed to the graph directory.

```python
class AgentScript(BaseModel):
    script_id: str                   # directory name in graph/
    source: str                      # which portal this script targets
    flow: str                        # which flow (easy_apply, standard, etc.)
    script_path: Path                # full path to graph.ts
    profile_variables: list[str]     # {{varName}} placeholders used in the script
```

This is a reference contract, not something the agent framework consumes — it
tracks which scripts we've deployed and what they expect.

## Current equivalents

| Contract | Current code | Location |
|---|---|---|
| `AgentSessionConfig` | (no equivalent — agent path not implemented) | — |
| `AgentSessionResult` | (no equivalent) | — |
| `McpProxyEvent` | (no equivalent — proxy not implemented) | — |
| `McpProxySnapshot` | `list[SnapshotElement]` return from `take_snapshot()` | `src/apply/browseros_client.py` |
| `HitlEvent` | (no equivalent — HITL routing not implemented) | — |
| `AgentScript` | (no equivalent — graph/ integration not implemented) | — |

Everything here is new — the agent motor has no code today.
