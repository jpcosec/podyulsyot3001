# OS Native Tools Motor Contracts

Date: 2026-04-05
Status: design-only

## Purpose

Contracts for the OS Native Tools motor. This motor receives resolved coordinates
(typically from the vision motor) and executes physical input events at the OS level.

## Execution contracts

### NativePlan

The execution plan for a sequence of OS-level actions.

```python
class NativePlan(BaseModel):
    actions: list[NativeAction]
    humanization: HumanizationConfig | None = None
```

### NativeAction

One physical input event.

```python
class NativeAction(BaseModel):
    action_type: NativeActionType
    x: int | None = None             # screen coordinates (for click, move, drag)
    y: int | None = None
    to_x: int | None = None          # drag destination
    to_y: int | None = None
    text: str | None = None          # for type_text
    key: str | None = None           # for press_key, key_combo
    keys: list[str] | None = None    # for key_combo (modifier + key)
    scroll_amount: int | None = None # for scroll
```

### NativeActionType

```python
NativeActionType = Literal[
    "click",
    "double_click",
    "right_click",
    "move_mouse",
    "type_text",
    "press_key",
    "key_combo",
    "drag",
    "scroll",
]
```

### HumanizationConfig

Timing and movement parameters to mimic human input.

```python
class HumanizationConfig(BaseModel):
    keystroke_delay: TimingModel = TimingModel(distribution="gaussian", mean_ms=80, std_ms=20)
    mouse_movement: Literal["linear", "bezier", "jitter"] = "bezier"
    inter_action_delay: TimingModel = TimingModel(distribution="uniform", min_ms=100, max_ms=500)
```

### TimingModel

```python
class TimingModel(BaseModel):
    distribution: Literal["fixed", "uniform", "gaussian"]
    mean_ms: int | None = None       # for fixed and gaussian
    std_ms: int | None = None        # for gaussian
    min_ms: int | None = None        # for uniform
    max_ms: int | None = None        # for uniform
```

## Coordinate source contract

The OS native motor needs coordinates but doesn't resolve them itself. Coordinates
come from external sources.

### ResolvedCoordinates

```python
class ResolvedCoordinates(BaseModel):
    x: int
    y: int
    source: Literal["vision", "browseros_rect", "ariadne_static", "manual"]
    confidence: float | None = None  # from vision motor
```

| Source | How coordinates are obtained |
|---|---|
| `vision` | VisionMatch from vision motor (template or OCR match) |
| `browseros_rect` | BrowserOS element bounding rect via JS `getBoundingClientRect()` |
| `ariadne_static` | Hardcoded in AriadneTarget.region for known-stable layouts |
| `manual` | Operator provides coordinates explicitly |

## Current equivalents

| Contract | Current code | Location |
|---|---|---|
| `NativePlan` | (no equivalent) | — |
| `NativeAction` | (no equivalent) | — |
| `HumanizationConfig` | (no equivalent) | — |
| `ResolvedCoordinates` | (no equivalent) | — |

Everything here is new — the OS native motor has no code today.
