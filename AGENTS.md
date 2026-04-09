# AGENTS.md

Guidance for coding agents working in `podyulsyot3001`.

## Project Overview

- Python codebase for a modular job-application pipeline.
- Main modules under `src/`:
  - `src/core/` - core infrastructure (DataManager, API client, state)
  - `src/core/ai/generate_documents_v2/` - LangGraph document generation
  - `src/core/tools/translator/` - translate job artifacts
  - `src/core/tools/render/` - deterministic PDF/DOCX rendering
  - `src/review_ui/` - Textual human review UI
- Main entrypoint: `python -m src.cli.main`
- LangGraph entrypoint: `langgraph.json` -> `src.core.ai.generate_documents_v2.graph:create_studio_graph`

## Standards Reference

All implementation must align with `docs/standards/`:
- `docs/standards/code/basic.md` - coding style and patterns
- `docs/standards/code/llm_langgraph_components.md` - LLM/LangGraph patterns
- `docs/standards/docs/documentation_and_planning_guide.md` - documentation conventions

## Environment And Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Required env vars for LLM flows:
```bash
export GOOGLE_API_KEY=...
export GEMINI_API_KEY=...
export LOG_DIR=logs
```

PDF rendering requires `pandoc` and a TeX distribution.

## Build, Run, And Test Commands

### Install
```bash
pip install -r requirements.txt
pip install -e .
```

### Main runtime commands
```bash
python -m src.cli.main api start
python -m src.cli.main pipeline --source xing --job-id 148172603
python -m src.cli.main run-batch --sources xing stepstone --limit 5
python -m src.cli.main review
python -m src.cli.main generate --source xing --job-id 148172603 --language en --render
python -m src.cli.main render cv --source xing --job-id 148172603 --language en
python -m src.cli.main translate --source xing
```

### Test commands
- Active suite: `python -m pytest tests/unit tests/test_generate_documents_v2 -q`
- Full suite: `python -m pytest tests/ -q`
- Single test file: `python -m pytest tests/unit/cli/test_main.py -q`
- Test subtree: `python -m pytest tests/unit/core/ai/generate_documents_v2 -q`

## Workflow Expectations

- Prefer small, targeted changes.
- Follow existing module boundaries.
- For major workflow changes, update docs and append to `changelog.md`.
- Keep runtime state on disk; keep graph state thin.

## Imports

- Use `from __future__ import annotations` at top of modules.
- Group imports: (1) standard library, (2) third-party, (3) local `src.*`.
- Prefer absolute imports from `src...` over fragile relative imports.
- Avoid wildcard imports.

## Formatting And File Structure

- Use ASCII by default unless target file already uses Unicode.
- Add short module docstring at top of each file.
- Every public function/method/class needs a structured docstring.
- Prefer short functions with one responsibility.
- Avoid comments unless clarifying a non-obvious invariant.

## Naming Conventions

- Modules/functions: `snake_case`
- Classes/Pydantic models: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Internal helpers: prefix with `_`
- Parser builders: `_build_parser()` in CLI modules.
- LangGraph nodes: `load_*`, `build_*`, `persist_*`, `apply_*`, `prepare_*`

## Types And Data Modeling

- Add type hints everywhere practical.
- Use `list[str]`, `dict[str, Any]`, `tuple[str, str]` for built-in generics.
- Use `TypedDict` for graph state and lightweight dicts.
- Use Pydantic models for external contracts, LLM outputs, review payloads.
- Add `Field(description=...)` on Pydantic fields consumed by LLMs.
- Prefer explicit return types on public functions.

## Error Handling

- Fail closed; don't silently convert failure to success.
- Prefer domain-specific exceptions over bare `Exception`.
- Log before re-raising with `from exc` when catching broad exceptions.
- Preserve stack traces.
- Validate required inputs early and raise fast.
- Treat missing review payloads as explicit states, not undefined.

## Logging And Observability

- Use `logging.getLogger(__name__)`.
- Use shared logging bootstrap from `src/shared/logging_config.py`.
- Import `LogTag` from `src/shared/log_tags.py`.
- Use `LogTag.LLM` for LLM-invoking paths, `LogTag.FAST` for deterministic paths.
- Use `LogTag.WARN` / `LogTag.FAIL` for warnings and failures.

## LangGraph And Agent-Specific Guidance

- Default nodes to synchronous `def node(state) -> dict` unless genuinely async end-to-end.
- Keep graph state small; persist heavy payloads to artifacts.
- Use `with_structured_output(...)` for LLM calls.
- Expose Studio-friendly graphs through `create_studio_graph()`.
- Keep `langgraph.json` in sync.
- Resume logic must be deterministic and safe on empty payloads.

## File I/O And Persistence

- Prefer centralized file I/O through `DataManager` and storage helpers.
- Legacy guardrail bans direct `.read_text()`, `.write_text()`, etc. in runtime code under `src/core/ai`, `src/core/tools`, `src/graph`.
- Follow local module pattern when editing existing code.
- Don't scatter new ad hoc persistence logic across node implementations.

## Testing Expectations

- Add or update focused unit tests near the changed module.
- Prefer narrow test files under `tests/unit/...`.
- Run affected test file plus `tests/unit/core/ai/generate_documents_v2` when changing generate_documents_v2.
- Run `tests/unit/cli/test_main.py` when changing CLI behavior.

## Documentation Expectations

- Keep top-level docs aligned with `README.md`.
- Keep module-specific docs in module directory.
- Record major changes in `changelog.md`.
- Track deferred behavior in `future_docs/` rather than documenting as supported.