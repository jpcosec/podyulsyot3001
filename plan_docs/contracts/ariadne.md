# Ariadne Contracts

Date: 2026-04-05
Status: design-only

## Purpose

These are the core contracts that define Ariadne's common language. Every other
contract document references these types. Full model descriptions are in
`plan_docs/ariadne/common_language.md` — this document focuses on the typed
interfaces and validation rules.

## Models

### AriadnePath

Top-level path artifact.

```python
class AriadnePath(BaseModel):
    meta: AriadnePathMeta
    entry_point: AriadneEntryPoint
    path_id: str
    steps: list[AriadneStep]
    bifurcations: dict[str, dict[str, str]] = {}
    dead_ends: list[AriadneDeadEnd] = []
```

**Validation rules:**
- `steps` must be non-empty
- `steps[i].step` must equal `i + 1` (sequential, 1-indexed)
- `path_id` must match pattern `<source>.<flow>.<variant>`
- `meta.total_steps` must equal `len(steps)`

### AriadnePathMeta

```python
class AriadnePathMeta(BaseModel):
    source: str
    flow: str
    version: str
    recorded_at: str
    recorded_by: Literal["human", "browseros_agent", "manual_authoring"]
    status: Literal["draft", "verified", "canonical"]
    total_steps: int
    notes: str | None = None
```

### AriadneEntryPoint

```python
class AriadneEntryPoint(BaseModel):
    description: str | None = None
    url_pattern: str | None = None
    trigger_target: AriadneTarget | None = None
    ariadne_tag: str | None = None
```

### AriadneStep

```python
class AriadneStep(BaseModel):
    step: int
    name: str
    description: str
    ariadne_tag: str | None = None
    observe: AriadneObserve
    actions: list[AriadneAction] = []
    next_target: AriadneTarget | None = None
    human_required: bool | Literal["conditional"] = False
    human_trigger: str | None = None
    human_message: str | None = None
    dry_run_stop: bool = False
    notes: str | None = None
```

**Validation rules:**
- If `human_required == "conditional"`, `human_trigger` must be non-None
- If `human_required == True` and `human_message` is None, a default message
  is generated from `description`

### AriadneObserve

```python
class AriadneObserve(BaseModel):
    expected_elements: list[AriadneExpectedElement] = []
```

### AriadneExpectedElement

```python
class AriadneExpectedElement(BaseModel):
    target: AriadneTarget
    required: bool = True
```

### AriadneAction

```python
class AriadneAction(BaseModel):
    intent: AriadneIntent
    target: AriadneTarget
    value: str | None = None
    fallback: AriadneAction | None = None
    note: str | None = None
```

**Validation rules:**
- `fill`, `fill_react_controlled`, `select` require `value` to be non-None
- `click`, `upload`, `press_key` ignore `value` (or use it motor-specifically)
- Recursive `fallback` depth should not exceed 2 (prevent infinite chains)

### AriadneTarget

```python
class AriadneTarget(BaseModel):
    css: str | None = None
    text: str | None = None
    image_template: str | None = None
    ocr_text: str | None = None
    region: dict | None = None
```

**Validation rules:**
- At least one field must be non-None (a target with all None fields is useless)
- `region` schema: `{"x": int, "y": int, "width": int, "height": int}`

### AriadneIntent

```python
AriadneIntent = Literal[
    "click",
    "fill",
    "fill_react_controlled",
    "select",
    "upload",
    "press_key",
    "scroll",
    "wait",
]
```

### AriadneDeadEnd

```python
class AriadneDeadEnd(BaseModel):
    tag: str
    reason: str
    description: str | None = None
    observed_at: str | None = None
```

## Current equivalents

| Ariadne contract | Current model | Location |
|---|---|---|
| `AriadnePath` | `BrowserOSPlaybook` | `src/apply/browseros_models.py` |
| `AriadnePathMeta` | `PlaybookMeta` | same |
| `AriadneEntryPoint` | `PlaybookEntryPoint` | same |
| `AriadneStep` | `PlaybookStep` | same |
| `AriadneObserve` | `ObserveBlock` | same |
| `AriadneExpectedElement` | `ExpectedElement` | same |
| `AriadneAction` | `PlaybookAction` | same |
| `AriadneTarget` | (none — `selector_text: str`) | same |
| `AriadneIntent` | `ActionTool` Literal | same |
| `AriadneDeadEnd` | `dead_ends_observed: list[dict]` | same |
