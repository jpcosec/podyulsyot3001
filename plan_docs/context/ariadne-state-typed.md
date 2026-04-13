---
type: model
domain: ariadne
source: plan_docs/issues/ariadne-oop-skeleton.md
---

# Pill: AriadneState (Typed)

## Structure

`AriadneState` is the LangGraph state object that flows between actors. It is pure data — no live objects, no live connections. `Labyrinth`, `AriadneThread`, `Sensor`, and `Motor` are constructor-injected into actors, never placed in state.

```python
class AriadneState(TypedDict):
    # Intent (set by Interpreter)
    instruction: str                   # raw user input
    current_mission_id: str            # resolved mission
    portal_name: str

    # Perception (set by Theseus)
    snapshot: SnapshotResult | None
    current_room_id: str | None        # from Labyrinth.identify_room
    danger_type: str | None            # "http_error" | "captcha" | None
    screenshot_b64: str | None         # annotated with hints when available

    # Typed session memory (replaces loose dict)
    hints: dict[str, str]              # {"AA": "button 'Apply'", ...}
    hints_available: bool
    dry_run: bool
    agent_failures: int                # circuit breaker counter for Delphi
    extracted_data: list[dict]         # for discovery missions

    # Execution history
    history: list[MotorCommand]        # successful steps (reducer: append)
    errors: list[str]                  # reducer: append
    trace: list[TraceEvent]            # Motor output carried to Recorder (see below)
```

## Recorder Communication

`Motor.act()` returns an `ExecutionResult` that contains a `TraceEvent` fragment. The reducer on `state["trace"]` appends it. The `Recorder` node reads `state["trace"]` and assimilates it into `Labyrinth` + `AriadneThread`. This is the **active** recording path (Theseus + Delphi).

The **passive** path (Chrome DevTools Recorder `.json` export) bypasses state entirely: it's a separate `Recorder.ingest_passive_trace(devtools_json)` call made out-of-band, not during a graph run.

Two sources, one assimilation pipeline. See `recording-pattern.md` and `oop-06-recorder.md`.

## Usage

- Interpreter seeds `instruction`, `current_mission_id`, `portal_name`.
- Theseus writes `snapshot`, `current_room_id`, `hints`, `screenshot_b64`, `danger_type`, appends to `history` and `trace`.
- Delphi reads `instruction` + `current_mission_id` + `hints`, writes to `history` and `trace`, bumps `agent_failures`.
- Recorder reads `trace` and writes to `Labyrinth`/`AriadneThread` (via injected deps, not via state).

## Verify

- No `AriadneState` field holds a live `Labyrinth`, `AriadneThread`, `Sensor`, or `Motor` instance.
- `session_memory: dict` is forbidden — use the typed fields above.
- `trace` is append-only and consumed by `Recorder` only.
