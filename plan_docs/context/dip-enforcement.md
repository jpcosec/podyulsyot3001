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
python -m pytest tests/architecture/test_domain_isolation.py -q
```
Uses `pytest-archon` to fail if any file in `ariadne/` imports from `motors/`.
