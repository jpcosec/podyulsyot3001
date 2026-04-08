# BrowserOS Level 2 Trace Contract

Date: 2026-04-08
Status: design-only

## Purpose

Contracts for recording BrowserOS Level 2 agent sessions from the direct `/chat`
SSE stream. This is the boundary between BrowserOS agent execution and the
Ariadne recording pipeline.

Unlike deterministic MCP replay capture, these contracts preserve a higher-level
agent trace first and normalize it later.

## Session contract

### BrowserOSLevel2SessionConfig

Configuration to start a BrowserOS Level 2 agent session.

```python
class BrowserOSLevel2SessionConfig(BaseModel):
    source: str                              # portal name
    goal: str                                # natural-language objective
    provider: str                            # browseros/openai/anthropic/etc.
    model: str
    mode: Literal["chat", "agent"] = "agent"
    entry_url: str | None = None             # optional starting page
    profile_data: dict | None = None         # placeholder detection later
    job_data: dict | None = None
    browser_context: dict | None = None
    user_system_prompt: str | None = None
    user_working_dir: str | None = None
    max_duration_seconds: float | None = None
```

### BrowserOSLevel2SessionResult

Outcome of a Level 2 BrowserOS session.

```python
class BrowserOSLevel2SessionResult(BaseModel):
    conversation_id: str
    status: Literal["completed", "aborted", "failed", "rate_limited"]
    started_at: str
    ended_at: str | None = None
    final_text: str | None = None
    finish_reason: str | None = None
    recording_path: Path | None = None
    evidence_paths: list[str] = []
    error: str | None = None
```

## Raw stream event contracts

### BrowserOSLevel2StreamEvent

One SSE event from BrowserOS `/chat`.

```python
class BrowserOSLevel2StreamEvent(BaseModel):
    timestamp: str
    conversation_id: str
    event_type: str
    payload: dict
```

### BrowserOSReasoningEvent

```python
class BrowserOSReasoningEvent(BaseModel):
    reasoning_id: str
    phase: Literal["start", "delta", "end"]
    delta: str | None = None
```

### BrowserOSTextEvent

```python
class BrowserOSTextEvent(BaseModel):
    text_id: str
    phase: Literal["start", "delta", "end"]
    delta: str | None = None
```

### BrowserOSToolCallEvent

Normalized BrowserOS tool-call event extracted from SSE.

```python
class BrowserOSToolCallEvent(BaseModel):
    tool_call_id: str
    tool_name: str
    phase: Literal[
        "tool-input-start",
        "tool-input-delta",
        "tool-input-available",
        "tool-output-available",
    ]
    input: dict | None = None
    input_text_delta: str | None = None
    output: dict | None = None
    is_error: bool | None = None
```

### BrowserOSFinishEvent

```python
class BrowserOSFinishEvent(BaseModel):
    finish_reason: str | None = None
```

## Trace artifact contracts

### BrowserOSLevel2Trace

Raw Level 2 trace stored before Ariadne normalization.

```python
class BrowserOSLevel2Trace(BaseModel):
    conversation_id: str
    source: str
    goal: str
    provider: str
    model: str
    mode: Literal["chat", "agent"]
    started_at: str
    ended_at: str | None = None
    stream_events: list[BrowserOSLevel2StreamEvent]
    final_text: str | None = None
    finish_reason: str | None = None
    evidence_paths: list[str] = []
```

### BrowserOSLevel2StepCandidate

Intermediate normalized candidate from one or more Level 2 tool events.

```python
class BrowserOSLevel2StepCandidate(BaseModel):
    step_index: int
    tool_events: list[BrowserOSToolCallEvent]
    candidate_intent: str | None = None
    target_hint: str | None = None
    value_hint: str | None = None
    requires_review: bool = False
    review_reason: str | None = None
```

## Normalization rules

- Store raw SSE first; do not collapse directly into Ariadne actions during capture.
- Treat BrowserOS tool arguments that contain element IDs as unstable unless paired
  with same-step resolution evidence.
- Preserve reasoning and final text for diagnostics, but do not treat them as
  deterministic replay instructions.
- Promote only normalized step candidates into Ariadne draft paths.

## Relationship to other contracts

- `motor_browseros_agent.md` defines the high-level BrowserOS agent motor boundary.
- `recording.md` defines the shared pipeline internals after raw capture.
- This document defines the BrowserOS-specific Level 2 raw trace boundary between them.
