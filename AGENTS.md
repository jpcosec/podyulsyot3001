# AGENTS.md

Guidance for coding agents working in `podyulsyot3001`.

## Project Overview

- Python codebase for a modular job-application pipeline.
- Main modules live under `src/`:
  - `src/core/` - core infrastructure (DataManager, API client, state)
  - `src/core/ai/generate_documents_v2/` - LangGraph document generation
  - `src/core/tools/translator/` - translate job artifacts
  - `src/core/tools/render/` - deterministic PDF/DOCX rendering
  - `src/review_ui/` - Textual human review UI
- Main operator entrypoint: `python -m src.cli.main`
- LangGraph assistant entrypoint: `langgraph.json` -> `src.core.ai.generate_documents_v2.graph:create_studio_graph`
- Python package metadata in `pyproject.toml` with package-dir mapping to `src/`

## Standards Reference

All implementation, tests, and documentation must stay aligned with `docs/standards/`:
- `docs/standards/code/basic.md` - coding style and patterns
- `docs/standards/code/llm_langgraph_components.md` - LLM/LangGraph component patterns
- `docs/standards/code/llm_langgraph_methodology.md` - LLM/LangGraph development methodology
- `docs/standards/docs/documentation_and_planning_guide.md` - documentation conventions
- `docs/standards/docs/documentation_quality_checklist.md` - docs quality checklist
- `docs/standards/docs/future_docs_guide.md` - future_docs/ usage guide
- `docs/standards/feature_creation_methodology.md` - feature development workflow
- `docs/standards/issue_guide.md` - issue handling process

## Environment And Setup

- Dependencies in `requirements.txt`.
- Typical setup:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

- Required env vars for LLM-backed flows:

```bash
export GOOGLE_API_KEY=...
export GEMINI_API_KEY=...
export LOG_DIR=logs
```

- Rendering PDF output also requires external tools such as `pandoc` and a TeX distribution.

## Build, Run, And Test Commands

### Install / package

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
python -m src.cli.main review --source xing --job-id 148172603
python -m src.cli.main generate --source xing --job-id 148172603 --language en --render
python -m src.cli.main render cv --source xing --job-id 148172603 --language en
python -m src.cli.main translate --source xing
```

### Test commands

- Active suite that passes in the current repo:

```bash
python -m pytest tests/unit tests/test_generate_documents_v2 -q
```

- Full suite:

```bash
python -m pytest tests/ -q
```

- Single test file:

```bash
python -m pytest tests/unit/cli/test_main.py -q
python -m pytest tests/unit/core/ai/generate_documents_v2/test_profile_updater.py -q
```

- Test subtree:

```bash
python -m pytest tests/unit/core/ai/generate_documents_v2 -q
```

## Workflow Expectations

- Prefer small, targeted changes.
- Follow existing module boundaries instead of introducing cross-cutting helpers casually.
- For major workflow changes, update relevant docs and append an entry to `changelog.md`.
- Keep runtime state and heavy payloads on disk; keep graph state thin.
- Do not revive deleted legacy modules just to satisfy old tests unless the task explicitly requires it.

## Repository Architecture Conventions

- Each module should have one clear responsibility.
- Public surface goes through `__init__.py`; avoid deep imports from implementation internals when a public import exists.
- `main.py` is for CLI entrypoints only.
- `data_manager.py` or `storage.py` owns persistence and artifact paths.
- `contracts/` or `contracts.py` owns typed schemas.
- `graph.py` owns orchestration, nodes, edges, and Studio graph exposure.
- Prompt construction belongs in dedicated prompt modules, not in graph wiring.

## Imports

- Use `from __future__ import annotations` at the top of Python modules.
- Group imports in this order:
  1. standard library
  2. third-party packages
  3. local `src.*` imports
- Prefer absolute imports from `src...` over fragile relative imports.
- Keep imports explicit; avoid wildcard imports.

## Formatting And File Structure

- Use ASCII by default unless the target file already uses Unicode or Unicode is clearly needed.
- Add a short module docstring at the top of each file describing its role.
- Every public function, method, and class should have a structured docstring.
- Prefer short functions with one responsibility.
- If a function accumulates too much state or too many local variables, consider extracting helpers or introducing a class.
- Avoid comments unless they clarify a non-obvious invariant or workflow detail.

## Naming Conventions

- Modules and functions: `snake_case`
- Classes and Pydantic models: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Internal helpers: prefix with `_`
- Parser builders should use `_build_parser()` in CLI modules.
- LangGraph node names should reflect role clearly, such as `load_*`, `build_*`, `persist_*`, `apply_*`, `prepare_*`.

## Types And Data Modeling

- Add type hints everywhere practical.
- Prefer precise built-in generics like `list[str]`, `dict[str, Any]`, and `tuple[str, str]`.
- Use `TypedDict` for graph state and lightweight dictionaries.
- Use Pydantic models for external contracts, structured LLM outputs, persisted review payloads, and artifact schemas.
- Add meaningful `Field(description=...)` text on Pydantic fields, especially when the schema is consumed by an LLM.
- Prefer explicit return types on public functions.

## Error Handling

- Fail closed; do not silently convert failure into success.
- Prefer domain-specific exceptions over bare `Exception` for control flow.
- If you catch a broad exception for a fallback, log it first and re-raise with `from exc` when appropriate.
- Preserve stack traces.
- Validate required inputs early and raise fast when missing.
- Treat missing review payloads or interrupted HITL resumes as explicit states, not undefined behavior.

## Logging And Observability

- Use `logging.getLogger(__name__)`.
- Use shared logging bootstrap from `src/shared/logging_config.py` at entrypoints.
- Import `LogTag` from `src/shared/log_tags.py`.
- Never hardcode emoji tags by hand.
- Use `LogTag.LLM` only for LLM-invoking paths.
- Use `LogTag.FAST` for deterministic paths and `LogTag.WARN` / `LogTag.FAIL` for warnings and failures.

## LangGraph And Agent-Specific Guidance

- Default graph nodes to synchronous `def node(state) -> dict` unless the work is genuinely async end-to-end.
- Keep graph state small; persist heavy payloads to artifacts instead of carrying them through state.
- Use `with_structured_output(...)` for LLM calls rather than parsing free-form strings.
- Expose Studio-friendly graphs through `create_studio_graph()` and keep `langgraph.json` in sync.
- Review flows are payload-driven; resume logic must be deterministic and safe on empty payloads.

## File I/O And Persistence

- Prefer centralized file I/O patterns through `DataManager` and related storage helpers.
- There is a legacy guardrail test that bans direct `.read_text()`, `.write_text()`, `.read_bytes()`, `.write_bytes()`, and `.mkdir()` calls in much of runtime code under `src/core/ai`, `src/core/tools`, and `src/graph`.
- Some current files already exceed that older rule, so use judgment and follow the local module pattern when editing existing code.
- Do not scatter new ad hoc persistence logic across node implementations.

## Testing Expectations For Changes

- Add or update focused unit tests near the changed module.
- Prefer narrow test files under `tests/unit/...`.
- When changing `generate_documents_v2`, run at least the affected test file plus `python -m pytest tests/unit/core/ai/generate_documents_v2 -q` if practical.
- When changing CLI behavior, run `python -m pytest tests/unit/cli/test_main.py -q`.

## Documentation Expectations

- Keep top-level workflow docs aligned with behavior in `README.md`.
- Keep module-specific docs in the module directory.
- Record every major change in `changelog.md`.
- If behavior is intentionally deferred, track it in `future_docs/` rather than documenting it as supported.
