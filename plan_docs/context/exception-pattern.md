---
type: pattern
domain: ariadne
source: src/automation/ariadne/exceptions.py
---

# Pill: Exception Implementation Pattern

## Pattern
Define all custom domain exceptions in `src/automation/ariadne/exceptions.py` (or a local `exceptions.py` for modes). Use a common base class.

## Implementation
```python
class AriadneError(Exception):
    """Base class for all Ariadne domain errors."""
    pass

class MapNotFoundError(AriadneError):
    """Raised when the requested portal map does not exist on disk."""
    def __init__(self, portal_name: str):
        super().__init__(f"MapNotFoundError: No map found for portal '{portal_name}'")
```

## When to use
Use in Phase 1 `zero-shot-error-typing.md` and any new node that needs specific error handling.

## Verify
Verify that the exception is catchable by its specific type, not just `except Exception`.
