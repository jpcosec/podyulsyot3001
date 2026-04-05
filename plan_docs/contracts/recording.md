# Recording Pipeline Contracts

Date: 2026-04-05
Status: design-only

## Purpose

Internal contracts for the recording pipeline. These define the data structures
used between the pipeline stages (watch → record → process → update). Motor-specific
input contracts (McpProxyEvent, CdpCaptureEvent) are defined in their respective
motor contract docs — this document covers the shared pipeline internals.

## Pipeline stage contracts

### RawRecordingEvent

The unified event format in the raw timeline. All motor-specific events normalize
to this shape before processing.

```python
class RawRecordingEvent(BaseModel):
    timestamp: str
    source: Literal["mcp_proxy", "cdp", "human_annotation", "snapshot"]
    event_type: str                  # "tool_call", "click", "change", "navigate", "snapshot", "annotation"
    data: dict                       # event-specific payload (McpProxyEvent, CdpClickData, etc.)
```

### RecordingTimeline

The complete raw recording for one session.

```python
class RecordingTimeline(BaseModel):
    session_id: str
    source: str                      # portal name
    motor: Literal["browseros_agent", "human"]
    started_at: str
    ended_at: str | None = None
    events: list[RawRecordingEvent]
```

Stored as JSON lines (`.jsonl`) for append-only writes during capture, or as
a single JSON file after session ends.

### CorrelatedStep

Intermediate representation after correlation (stage 3). Raw events grouped
into logical steps, with element identities stabilized but not yet normalized
to Ariadne common language.

```python
class CorrelatedStep(BaseModel):
    step_index: int
    boundary_reason: Literal["navigation", "snapshot_gap", "time_gap", "annotation"]
    events: list[RawRecordingEvent]          # raw events in this step
    snapshot_before: list[SnapshotElement]    # snapshot at step start
    snapshot_after: list[SnapshotElement] | None = None  # snapshot at step end
    screenshot_path: str | None = None
    annotations: list[dict] = []             # human annotations attached to this step
```

### NormalizationResult

Output of the process stage. Contains the normalized AriadnePath plus diagnostics.

```python
class NormalizationResult(BaseModel):
    path: AriadnePath                        # the normalized path (status: draft)
    confidence: float                        # overall normalization confidence (0.0–1.0)
    unresolved_values: list[UnresolvedValue] # literals that couldn't be matched to templates
    warnings: list[str]                      # non-fatal normalization issues
```

### UnresolvedValue

A literal value in the recording that couldn't be matched to a `{{placeholder}}`.

```python
class UnresolvedValue(BaseModel):
    step: int
    action_index: int
    field: Literal["target", "value"]
    raw_value: str
    suggestion: str | None = None    # best-guess placeholder (if close to a profile field)
```

These are flagged for human review during path correction.

## Session metadata

### RecordingSessionMeta

Metadata stored alongside the recording artifacts.

```python
class RecordingSessionMeta(BaseModel):
    session_id: str
    source: str
    motor: Literal["browseros_agent", "human"]
    started_at: str
    ended_at: str | None = None
    status: Literal["recording", "processing", "completed", "failed"]
    profile_data_hash: str           # hash of profile data used (for privacy)
    job_id: str | None = None        # if recording was job-specific
    entry_url: str
    events_count: int
    steps_count: int | None = None   # populated after processing
    normalization_confidence: float | None = None
```

## Current equivalents

| Contract | Current code | Location |
|---|---|---|
| `RawRecordingEvent` | (no equivalent) | — |
| `RecordingTimeline` | (no equivalent) | — |
| `CorrelatedStep` | (no equivalent) | — |
| `NormalizationResult` | (no equivalent) | — |
| `UnresolvedValue` | (no equivalent) | — |
| `RecordingSessionMeta` | (no equivalent) | — |

Everything here is new — no recording pipeline exists today.
