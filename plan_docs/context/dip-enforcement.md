---
type: guardrail
domain: architecture
source: tests/architecture/test_domain_isolation.py:1
---

# Pill: DIP Enforcement

## Rule
`ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config["configurable"]["executor"]` or resolved through `MotorRegistry`.

## ❌ Forbidden
```python
# inside any file under src/automation/ariadne/
from src.automation.motors.browseros.executor import BrowserOSExecutor
```

## ✅ Correct
```python
# Option A — accept executor from LangGraph config (orchestrator.py:91)
executor = config.get("configurable", {}).get("executor")

# Option B — resolve via registry (infrastructure layer only)
from src.automation.motors.registry import MotorRegistry
executor = MotorRegistry.get_executor("browseros")
```

Option B is only valid in infrastructure-layer files (`main.py`, wiring code). Inside `ariadne/` nodes, always use Option A.

## Verify
```bash
# NOTE: test_domain_isolation.py is disabled pending test suite realignment. Use manual check:
grep -rn "from src\.automation\.motors" src/automation/ariadne/
```
