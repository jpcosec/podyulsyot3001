---
type: pattern
domain: architecture
source: src/automation/motors/registry.py:1
---

# Pill: Registry Pattern (DIP-Compliant)

## Pattern
Avoid direct imports of concrete implementations (e.g. `BrowserOSExecutor`). Use the `MotorRegistry` and `ModeRegistry` to resolve instances at runtime.

## Implementation (Motor)
```python
from src.automation.motors.registry import MotorRegistry

# Get executor instance by name
executor = MotorRegistry.get_executor("crawl4ai")
async with executor as active:
    await active.take_snapshot()
```

## Implementation (Portal Mode)
```python
from src.automation.ariadne.modes.registry import ModeRegistry

# Get portal-specific heuristics
mode = ModeRegistry.get_mode("linkedin")
await mode.apply_heuristics(state, executor)
```

## When to use
Use in CLI entrypoints (`main.py`) or in orchestration logic. **Never** import from `src/automation/motors/` inside the `ariadne/` domain.

## Verify
Verify that tests pass with `test_domain_isolation.py`.
