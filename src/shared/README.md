# 🔧 Shared

Cross-cutting utilities shared across all pipeline modules. Currently contains the `LogTag` enum for structured, consistent log output.

---

## 🏗️ Architecture & Features

A single-responsibility package — no business logic, no I/O, no external dependencies.

- Observability log tags (`LogTag` enum): `src/shared/log_tags.py`

`LogTag` is a `StrEnum` so each member formats directly into f-strings without calling `.value`. Tags are bracketed (`[⚡]`) to be grep-friendly.

---

## ⚙️ Configuration

No environment variables. No dependencies beyond the Python standard library.

---

## 🚀 CLI / UI / Usage

Not a runnable module. Import `LogTag` wherever structured log output is needed:

```python
from src.shared.log_tags import LogTag
```

---

## 📝 Data Contract

`LogTag` in `src/shared/log_tags.py` — all tags and their semantic contracts are documented in the enum's docstring.

---

## 🛠️ How to Add / Extend

1. **New tag**: add a member to `LogTag` in `src/shared/log_tags.py` with a docstring explaining its semantic meaning and constraints.
2. **New shared utility**: add a new module to `src/shared/` and export it from `src/shared/__init__.py`.

Keep `src/shared/` free of imports from other `src/` modules to avoid circular dependencies.

---

## 💻 How to Use

```python
import logging
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)

logger.info(f"{LogTag.LLM} Generating match proposal for {job_id}")
logger.warning(f"{LogTag.WARN} Rate limit hit, retrying in {delay}s")
logger.error(f"{LogTag.FAIL} Schema validation failed: {err}")
```

Full tag vocabulary: see `src/shared/log_tags.py` and `docs/standards/docs/documentation_and_planning_guide.md` §3.

---

## 🚑 Troubleshooting

- **Tag used on wrong path** (e.g. `LogTag.LLM` on a deterministic function) — the enum only prevents typos; semantic correctness is a code review concern. Check the tag docstring for constraints.
