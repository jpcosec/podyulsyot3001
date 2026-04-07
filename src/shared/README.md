# 🔧 Shared

Cross-cutting utilities shared across all pipeline modules. Contains the `LogTag` enum for structured log output and the `configure_logging` function used by all entry points.

---

## 🏗️ Architecture & Features

A single-responsibility package — no business logic, no I/O, no external dependencies beyond the Python standard library.

- Observability log tags (`LogTag` enum): `src/shared/log_tags.py`
- Logging configuration (`configure_logging`): `src/shared/logging_config.py`

`LogTag` is a `StrEnum` so each member formats directly into f-strings without calling `.value`. Tags are bracketed (`[⚡]`) to be grep-friendly.

`configure_logging` loads `config/logging.json` via `logging.config.dictConfig`. All loggers — including third-party ones (LangChain, LangGraph, httpx) — flow into the configured root logger. Third-party loggers are capped at `WARNING` in the config file.

---

## ⚙️ Configuration

`LOG_DIR` (`.env`) — directory where run-specific log files are written. Defaults to `logs/` relative to the project root.

No other environment variables. No dependencies beyond the Python standard library.

---

## 🚀 CLI / UI / Usage

Not a runnable module. Call `configure_logging` once at entry-point startup, before any library imports run:

```python
from src.shared.logging_config import configure_logging

configure_logging()                                    # console only
configure_logging(log_file="translator_xing_run.log")    # console + file under LOG_DIR
```

Import `LogTag` wherever structured log output is needed:

```python
from src.shared.log_tags import LogTag
```

---

## 📝 Data Contract

- `LogTag` in `src/shared/log_tags.py` — all tags and their semantic contracts are documented in the enum's docstring.
- Log format and third-party logger levels: `config/logging.json`.

---

## 🛠️ How to Add / Extend

1. **New tag**: add a member to `LogTag` in `src/shared/log_tags.py` with a docstring explaining its semantic meaning and constraints.
2. **Tune third-party log levels**: edit `config/logging.json` — add or adjust logger entries under `"loggers"`.
3. **New shared utility**: add a new module to `src/shared/` and export it from `src/shared/__init__.py`.

Keep `src/shared/` free of imports from other `src/` modules to avoid circular dependencies.

---

## 💻 How to Use

```python
import logging
from src.shared.log_tags import LogTag
from src.shared.logging_config import configure_logging

configure_logging()  # call once at entry point

logger = logging.getLogger(__name__)

logger.info(f"{LogTag.LLM} Generating match proposal for {job_id}")
logger.warning(f"{LogTag.WARN} Rate limit hit, retrying in {delay}s")
logger.error(f"{LogTag.FAIL} Schema validation failed: {err}")
```

Full tag vocabulary: see `src/shared/log_tags.py` and `docs/standards/docs/documentation_and_planning_guide.md` §3.

---

## 🚑 Troubleshooting

- **Tag used on wrong path** (e.g. `LogTag.LLM` on a deterministic function) — the enum only prevents typos; semantic correctness is a code review concern. Check the tag docstring for constraints.
- **Too much noise from LangChain/LangGraph** — lower their level in `config/logging.json` (e.g. change `"WARNING"` to `"ERROR"`).
- **Log file not created** — check that `LOG_DIR` in `.env` points to a writable directory. The directory is created automatically if it doesn't exist.
