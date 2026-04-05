# BrowserOS CLI Motor Contracts

Date: 2026-04-05
Status: design-only

## Purpose

Contracts between the Ariadne BrowserOS CLI translator and the BrowserOS CLI
executor. These define the translator's output — the motor-specific plan that
the executor consumes to replay paths via MCP tool calls.

## Translator output

### BrowserOSCliPlan

The full execution plan for one AriadnePath, compiled for BrowserOS CLI.

```python
class BrowserOSCliPlan(BaseModel):
    path_id: str
    steps: list[BrowserOSCliStep]
    session_config: BrowserOSCliSessionConfig
```

### BrowserOSCliStep

One step in the replay. Maps 1:1 to an AriadneStep.

```python
class BrowserOSCliStep(BaseModel):
    step: int
    name: str
    observe: BrowserOSCliObserve
    actions: list[BrowserOSCliAction]
    next_action: BrowserOSCliAction | None = None   # "next" button click
    human_required: bool | Literal["conditional"] = False
    human_message: str | None = None
    dry_run_stop: bool = False
```

### BrowserOSCliObserve

Observation check before a step executes.

```python
class BrowserOSCliObserve(BaseModel):
    expected_elements: list[BrowserOSCliExpectedElement]
```

The executor calls `take_snapshot()`, parses the elements, and asserts each
expected element is present via text matching.

### BrowserOSCliExpectedElement

```python
class BrowserOSCliExpectedElement(BaseModel):
    text: str                       # fuzzy text match against snapshot
    element_type: str | None = None # optional type filter (textbox, button, etc.)
    required: bool = True
```

### BrowserOSCliAction

One MCP tool call.

```python
class BrowserOSCliAction(BaseModel):
    tool: BrowserOSCliTool
    selector_text: str              # resolved text for element lookup in snapshot
    value: str | None = None        # resolved value (templates already substituted)
    fallback: BrowserOSCliAction | None = None
```

### BrowserOSCliTool

```python
BrowserOSCliTool = Literal[
    "click",
    "fill",
    "fill_react",         # evaluate_script with React native setter
    "select_option",
    "upload_file",
    "press_key",
    "scroll",
]
```

Note: `fill_react` is a motor-level tool (composes `evaluate_script` with the
React native value setter pattern). It maps from `AriadneIntent.fill_react_controlled`.

### BrowserOSCliSessionConfig

```python
class BrowserOSCliSessionConfig(BaseModel):
    base_url: str = "http://127.0.0.1:9200/mcp"
    use_hidden_page: bool = True
    screenshot_on_complete: bool = True
    screenshot_on_error: bool = True
```

## Current equivalents

| Contract | Current code | Location |
|---|---|---|
| `BrowserOSCliPlan` | `BrowserOSPlaybook` | `src/apply/browseros_models.py` |
| `BrowserOSCliStep` | `PlaybookStep` | same |
| `BrowserOSCliObserve` | `ObserveBlock` | same |
| `BrowserOSCliExpectedElement` | `ExpectedElement` | same |
| `BrowserOSCliAction` | `PlaybookAction` | same |
| `BrowserOSCliTool` | `ActionTool` | same |
| `BrowserOSCliSessionConfig` | (inline in `BrowserOSClient.__init__`) | `src/apply/browseros_client.py` |

The current `BrowserOSPlaybook` serves double duty as both the Ariadne common
language (it IS the playbook) and the motor execution plan (it's what the
executor consumes). After refactoring, these are separate: Ariadne stores
`AriadnePath`, the translator compiles it to `BrowserOSCliPlan`, and the
executor consumes `BrowserOSCliPlan`.
