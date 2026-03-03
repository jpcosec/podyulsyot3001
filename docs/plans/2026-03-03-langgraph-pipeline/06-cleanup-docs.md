# Phase 5: Cleanup + Documentation

## Context for subagent

You are completing the LangGraph pipeline migration at `/home/jp/phd`. Phases 0-4 built the full graph, extracted parsers/agents, implemented all nodes, and added CLI integration with checkpointing. Everything works. Now you need to:

1. Make the graph the only `run` execution path
2. Mark old step-based code as deprecated (individual step verbs may remain)
3. Update all documentation to reflect the new architecture
4. Write a comprehensive changelog entry

**Read before starting:**
- `docs/plans/2026-03-03-langgraph-pipeline/00-overview.md` — full migration overview
- `src/graph/pipeline.py` — the complete graph
- `src/cli/pipeline.py` — CLI with both old step commands and new graph commands
- `README.md` — top-level project documentation
- `CLAUDE.md` — agent instructions
- `docs/pipeline/match_review_regeneration_loop.md` — review loop documentation
- `docs/pipeline/end_to_end_pipeline_deep_dive.md` — pipeline architecture docs
- `src/cli/README.md` — CLI documentation
- `changelog.md` — project changelog

## Objectives

1. Make `pipeline job <id> run` invoke LangGraph directly (no legacy fallback)
2. Deprecate `src/steps/` with clear markers
3. Complete mandatory domain split from `src/utils/pipeline.py` into `src/graph/`
4. Update README.md with new `src/graph/` structure
5. Update CLAUDE.md with new commands
6. Update pipeline documentation
7. Final changelog entry

## What to do

### 1. Switch default execution in CLI

In `src/cli/pipeline.py`:
- Change `pipeline job <id> run` to invoke the LangGraph graph (was: call `_run_all_pending` which loops through step functions)
- Remove `pipeline job <id> run --legacy` (no runtime fallback after this migration)
- Keep individual step commands importable/executable (`job <id> ingest`, `job <id> match`, etc.) for targeted manual operation
- Rename `graph-run` → `run` and remove transitional alias once tests pass

This is a hard cutover. Tag the pre-cutover commit, then move forward with no CLI legacy execution mode.

### 1.5 Non-negotiable refactorings

These must be complete before Phase 5 can be considered done:

1. **Split keywords from matching in `src/steps/matching.py`**
   - Keyword extraction logic must no longer live inside `matching.py`
   - Use a dedicated keywords domain (`src/graph/nodes/keywords.py` and/or a focused step helper/module)
2. **Split domains in `src/utils/pipeline.py`**
   - Parsing, claim-building, and agent orchestration must be extracted into focused modules under `src/graph/`
   - `src/utils/pipeline.py` remains only as a compatibility shim with thin wrappers/re-exports where needed

### 2. Deprecate `src/steps/`

Add a deprecation notice to `src/steps/__init__.py`:

```python
"""
DEPRECATED: Step-based pipeline execution.

This package is superseded by src/graph/ (LangGraph-based pipeline).
Step functions remain importable for backwards compatibility but are no longer
the primary execution path. Use `pipeline job <id> run` (which now invokes
the LangGraph graph) or `pipeline job <id> graph-status` instead.
"""
```

Do NOT delete any files in `src/steps/` — they remain importable.

### 3. Thin out `src/utils/pipeline.py`

Replace the body of `src/utils/pipeline.py` with re-exports from `src/graph/`:

```python
"""
Backwards compatibility shim.

All pipeline logic has moved to src/graph/. This module re-exports
key symbols so existing imports continue to work.
"""
from src.graph.parsers.proposal_parser import parse_reviewed_proposal
from src.graph.parsers.claim_builder import build_claim_text as _propose_claim_text
from src.graph.agents.base import AgentRunner

# Keep CVTailoringPipeline and MatchProposalPipeline importable
# by defining thin wrappers that delegate to graph nodes
# ... (keep the class definitions if anything imports them directly)
```

**Important**: Check what imports `CVTailoringPipeline` and `MatchProposalPipeline` — if only `src/steps/cv_tailoring.py` and `src/steps/matching.py` import them, and those are deprecated, you can safely thin the file. If other code imports them, keep the classes as shims.

### 4. Update README.md

**Repository Structure section** — add `src/graph/` to the tree:
```
├── src/
│   ├── graph/                      # LangGraph pipeline coordinator
│   │   ├── state.py                # ApplicationState TypedDict
│   │   ├── pipeline.py             # StateGraph definition + edges
│   │   ├── nodes/                  # One module per pipeline node
│   │   │   ├── ingest.py
│   │   │   ├── match.py
│   │   │   ├── keywords.py
│   │   │   ├── review.py
│   │   │   ├── motivate.py
│   │   │   ├── tailor_cv.py        # LangGraph subgraph (matcher→seller→checker)
│   │   │   ├── email.py
│   │   │   ├── render.py
│   │   │   └── package.py
│   │   ├── agents/                 # LLM agent wrappers
│   │   │   ├── base.py             # AgentRunner (shared infra)
│   │   │   ├── matcher.py
│   │   │   ├── seller.py
│   │   │   └── checker.py
│   │   └── parsers/                # Deterministic parsing
│   │       ├── proposal_parser.py
│   │       └── claim_builder.py
│   ├── steps/                      # LEGACY — step functions (deprecated)
```

**Workflow Overview section** — update to describe the graph-based flow:
- Remove "Phase 10" references
- Describe the interrupt-based review loop
- Update CLI examples to use `run` / `run --resume`

**Key Modules section** — add Graph Coordinator subsection:
```
### Graph Coordinator (`src/graph/`)
- **`pipeline.py`** — `StateGraph` definition with 9 nodes and conditional review loop
- **`state.py`** — `ApplicationState` TypedDict carrying typed data between nodes
- **`nodes/`** — one focused module per pipeline step
- **`agents/`** — LLM agent wrappers (matcher, seller, checker)
- **`parsers/`** — deterministic parsing (proposal parser, claim builder)
- **`nodes/tailor_cv.py`** — CV tailoring as LangGraph subgraph (matcher → seller → checker)
```

**Deep Dive section** — add link to this migration plan.

**Dependencies section** — add `langgraph`, `langgraph-checkpoint-sqlite`.

### 5. Update CLAUDE.md

In the Common Commands section, add:
```bash
# Graph-based pipeline (default and only run path)
python src/cli/pipeline.py job 201084 run                       # run graph pipeline
python src/cli/pipeline.py job 201084 run --resume              # resume after review
python src/cli/pipeline.py job 201084 graph-status              # show graph state
```

In the Architecture section, add:
```
### Graph Coordinator (src/graph/)
Pipeline is now coordinated by a LangGraph `StateGraph`:
- 9 nodes: ingest → match → keywords → review_gate → motivate/tailor_cv → email/render → package
- `review_gate` uses `interrupt()` for human-in-the-loop review
- CV tailoring runs as a 3-agent subgraph (matcher → seller → checker)
- SQLite checkpointer persists state at `{job_dir}/.graph/checkpoints.db`
- Old step functions under `src/steps/` are deprecated but still importable
```

### 6. Update `docs/pipeline/match_review_regeneration_loop.md`

Rewrite to reflect the interrupt-based flow:

- **Section "End-to-end flow"**: update commands to use `run` / `--resume`
- **Section "What regeneration does"**: describe per-requirement directives (not JSON dump)
- **Section "Claim priority"**: add new section explaining edited claim > LLM > template
- **Section "Approval lock behavior"**: update to describe interrupt/resume instead of separate match-approve command
- Keep file versioning and evidence ID hygiene sections (unchanged logic)

### 7. Update `docs/pipeline/end_to_end_pipeline_deep_dive.md`

Add a section about the LangGraph coordinator:
- Graph DAG diagram
- Interrupt/resume UX
- Subgraph architecture for CV tailoring
- Checkpointing for cross-session persistence

## What NOT to do

- Do NOT delete `src/steps/` files — mark as deprecated, keep importable
- Do NOT delete `src/utils/pipeline.py` — thin it to re-exports
- Do NOT break the individual step commands (`job <id> ingest`, etc.)
- Do NOT change graph node implementations — they are complete
- Do NOT restructure `src/graph/` — the file layout is final
- Do NOT update memory files — those are auto-updated by the system

## Completion criteria

The phase is done when:
1. `pipeline job <id> run` invokes the LangGraph graph by default
2. `pipeline job <id> run --legacy` is removed
3. `src/steps/__init__.py` has deprecation notice
4. `src/utils/pipeline.py` is a thin re-export shim
5. `README.md` reflects current architecture (src/graph/ in tree, updated workflow, updated modules)
6. `CLAUDE.md` has new commands and architecture description
7. `docs/pipeline/match_review_regeneration_loop.md` describes interrupt-based flow
8. `src/cli/README.md` documents graph-first commands; no `run --legacy`
9. `changelog.md` has comprehensive migration entry
10. All tests pass: `pytest tests/ -x`
11. Existing imports from `src.utils.pipeline` still work
12. Keyword extraction is split out of `src/steps/matching.py`
13. `src/utils/pipeline.py` contains no mixed-domain business logic

## Commit

```
docs: complete LangGraph migration — update docs, deprecate steps

- Make LangGraph the only execution path for 'pipeline job <id> run'
- Remove run --legacy fallback mode
- Mark src/steps/ as deprecated (still importable)
- Thin src/utils/pipeline.py to re-exports from src/graph/
- Update README.md, CLAUDE.md, CLI docs, pipeline docs
```

Update `changelog.md`:
```
## 2026-03-03 — LangGraph Pipeline Migration: Phase 5 (Cleanup + Docs)

- `pipeline job <id> run` now invokes the LangGraph graph by default.
- Removed `run --legacy`; no fallback execution mode after migration cutover.
- Marked `src/steps/` as deprecated (still importable for backwards compatibility).
- Thinned `src/utils/pipeline.py` to re-exports from `src/graph/`.
- Updated `README.md` with `src/graph/` in repository structure, new workflow description, and graph coordinator documentation.
- Updated `CLAUDE.md` with graph-based commands and architecture section.
- Rewrote `docs/pipeline/match_review_regeneration_loop.md` for interrupt-based review flow.
- Updated `docs/pipeline/end_to_end_pipeline_deep_dive.md` with LangGraph architecture section.
- Updated `src/cli/README.md` with `run`, `run --resume`, and `graph-status` commands.
```
