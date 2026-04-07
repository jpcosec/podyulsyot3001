# BrowserOS Domain Interface Boundary

## Explanation

The BrowserOS backend still imports Ariadne domain models directly. That keeps the motor coupled to domain internals instead of depending only on the motor protocol boundary.

## Reference in src

- `src/automation/motors/browseros/cli/backend.py`
- `src/automation/motors/browseros/cli/replayer.py`
- `src/automation/ariadne/models.py`

## What to fix

Reduce BrowserOS dependencies on the full Ariadne model surface so the motor only consumes the minimal replay contract it needs.

## How to do it

Introduce a narrow step/action interface or DTO layer at the Ariadne boundary, move BrowserOS-specific replay assumptions behind that interface, and keep model-to-motor adaptation in one place.

## Does it depend on another issue?

No.
