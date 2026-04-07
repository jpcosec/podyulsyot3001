# `src/automation/ariadne/` — Ariadne Domain Layer

## 🏗️ Architecture

This package is the backend-neutral core of the automation system.

- `models.py` defines the shared semantic contract used by portal maps and motors.
- `session.py` owns the apply orchestration loop, resolves portal routing, and delegates browser work to a motor.
- `hitl.py` persists interrupt payloads and terminal resume decisions for active apply sessions.
- `motor_protocol.py` defines the `MotorProvider` and `MotorSession` contracts.
- `navigator.py` decides the next step from observed portal state.
- `recorder.py`, `trace_models.py`, and `normalizer.py` support recording and promotion workflows.
- `exceptions.py` keeps Ariadne-specific errors inside the domain layer.

## ⚙️ Configuration

This layer does not have its own config file.

- Portal maps are loaded from `src/automation/portals/<portal>/maps/easy_apply.json`.
- Storage is injected through `AutomationStorage` from `src/automation/storage.py`.
- Runtime profile data is validated through `src/automation/contracts.py` and loaded through `AutomationStorage` before `session.py` builds the execution context.

## 🚀 CLI / Usage

The main entry point lives in `src/automation/main.py`.

```bash
python -m src.automation.main apply --source xing --job-id 123 --cv cv.pdf --dry-run
python -m src.automation.main promote --trace-id trace_123 --portal xing
```

## 📝 Data Contract

- `AriadnePortalMap` is the canonical map schema.
- `AriadneState`, `AriadnePath`, `AriadneStep`, and `AriadneAction` model replay behavior.
- `ApplyMeta` is the persisted apply result artifact.
- `AriadneSessionTrace` captures draft recordings before normalization.

## 🛠️ How to Add / Extend

1. Add or update portal JSON maps under `src/automation/portals/`.
2. Extend `models.py` only when the semantic contract itself changes.
3. Keep orchestration concerns in `session.py` and `navigator.py`, and keep portal-specific branching in `src/automation/portals/*/routing.py`.
4. Add or update promotion logic in `normalizer.py` when new recording shapes appear.

## 💻 How to Use

```python
from pathlib import Path

from src.automation.ariadne.session import AriadneSession
from src.automation.motors.browseros.cli.backend import BrowserOSMotorProvider

session = AriadneSession("xing")
motor = BrowserOSMotorProvider()
# await session.run(motor, job_id="123", cv_path=Path("cv.pdf"), dry_run=True)
```

## 🚑 Troubleshooting

- If a map cannot be loaded, verify `easy_apply.json` exists for the requested portal.
- If replay stops in an unexpected state, inspect the corresponding map predicates and navigator transitions.
- If promotion output is noisy, inspect the raw trace and normalization heuristics before editing the canonical map.
