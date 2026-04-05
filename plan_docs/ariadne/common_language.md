# Ariadne Common Language

Date: 2026-04-05
Status: design-only

## Purpose

Define the backend-neutral vocabulary for describing browser automation paths.
Every Ariadne path is written in this language. Motors never see each other's
native format — they only see common language (via translators on the way out,
via the recording pipeline on the way in).

## Core models

### AriadnePath

The top-level artifact. One complete path through a portal flow.

```python
class AriadnePath(BaseModel):
    meta: AriadnePathMeta
    entry_point: AriadneEntryPoint
    path_id: str                              # e.g. "linkedin.easy_apply.standard"
    steps: list[AriadneStep]
    bifurcations: dict[str, dict[str, str]]   # tag → condition → destination tag
    dead_ends: list[AriadneDeadEnd]
```

**Current equivalent**: `BrowserOSPlaybook` in `src/apply/browseros_models.py`

### AriadnePathMeta

Metadata about the path: where it came from, when, status.

```python
class AriadnePathMeta(BaseModel):
    source: str              # portal name (linkedin, xing, stepstone, etc.)
    flow: str                # flow name (easy_apply, standard_apply, etc.)
    version: str             # path version (v1, v2, etc.)
    recorded_at: str         # ISO timestamp of recording
    recorded_by: str         # "human" | "browseros_agent" | "manual_authoring"
    status: str              # "draft" | "verified" | "canonical"
    total_steps: int
    notes: str | None = None
```

**Current equivalent**: `PlaybookMeta`

### AriadneEntryPoint

How to reach the start of this path.

```python
class AriadneEntryPoint(BaseModel):
    description: str | None = None
    url_pattern: str | None = None       # regex or glob for matching URLs
    trigger_target: AriadneTarget | None = None  # element that starts the flow
    ariadne_tag: str | None = None       # path naming tag for this entry
```

**Current equivalent**: `PlaybookEntryPoint` (but with `trigger_element_text` string
instead of a full `AriadneTarget`)

### AriadneStep

One replayable step in a path.

```python
class AriadneStep(BaseModel):
    step: int
    name: str
    description: str
    ariadne_tag: str | None = None
    observe: AriadneObserve
    actions: list[AriadneAction] = []
    next_target: AriadneTarget | None = None  # "next" button or navigation trigger
    human_required: bool | Literal["conditional"] = False
    human_trigger: str | None = None          # condition for conditional human_required
    human_message: str | None = None          # what to tell the human
    dry_run_stop: bool = False
    notes: str | None = None
```

**Current equivalent**: `PlaybookStep`

Key differences from current model:
- `next_button_text` (string) → `next_target` (AriadneTarget) — multi-strategy resolution
- `screenshot` field removed — screenshots are storage/evidence concerns, not step definition
- `observe` uses AriadneObserve instead of BrowserOS-specific ObserveBlock

### AriadneObserve

What must be true about the page before a step can execute.

```python
class AriadneObserve(BaseModel):
    expected_elements: list[AriadneExpectedElement] = []
```

**Current equivalent**: `ObserveBlock` (but with `tool: "take_snapshot"` hard-coded —
that field disappears because observation is an intent, not a tool call)

### AriadneExpectedElement

One element that must be observable before a step can proceed.

```python
class AriadneExpectedElement(BaseModel):
    target: AriadneTarget          # how to find this element
    required: bool = True          # optional elements just log warnings
```

**Current equivalent**: `ExpectedElement` (with `text` + `type` fields instead of
a full AriadneTarget)

### AriadneAction

One action to perform within a step.

```python
class AriadneAction(BaseModel):
    intent: AriadneIntent
    target: AriadneTarget
    value: str | None = None       # template with {{placeholders}}
    fallback: AriadneAction | None = None
    note: str | None = None
```

**Current equivalent**: `PlaybookAction` (with `tool: ActionTool` + `selector_text`
instead of `intent` + `AriadneTarget`)

### AriadneTarget

Multi-strategy element descriptor. Each motor uses the field it understands.

```python
class AriadneTarget(BaseModel):
    css: str | None = None              # Crawl4AI, BrowserOS (via Playwright)
    text: str | None = None             # BrowserOS (fuzzy snapshot match)
    image_template: str | None = None   # Vision motor (OpenCV template)
    ocr_text: str | None = None         # Vision motor (OCR fallback)
    region: dict | None = None          # Vision motor (bounding box hint)
```

**Current equivalent**: no equivalent — current model uses a single `selector_text`
string (BrowserOS text matching only)

**Precedence order** when multiple fields are populated (within a single translator):
1. CSS — most deterministic
2. Text — fuzzy match fallback
3. OCR text — vision fallback
4. Image template — visual matching

Each motor's translator documents which fields it supports and in what order.

### AriadneDeadEnd

A documented failure path discovered during recording.

```python
class AriadneDeadEnd(BaseModel):
    tag: str                    # ariadne_tag where the dead end was observed
    reason: str                 # "external_ats" | "job_expired" | "captcha" | etc.
    description: str | None = None
    observed_at: str | None = None  # ISO timestamp
```

**Current equivalent**: `dead_ends_observed` list of dicts on `BrowserOSPlaybook`

## Intent vocabulary

Actions use intents, not backend tool names. The translator is responsible for
knowing how to execute each intent on its backend.

| Intent | Meaning | Replaces |
|---|---|---|
| `click` | Click an element | BrowserOS `click` |
| `fill` | Set a text input value | BrowserOS `fill` |
| `fill_react_controlled` | Set value on a React controlled input | BrowserOS `evaluate_script_react` |
| `select` | Choose a dropdown option | BrowserOS `select_option` |
| `upload` | Upload a file | BrowserOS `upload_file` |
| `press_key` | Press a keyboard key | (not in current model) |
| `scroll` | Scroll the page | (not in current model) |
| `wait` | Wait for a condition | (not in current model) |

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

This vocabulary will grow as motors are implemented, but each addition must be
an intent ("what to do"), never a backend mechanism ("how to do it").

## Template syntax

Values and target fields can contain `{{placeholder}}` templates resolved from
a context dictionary at execution time.

```python
# Context structure
{
    "profile": {
        "first_name": "Juan Pablo",
        "last_name": "Ruiz",
        "phone": "+49123456789",
        "phone_country_code": "DE",
        "email": "jp@example.com",
    },
    "job": {
        "job_title": "Data Scientist",
        "company_name": "Acme Corp",
        "application_url": "https://...",
    },
    "cv_path": "/path/to/cv.pdf",
    "cv_filename": "cv.pdf",
}
```

Resolution uses dot notation: `{{profile.first_name}}` → `"Juan Pablo"`.
Unresolved placeholders in target fields are errors. Unresolved placeholders
in values are skipped with a warning (the field may be optional).

**Current equivalent**: same `{{key}}` syntax in `BrowserOSPlaybook`, resolved by
`BrowserOSPlaybookExecutor.render_template()`.

## What this model does NOT cover

- **How motors execute steps** — that's the translator's job (see `translators.md`)
- **How recordings produce steps** — that's the recording pipeline (see `recording_pipeline.md`)
- **Where paths are stored on disk** — that's storage (see `storage.md`)
- **How paths mature** — that's promotion (see `promotion.md`)
- **What errors look like** — that's the error taxonomy (see `error_taxonomy.md`)

## Open design questions

1. Should `AriadneObserve` support negative assertions ("this element must NOT
   be present")? Useful for detecting dead ends during replay.
2. Should `AriadneStep` carry a `timeout` field for how long to wait for
   observation to pass before failing?
3. Should `AriadneAction` support a `condition` field ("only execute this action
   if X is present")? The current playbook has `human_required: "conditional"`
   but no general conditional execution model.
4. Should `bifurcations` be a first-class model (`AriadneBifurcation`) or stay
   as a dict? The current playbook uses `dict[str, dict[str, str]]`.
5. Should `AriadnePath` carry a `required_motors` field declaring which motors
   can replay it? (e.g., a path with only `css` targets can't be replayed by
   vision-only, and a path with only `image_template` targets can't be replayed
   by BrowserOS CLI)
