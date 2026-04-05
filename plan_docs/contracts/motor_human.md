# Human Motor Contracts

Date: 2026-04-05
Status: design-only

## Purpose

Contracts for the Human motor. Like the BrowserOS Agent motor, the Human motor
produces Ariadne paths via the recording pipeline. These contracts define the
session interface and what the recording pipeline receives from CDP capture.

## Session contracts

### HumanSessionConfig

Configuration to start a human recording session.

```python
class HumanSessionConfig(BaseModel):
    source: str                      # portal name
    entry_url: str                   # where to open BrowserOS
    profile_data: dict               # candidate profile for {{placeholder}} detection
    job_data: dict | None = None     # job context for {{placeholder}} detection
    recording_enabled: bool = True   # always True for human sessions (that's the point)
```

### HumanSessionResult

Outcome of a human session.

```python
class HumanSessionResult(BaseModel):
    session_id: str
    status: Literal["completed", "aborted"]
    duration_seconds: float
    annotations_count: int
    recording_path: Path | None      # path to draft AriadnePath
```

## Recording pipeline input

These contracts define what the recording pipeline receives from CDP event
capture during a human session.

### CdpCaptureEvent

One event from the in-page capture script, received via CDP `Runtime.consoleAPICalled`.

```python
class CdpCaptureEvent(BaseModel):
    timestamp: str                   # from `ts` field in injected JSON
    event_type: Literal["click", "change", "submit"]
    data: CdpClickData | CdpChangeData | CdpSubmitData
```

### CdpClickData

```python
class CdpClickData(BaseModel):
    tag: str                         # HTML tag (BUTTON, A, INPUT, etc.)
    text: str                        # element innerText (truncated to 100 chars)
    x: int                           # clientX coordinate
    y: int                           # clientY coordinate
    name: str | None = None          # element name or id attribute
```

### CdpChangeData

```python
class CdpChangeData(BaseModel):
    tag: str                         # HTML tag (INPUT, SELECT, TEXTAREA)
    name: str | None = None          # element name attribute
    value: str                       # new value (redacted for password fields)
    input_type: str | None = None    # input type attribute
```

### CdpSubmitData

```python
class CdpSubmitData(BaseModel):
    action: str                      # form action URL
    method: str                      # form method (GET, POST)
```

### CdpNavigationEvent

Page navigation detected via CDP `Page.frameNavigated`.

```python
class CdpNavigationEvent(BaseModel):
    timestamp: str
    url: str
    frame_id: str
```

### HumanAnnotation

An explicit annotation from the human during recording.

```python
class HumanAnnotation(BaseModel):
    timestamp: str
    annotation_type: Literal[
        "step_boundary",             # "this is a new step"
        "human_required",            # "this step always needs a human"
        "bifurcation",               # "sometimes this goes a different way"
        "dead_end",                   # "this path is a dead end"
        "note",                       # free text note
    ]
    text: str | None = None          # annotation content
    ariadne_tag: str | None = None   # optional tag for the step
```

## Current equivalents

| Contract | Current code | Location |
|---|---|---|
| `HumanSessionConfig` | (no equivalent) | — |
| `HumanSessionResult` | (no equivalent) | — |
| `CdpCaptureEvent` | (documented in browseros_interfaces.md, not implemented) | — |
| `CdpClickData` | (documented as capture script JSON fields) | — |
| `CdpChangeData` | (documented as capture script JSON fields) | — |
| `CdpSubmitData` | (documented as capture script JSON fields) | — |
| `CdpNavigationEvent` | (documented as CDP Page.frameNavigated) | — |
| `HumanAnnotation` | (no equivalent) | — |

Everything here is new — the human motor has no code today. The CDP event
shapes come from the capture script documented in
`docs/reference/external_libs/browseros_interfaces.md`.
