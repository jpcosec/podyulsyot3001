# Phase 0: Install LangGraph + Scaffold

## Context for subagent

You are working on a PhD application pipeline at `/home/jp/phd`. The project uses conda environment `phd-cv` (Python 3.11), dependencies are in `environment.yml`. The codebase has a step-based pipeline under `src/steps/` that we are migrating to a LangGraph `StateGraph`. This is Phase 0 — you are laying the foundation.

**Read before starting:**
- `docs/plans/2026-03-03-langgraph-pipeline/00-overview.md` — full migration overview
- `src/utils/state.py` — `JobState` class, `STEP_OUTPUTS`, `STEP_ORDER`
- `src/models/pipeline_contract.py` — existing Pydantic models (`PipelineState`, `EvidenceItem`, `RequirementMapping`, `ProposedClaim`, `ReviewedClaim`, `ReviewedMapping`)

## Objectives

1. Install `langgraph` and `langgraph-checkpoint-sqlite` into the conda environment
2. Create the `src/graph/` directory structure with all necessary `__init__.py` files
3. Define `ApplicationState` TypedDict in `src/graph/state.py`
4. Create `src/graph/pipeline.py` with a compilable graph skeleton (all nodes as pass-through stubs, all edges wired)
5. Write a smoke test that compiles the graph and invokes it with minimal state

## What to do

### 1. Install dependencies

Add to `environment.yml` under pip dependencies:
```yaml
- langgraph>=0.4
- langgraph-checkpoint-sqlite>=2.0
```

Run `pip install langgraph langgraph-checkpoint-sqlite` to install immediately.

### 2. Create directory structure

```
src/graph/
  __init__.py               # exports: compile_pipeline, ApplicationState
  state.py                  # ApplicationState TypedDict
  pipeline.py               # StateGraph definition with stubs
  nodes/
    __init__.py
    ingest.py               # stub
    match.py                # stub
    keywords.py             # stub
    review.py               # stub
    motivate.py             # stub
    tailor_cv.py            # stub
    email.py                # stub
    render.py               # stub
    package.py              # stub
  agents/
    __init__.py
    base.py                 # stub (will hold shared agent logic)
    matcher.py              # stub
    seller.py               # stub
    checker.py              # stub
  parsers/
    __init__.py
    proposal_parser.py      # stub
    claim_builder.py        # stub
```

### 3. Define ApplicationState

In `src/graph/state.py`:

```python
from __future__ import annotations
import operator
from typing import Annotated, TypedDict


class ApplicationState(TypedDict, total=False):
    # Identity (set at start, never changes)
    job_id: str
    source: str

    # Ingestion outputs
    job_posting: dict | None

    # Matching outputs
    evidence_items: list[dict]
    requirement_mappings: list[dict]
    keywords: dict

    # Review state
    reviewed_claims: list[dict]
    review_round: int
    proposal_path: str

    # Motivation outputs
    motivation_letter_md: str
    motivation_data: dict

    # CV tailoring outputs
    proposed_claims: list[dict]
    to_render_md: str

    # Email output
    email_draft_md: str

    # Rendering outputs
    rendered_paths: list[str]

    # Final
    final_pdf_path: str | None

    # Accumulated (append-only across nodes)
    comments: Annotated[list[dict], operator.add]

    # Config (set once at start)
    force: bool
    language: str
    render_via: str
    docx_template: str
```

### 4. Create graph skeleton in `src/graph/pipeline.py`

Define all 9 nodes as stub functions that return empty dicts (pass-through). Wire all edges including:
- `START → ingest → match → keywords → review_gate`
- Conditional edge after `review_gate`: if any edited claims → `match`, else → `motivate`
- `motivate → email → package`
- `review_gate → tailor_cv → render → package`
- `package → END`

Use `MemorySaver` checkpointer for the skeleton (SQLite comes in Phase 4).

Expose `compile_pipeline()` function that returns the compiled graph.

### 5. Write smoke test

In `tests/graph/test_pipeline.py`:
- Test that `compile_pipeline()` returns without error
- Test that invoking the graph with `{"job_id": "test", "source": "tu_berlin", "review_round": 0, "force": False}` runs through all stubs to END (since review_gate stub returns no edited claims, it should route forward)

## What NOT to do

- Do NOT implement any real node logic — stubs only return `{}`
- Do NOT modify any existing files under `src/steps/`, `src/utils/`, or `src/cli/`
- Do NOT delete or rename anything
- Do NOT add LangChain dependencies — only `langgraph` and its checkpoint package
- Do NOT use `langchain_core` for the LLM calls — we use our own `GeminiClient`

## Completion criteria

The phase is done when:
1. `pip show langgraph` shows the package installed
2. `environment.yml` has the new dependencies
3. All files in `src/graph/` exist with correct structure
4. `python -c "from src.graph import compile_pipeline; g = compile_pipeline(); print('OK')"` works
5. `pytest tests/graph/test_pipeline.py` passes
6. All existing tests still pass: `pytest tests/ -x --ignore=tests/graph`

## Commit

```
feat: scaffold LangGraph pipeline structure

- Install langgraph and langgraph-checkpoint-sqlite
- Create src/graph/ with state definition and stub graph
- All 9 nodes wired as pass-through stubs
- Smoke test verifies compilation and invocation
```

Update `changelog.md` with a new entry at top:
```
## 2026-03-03 — LangGraph Pipeline Migration: Phase 0 (Scaffold)

- Installed `langgraph` and `langgraph-checkpoint-sqlite` dependencies.
- Created `src/graph/` package with `ApplicationState` TypedDict and compilable `StateGraph` skeleton.
- All 9 pipeline nodes defined as stubs with correct edge wiring (including conditional review loop).
- Added smoke test in `tests/graph/test_pipeline.py`.
```
