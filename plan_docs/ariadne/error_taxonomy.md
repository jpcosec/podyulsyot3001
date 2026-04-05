# Ariadne Error Taxonomy

Date: 2026-04-05
Status: design-only

## Purpose

Define backend-neutral error classes that all motors and translators raise into.
Higher layers (operator CLI, TUI, orchestrator) only catch Ariadne errors —
they never import motor-specific error classes.

## Error hierarchy

```
AriadneError (base)
├── TranslationError        — path could not be compiled to motor format
├── ObservationFailed       — expected elements not present at a step
├── TargetNotFound          — specific element could not be resolved
├── PortalStructureChanged  — mandatory structural drift detected
├── ReplayAborted           — operator or dry-run guard stopped execution
└── RecordingError          — recording pipeline failure
```

### TranslationError

Raised by translators when a common-language step cannot be compiled to the
motor's native format.

**Typical causes:**
- Required `AriadneTarget` field is missing for this motor
  (e.g., Crawl4AI needs `css` but only `text` is populated)
- Unsupported intent for this motor
  (e.g., `upload` has no C4A-Script equivalent — but this should be handled
  by the translator via hooks, so it's a translator bug if raised)
- Unresolvable `{{placeholder}}` in target or value

**Who raises:** translator code, before execution begins
**Who catches:** orchestrator, to report which motor can't handle the path

**Current equivalents:** none (translation doesn't exist yet)

### ObservationFailed

Raised during replay when a step's observe block fails — expected elements
are not present on the page.

**Typical causes:**
- Page hasn't finished loading (timing issue)
- Portal layout changed (observe block expectations are stale)
- Wrong page entirely (navigation went somewhere unexpected)

**Who raises:** motor execution code, during observe phase of a step
**Who catches:** orchestrator, to decide whether to retry, skip, or abort

**Current equivalents:**
- `BrowserOSObserveError` in `src/apply/browseros_executor.py`
  (raised by `_assert_expected_elements()`)

### TargetNotFound

Raised during replay when a specific action target cannot be resolved on
the current page.

**Typical causes:**
- Element text changed (portal copy updated)
- CSS selector no longer matches (portal DOM restructured)
- Image template no longer matches (portal visual redesign)
- Element is present but hidden or disabled

**Who raises:** motor execution code, during action execution
**Who catches:** orchestrator, to try fallback action or abort

**Current equivalents:**
- `BrowserOSObserveError` in `src/apply/browseros_executor.py`
  (raised by `_resolve_element_id()` — currently overloaded with ObservationFailed)

### PortalStructureChanged

Raised when multiple observation or target failures indicate the portal has
structurally changed, not just a transient issue.

**Typical causes:**
- Multiple mandatory selectors absent from DOM
- Portal redirects to a different flow than expected
- Form structure fundamentally different from recorded path

**Who raises:** motor execution code or orchestrator (after multiple TargetNotFound/ObservationFailed)
**Who catches:** top-level handler, to flag the path for re-recording

**Current equivalents:**
- `PortalStructureChangedError` in `src/apply/smart_adapter.py`
  (raised by `_check_selector_results()` when mandatory selectors are absent)

### ReplayAborted

Raised when execution is intentionally stopped.

**Typical causes:**
- `dry_run_stop` reached on a step
- Operator declined a `human_required` confirmation
- Timeout exceeded
- Operator manually cancelled

**Who raises:** motor execution code or HITL callback
**Who catches:** top-level handler, to report clean termination (not an error per se)

**Current equivalents:**
- `RuntimeError("Application aborted by operator")` in `src/apply/browseros_executor.py`
  (raised by `_request_human_confirmation()`)
- Implicit in `ApplyAdapter.run()` dry-run branch (returns early, doesn't raise)

### RecordingError

Raised when the recording pipeline fails during capture, correlation, or
normalization.

**Typical causes:**
- CDP WebSocket connection lost during recording
- MCP proxy failed to intercept events
- Capture script injection failed on navigation
- Normalization produced an invalid AriadnePath

**Who raises:** recording pipeline code
**Who catches:** session manager, to report partial recording or abort

**Current equivalents:** none (recording pipeline doesn't exist yet)

## Error data

All Ariadne errors carry structured context:

```python
class AriadneError(Exception):
    def __init__(
        self,
        message: str,
        *,
        step: AriadneStep | None = None,
        target: AriadneTarget | None = None,
        motor: str | None = None,
        path_id: str | None = None,
    ):
        super().__init__(message)
        self.step = step
        self.target = target
        self.motor = motor
        self.path_id = path_id
```

This enables higher layers to report exactly which step, target, motor, and
path caused the error without parsing the message string.

## Motor error wrapping

Motors internally use whatever error handling their backend provides. At the
motor boundary, all errors must be caught and re-raised as Ariadne errors.

```python
# Inside a motor's execution code
try:
    self.client.click(page_id, element_id)
except BrowserOSError as exc:
    raise TargetNotFound(
        f"BrowserOS click failed: {exc}",
        step=current_step,
        target=current_action.target,
        motor="browseros_cli",
    ) from exc
```

Motor-specific errors (`BrowserOSError`, `BrowserOSObserveError`,
`PortalStructureChangedError`) become internal implementation details —
never exposed above the motor layer.

## Migration from current errors

| Current error | Location | Ariadne replacement |
|---|---|---|
| `BrowserOSError` | `browseros_client.py` | Internal to BrowserOS CLI motor |
| `BrowserOSObserveError` | `browseros_executor.py` | `ObservationFailed` or `TargetNotFound` |
| `PortalStructureChangedError` | `smart_adapter.py` | `PortalStructureChanged` |
| `RuntimeError("aborted by operator")` | `browseros_executor.py` | `ReplayAborted` |
| `RuntimeError("Failed to navigate")` | `smart_adapter.py` | `ObservationFailed` |
| `ValueError("No application_url")` | `browseros_backend.py` | Stays as ValueError (input validation, not Ariadne error) |

## Open questions

1. Should `TargetNotFound` and `ObservationFailed` be the same error class?
   They're currently conflated in `BrowserOSObserveError`. Splitting them
   enables different handling (retry target resolution vs. wait for page load)
   but adds complexity.
2. Should `PortalStructureChanged` be raised automatically after N consecutive
   `TargetNotFound` errors, or only when explicit structural checks fail?
3. Should `ReplayAborted` be an error at all, or a normal return value?
   Dry-run completion is not a failure. Could use a `ReplayResult` with a
   status field instead.
4. Should errors carry screenshots? A screenshot at the moment of failure
   is extremely useful for debugging but makes the error object heavy.
