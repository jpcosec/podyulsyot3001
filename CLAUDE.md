# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Postulator 3000 is a modular job application pipeline that produces tailored CV and motivation letter documents from job postings. It combines a translator, LangGraph-native document generation engine (with HITL review via a Textual TUI), and a typed render pipeline.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Commands

```bash
# Run active test suite
python -m pytest tests/unit tests/test_generate_documents_v2 -q

# Run all tests
python -m pytest tests/ -q

# Run a single test file
python -m pytest tests/unit/cli/test_main.py -q

# Run a focused test subtree
python -m pytest tests/unit/core/ai/generate_documents_v2 -q

# Translate job postings
python -m src.cli.main translate --source xing

# Run document generation pipeline
python -m src.cli.main generate --source stepstone --job-id <ID> --language en --render

# Launch HITL review TUI
python -m src.cli.main review --source stepstone --job-id <ID>

# Render CV to PDF
python -m src.cli.main render cv --source stepstone --job-id <ID> --language en

# Run batch pipeline
python -m src.cli.main run-batch --sources xing stepstone --limit 5

# Start API server
python -m src.cli.main api start
```

## Architecture

### Module layout

Each module is a self-contained package under `src/`:

- `src/core/` — shared infrastructure: `DataManager` (data_manager.py), API client, state, profile.
- `src/core/ai/generate_documents_v2/` — LangGraph-native staged document generation: `graph.py`, `contracts/`, `storage.py`, `nodes/`, `subgraphs/`, `pipeline.py`.
- `src/core/tools/render/` — typed, engine-agnostic PDF/DOCX rendering via Pandoc + Jinja2. Entry point is `RenderCoordinator` in `coordinator.py`; `RenderRequest` in `request.py` is the unified request model. Document types and engines registered in `registry.py`.
- `src/core/tools/translator/` — field and document translation pipeline.
- `src/review_ui/` — Textual TUI: `app.py` (`MatchReviewApp`), `bus.py` (`MatchBus` connects UI to LangGraph + disk), `screens/`, `widgets/`.
- `src/shared/` — `LogTag` (log_tags.py), logging bootstrap (logging_config.py).

### Control plane vs. data plane

**Control plane** lives in the operator CLI and API-backed review flow; carries routing signals, job identifiers, and lightweight review metadata.

**Data plane** lives under `data/jobs/<source>/<job_id>/nodes/`, where module artifacts are persisted by `DataManager` and module-local storage helpers.

### Document generation graph flow

`ingestion → requirement_filter → alignment → blueprint → drafting → assembly`

The graph persists stage artifacts per step. Heavy payloads stay on disk; graph state stays thin.

### Render pipeline

`RenderRequest` → `RenderCoordinator` → resolves document adapter + style manifest + language bundle → `LatexRenderer` (Pandoc) → output file.

### HITL review loop

1. Operator launches runs through `src/cli/main.py`.
2. Review surfaces are loaded in `src/review_ui/` from canonical artifacts and API metadata.
3. Reviewer acts through the TUI and the control plane resumes or updates the relevant workflow.

### Shared data contracts

- `JobKG` / `JobDelta` — staged job-understanding contracts for document generation.
- `RenderRequest` — unified input model for the render coordinator.
- LangGraph entrypoint: `langgraph.json` → `src.core.ai.generate_documents_v2.graph:create_studio_graph`.

## Layer Separation (per module)

| File | Owns |
|---|---|
| `contracts.py` | All Pydantic input/output models — the schema boundary |
| `storage.py` | All file I/O and artifact paths — no business logic |
| `main.py` | CLI entry point only — delegates to graph/coordinator |

**No file does two things.** If a function in `graph.py` is also writing to disk, that write belongs in `storage.py`. Cross-module dependencies go through `contracts.py`, never by importing internal files.

## Code Conventions

### Imports

- Use `from __future__ import annotations` at the top of all modules.
- Group: (1) standard library, (2) third-party, (3) local `src.*`.
- Prefer absolute imports from `src...` over relative imports.

### Naming

- Modules/functions: `snake_case` | Classes/Pydantic models: `PascalCase` | Constants: `UPPER_SNAKE_CASE`
- Internal helpers: prefix with `_` | CLI parsers: `_build_parser()` | LangGraph nodes: `load_*`, `build_*`, `persist_*`, `apply_*`, `prepare_*`

### Types and data modeling

- Use `list[str]`, `dict[str, Any]`, `tuple[str, str]` for built-in generics.
- Use `TypedDict` for graph state. Use Pydantic models for external contracts, LLM outputs, review payloads.
- Add `Field(description=...)` on Pydantic fields consumed by LLMs — descriptions are read by LLMs, so keep them accurate and specific.

### Error handling

- Fail closed: never silently convert failure to success.
- Use domain-specific exceptions (`ToolDependencyError`, `ToolFailureError`) over bare `Exception`.
- Log with `LogTag.WARN` before re-raising; always use `raise ... from exc` to preserve stack traces.

### Logging

```python
from src.shared.log_tags import LogTag

logger.info(f"{LogTag.LLM} Generating match proposal for {job_id}")   # LLM paths only
logger.info(f"{LogTag.FAST} Computing alignment score")                # deterministic paths
logger.warning(f"{LogTag.WARN} Rate limit hit, retrying")
logger.error(f"{LogTag.FAIL} Validation failed: {err}")
```

Use the logging bootstrap from `src/shared/logging_config.py`. Never write emoji tag strings by hand.

### LangGraph

- Default nodes to synchronous `def node(state) -> dict` unless genuinely async.
- Use `with_structured_output(...)` for all LLM calls.
- Expose Studio-friendly graphs through `create_studio_graph()`. Keep `langgraph.json` in sync.
- Resume logic must be deterministic and safe on empty payloads.
- Missing credentials fall back to a demo chain in dev only, where explicitly implemented.

### File I/O

- All file I/O goes through `DataManager` and module-local storage helpers.
- Direct `.read_text()` / `.write_text()` in runtime code under `src/core/ai`, `src/core/tools`, `src/graph` is banned.

## Key documentation

- Coding style: `docs/standards/code/basic.md`
- LangGraph component standards: `docs/standards/code/llm_langgraph_components.md`
- LangGraph methodology: `docs/standards/code/llm_langgraph_methodology.md`
- Documentation & planning guide: `docs/standards/docs/documentation_and_planning_guide.md`
- Major changes: `changelog.md`
- Deferred behavior: `future_docs/`

## Environment

```env
GOOGLE_API_KEY=...       # Gemini API access
GEMINI_API_KEY=...       # same key, both names accepted
LOG_DIR=logs             # directory for run-specific log files (default: logs/)
```

Requires: `pandoc` and `texlive-full` (or equivalent) installed for PDF rendering.
