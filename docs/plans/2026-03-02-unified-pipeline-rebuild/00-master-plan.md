# Unified Pipeline Rebuild Plan

Date: 2026-03-02
Status: Approved to start
Mode: Hard break (delete wrappers, rebuild orchestration)

## 1) Objective

Rebuild the application pipeline from scratch as one unified flow. Keep only foundational assets and deterministic engines. Remove all fragmented orchestration and service wrappers.

## 2) Keep vs Delete Boundaries

Keep (authoritative base):

- `src/utils/gemini.py`
- `src/prompts/*.txt` and `src/prompts/__init__.py`
- `src/models/*.py`
- `src/render/*.py`
- Deterministic scraper/translation primitives (`src/scraper/scrape_single_url.py`, `src/scraper/deterministic_extraction.py`, `src/scraper/translate_markdowns.py`, `src/scraper/deep_translate_jobs.py`)

Delete and rebuild:

- Existing orchestration wrappers in `src/cli/pipeline.py`
- Existing CV orchestration pipeline wrappers (`src/cv_generator/pipeline.py`, `src/cv_generator/ats.py`, CLI glue calling them)
- Existing multi-agent wrapper code (`src/agent/*`)
- Existing motivation orchestration service wrappers

## 3) Non-Negotiable Rules

1. No new hardcoded LLM wrappers inside feature modules.
2. Every LLM interaction must use one template executor.
3. One unified state object drives all phases.
4. Deterministic renderers remain deterministic.
5. Archived jobs are not touched by generation/translation flows.

## 4) New Pipeline Phases

1. Deterministic ingest/normalize
2. Context assembly and evidence catalog build
3. LLM matching
4. LLM gap proposals
5. LLM proposal synthesis
6. Human review gate
7. Deterministic CV render from approved proposal
8. LLM motivation letter generation
9. LLM email generation
10. Deterministic ATS/package/report

## 5) Work Packages

### WP-A: Foundation and Dependency Wiring

- Add LangGraph dependency and lock versions.
- Create `src/unified_pipeline/` package.
- Introduce unified state models and checkpoint schema.

### WP-B: LLM Call Template

- Build `src/unified_pipeline/llm/template.py` as the only LLM execution API.
- Responsibilities:
  - prompt loading + context injection
  - model call
  - JSON extraction and parsing
  - Pydantic validation
  - retry policy + error normalization
  - call-budget accounting
  - run telemetry

### WP-C: Graph Nodes

- Implement node modules under `src/unified_pipeline/nodes/`:
  - deterministic ingest
  - context build
  - match
  - gap proposal
  - final proposal
  - review gate
  - CV render
  - motivation
  - email
  - report/package

### WP-D: Unified CLI

- Replace fragmented commands with phase-aware entrypoints:
  - `pipeline unified-run <job_id>`
  - `pipeline unified-phase <job_id> --from <phase> --to <phase>`
  - `pipeline unified-review <job_id>`
  - `pipeline unified-resume <job_id>`

### WP-E: Migration and Cleanup

- Remove old wrappers/services.
- Provide migration notes from old artifacts to new artifact layout.
- Keep deterministic renderer and scraper contracts stable.

## 6) Testing Strategy

1. Unit tests for each graph node.
2. Contract tests for LLM template parser and retry logic.
3. Integration tests for one full unified run with mocked LLM.
4. Resume tests (fail at phase N, resume from phase N+1).
5. Deterministic rendering parity tests (DOCX/PDF extraction remains stable).

## 7) Definition of Done

- One graph run produces proposal, CV, motivation letter, and email.
- All LLM calls go through one template executor.
- No duplicated response parsing logic exists outside the template.
- Pipeline checkpoints support resume without repeating completed phases.
- Documentation reflects only the new flow.
