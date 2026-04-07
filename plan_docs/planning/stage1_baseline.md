# Stage 1 — Baseline & Inventory

> Methodology reference: `docs/standards/feature_creation_methodology.md`
>
> Status: **COMPLETE** — all in-scope tests pass, issue inventory documented.

---

## Worktree Scope

This worktree uses **sparse checkout** scoped to the automation pipeline only:

| Included | Excluded (other worktree / main branch) |
|----------|-----------------------------------------|
| `src/apply/` | `src/core/ai/` (generate_documents_v2) |
| `src/scraper/` | `src/core/tools/` (render, translator) |
| `src/shared/` | `src/cli/` |
| `src/core/data_manager.py` + `state.py` (stub) | `tests/legacy/`, `tests/unit/cli/`, `tests/unit/core/` |
| `tests/unit/apply/` | |
| `tests/unit/scraper/` | |

---

## Current Module Layout

### `src/apply/` — Application execution

| File | Responsibility |
|------|---------------|
| `browseros_client.py` | BrowserOS MCP HTTP client; snapshot parsing |
| `browseros_executor.py` | Step-by-step playbook runner against BrowserOS |
| `browseros_backend.py` | Provider builder; wires client + executor + playbooks |
| `browseros_models.py` | `BrowserOSPlaybook` Pydantic model |
| `models.py` | `FormSelectors`, `ApplyMeta`, `ApplicationRecord` contracts |
| `smart_adapter.py` | `ApplyAdapter` ABC; idempotency, script rendering, selector checks |
| `main.py` | CLI entrypoint; dispatches to BrowserOS backend |
| `providers/{linkedin,stepstone,xing}/adapter.py` | Portal-specific selectors, scripts, URLs |

### `src/scraper/` — Job listing ingestion

| File | Responsibility |
|------|---------------|
| `models.py` | `JobPosting` Pydantic model |
| `smart_adapter.py` | `SmartScraperAdapter` ABC; persist listings + raw artifacts |
| `main.py` | CLI entrypoint; PROVIDERS registry, batch scrape loop |
| `providers/{stepstone,xing,tuberlin}/adapter.py` | Portal-specific link extraction and scrape logic |

### Shared dependencies (in-scope stubs)

| File | Responsibility |
|------|---------------|
| `src/shared/log_tags.py` | `LogTag` StrEnum — structured log tags |
| `src/core/data_manager.py` | `DataManager` — job artifact I/O under `data/jobs/` |
| `src/core/state.py` | `GraphState`, `RunStatus`, `ErrorContext` TypedDicts |

---

## Test Baseline

Run: `python -m pytest tests/ -q` (2026-04-05)

```
57 passed, 6 skipped
```

### Test coverage map

| Test module | Tests | Notes |
|-------------|-------|-------|
| `tests/unit/apply/browseros/test_client.py` | 3 passed | |
| `tests/unit/apply/browseros/test_executor.py` | 6 passed | |
| `tests/unit/apply/browseros/test_models.py` | 1 passed | |
| `tests/unit/apply/providers/linkedin/test_adapter.py` | 8 passed, 2 skipped | |
| `tests/unit/apply/providers/stepstone/test_adapter.py` | 8 passed, 2 skipped | |
| `tests/unit/apply/providers/xing/test_adapter.py` | 10 passed, 2 skipped | |
| `tests/unit/apply/test_models.py` | 4 passed | |
| `tests/unit/apply/test_smart_adapter.py` | 15 passed | |
| `tests/unit/scraper/test_smart_adapter.py` | 2 passed | |

### Skipped tests (6)

Pattern: `test_mandatory_selectors_found_in_fixture` and `test_optional_selectors_found_in_fixture` for all 3 providers.

**Reason**: require captured HTML fixture files at `tests/fixtures/apply/{linkedin,stepstone,xing}_apply_modal.html`.
**How to create**: `python scripts/capture_linkedin_apply_fixture.py --job-url <URL>` (per provider).
**Action**: acceptable skip — fixtures require live browser session. Not a blocker.

---

## Dependency Audit

### External imports from `src/apply/` and `src/scraper/`

These cross-package imports will require re-pointing during the refactor:

| Importing module | Dependency | Notes |
|-----------------|------------|-------|
| `apply/browseros_client.py` | `src.shared.log_tags.LogTag` | moves to new shared location |
| `apply/browseros_executor.py` | `src.shared.log_tags.LogTag` | same |
| `apply/browseros_backend.py` | `src.shared.log_tags.LogTag`, `src.core.data_manager.DataManager` | both move |
| `apply/smart_adapter.py` | `src.shared.log_tags.LogTag`, `src.core.data_manager.DataManager` | both move |
| `apply/main.py` | `src.shared.log_tags.LogTag`, `src.core.data_manager.DataManager` | both move |
| `scraper/smart_adapter.py` | `src.shared.log_tags.LogTag`, `src.core.data_manager.DataManager` | both move |
| `scraper/main.py` | `src.shared.log_tags.LogTag`, `src.core.data_manager.DataManager` | both move |

**Refactor note**: `src.core.data_manager` and `src.shared` will move to `automation/` as part of the structural refactor. All 7 import sites must be updated in the same migration step.

---

## Issue Inventory

### I-1: `src/core/__init__.py` eagerly imports `state.py`

**Location**: `src/core/__init__.py:4`

```python
from src.core.state import ErrorContext, GraphState, RunStatus
```

If only `data_manager.py` is available, the package fails to import. Breaks any module that does `from src.core.data_manager import DataManager` via package init side effects.

**Resolution**: In the refactor, expose `DataManager` directly from its new home — do not re-export via package `__init__.py`.

---

### I-2: `DataManager` default path relies on CWD

**Location**: `src/core/data_manager.py:41`

```python
def __init__(self, jobs_root: str | Path = "data/jobs") -> None:
```

Works when invoked from project root. Breaks silently if CWD differs.

**Resolution**: The refactor should pass `jobs_root` explicitly from the CLI entrypoint using `Path(__file__).parents[N] / "data/jobs"`.

---

### I-3: Provider profile paths are hardcoded relative strings

**Location**: `src/apply/providers/{linkedin,stepstone,xing}/adapter.py`

```python
return Path("data/profiles/linkedin_profile")  # and variants
```

Same CWD dependency as I-2.

**Resolution**: Derive from project root in the new portal definitions.

---

### I-4: `scraper/main.py` creates `DataManager` at module import time

**Location**: `src/scraper/main.py:42`

```python
# PROVIDERS dict is built at module load, creating DataManager on import
```

Module-level side effect — prevents testing the module without a `data/` directory present.

**Resolution**: Move `PROVIDERS` construction into `main()` or a factory function.

---

### I-5: `scraper/smart_adapter.py` — naive language detection

**Location**: `src/scraper/smart_adapter.py:113`

Heuristic fails on short or mixed-language postings. Documented in `plan_docs/issues/gaps/language-detection-hardening.md`.

**Resolution**: Deferred — acceptable for current scope.

---

### I-6: `scraper/providers/xing/adapter.py` — generated CSS class names

**Location**: `src/scraper/providers/xing/adapter.py:108`

Portal rebuilds silently break selectors. Documented in `plan_docs/issues/gaps/xing-listing-metadata-composition.md`.

**Resolution**: Deferred — portal-level fragility, tracked issue.

---

### I-7: `scraper/providers/stepstone/adapter.py` — links lose listing metadata

**Location**: `src/scraper/providers/stepstone/adapter.py:55`

`extract_links` returns plain URL strings, dropping listing-side metadata.

**Resolution**: Deferred — tracked in `plan_docs/issues/gaps/discovery-entry-contract.md`.

---

### I-8: `apply/smart_adapter.py` — profile field override not implemented

**Location**: `src/apply/smart_adapter.py:348`

```python
# TODO: override in adapter or subclass to include candidate personal fields
```

Placeholder. Subclasses cannot inject custom profile fields into form-filling context.

**Resolution**: Design in the portal contracts (Stage 4).

---

## Checklist

- [x] Current module layout mapped
- [x] Dependency audit (cross-package imports listed)
- [x] Test baseline run: 57 passed, 6 skipped (acceptable)
- [x] Skipped tests explained and categorized
- [x] Issue inventory: 8 issues documented (I-1 to I-8)
- [x] `src/shared/log_tags.py` SyntaxWarning fixed (invalid `\[` escape in docstring)
- [x] Sparse checkout scope documented

**Stage 1 is complete. Ready to proceed to Stage 2.**
