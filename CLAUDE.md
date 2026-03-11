# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

PhD 2.0 is a graph-driven pipeline that produces PhD application artifacts (motivation letter, tailored CV, email) from job postings and a candidate profile knowledge base. It combines deterministic node contracts with LLM generation and mandatory human-in-the-loop review at each semantic gate.

## Commands

```bash
# Run all tests
python -m pytest tests/ -q

# Run tests for a specific module
python -m pytest tests/core/tools -q
python -m pytest tests/nodes/match -q

# Run a single test file
python -m pytest tests/core/tools/test_translation_service.py -q

# Run the prep-match flow (scrape -> translate -> extract -> match -> review_match)
python -m src.cli.run_prep_match \
  --source tu_berlin \
  --job-id 201399 \
  --source-url <URL> \
  --profile-evidence <path/to/evidence.json>

# Resume after HITL review decision
python -m src.cli.run_prep_match \
  --source tu_berlin \
  --job-id 201399 \
  --resume

# Select Gemini model (default: gemini-2.5-flash)
PHD2_GEMINI_MODEL=gemini-2.0-flash python -m src.cli.run_prep_match ...
```

## Architecture

### Three-layer source structure

- `src/core/` — deterministic only: contracts, tools (scraping, translation), round management, I/O layer. **Must never import from `src/ai/`.**
- `src/ai/` — LLM boundary: `LLMRuntime` (Gemini wrapper), `PromptManager` (Jinja2 template renderer).
- `src/nodes/` — per-node packages (`contract.py`, `logic.py`); LLM nodes also have `prompt/system.md` and `prompt/user_template.md`.
- `src/cli/` — operator entry points.
- `src/graph.py` — LangGraph app assembly and routing.

### Control plane vs. Data plane

**Control plane** (`GraphState` TypedDict in `src/core/graph/state.py`): carries only routing signals — `source`, `job_id`, `run_id`, `current_node`, `status`, `review_decision`, `error_state`. No artifact payloads in state.

**Data plane** (disk): all artifact content lives under `data/jobs/<source>/<job_id>/`. Each node writes to `nodes/<node>/{input,proposed,review,approved,meta}/`. JSON = machine truth, Markdown = human review surface.

### Node shape

Every node follows this package layout:
```
src/nodes/<node_name>/
  contract.py     # Pydantic input/output schemas
  logic.py        # pure business logic; no LangGraph coupling
  __init__.py
  prompt/         # LLM nodes only
    system.md
    user_template.md   # Jinja2 template
```

`logic.py` exports `run_logic(state: Mapping) -> dict` and is the LangGraph node handler. Full nodes (target architecture) will separate into `node.py` (orchestration) + `logic.py` (pure logic) using `WorkspaceManager` / `ArtifactReader` / `ArtifactWriter` from `src/core/io/` (not yet implemented; nodes currently do inline path I/O).

### Graph topology (`src/graph.py`)

Full pipeline: `scrape -> translate_if_needed -> extract_understand -> match -> review_match -> build_application_context -> review_application_context -> generate_motivation_letter -> review_motivation_letter -> tailor_cv -> review_cv -> draft_email -> review_email -> render -> package`

Review nodes have three branches: `approve` (continue), `request_regeneration` (loop back to generator), `reject` (end). Graph is checkpointed with SQLite (`langgraph.checkpoint.sqlite`). `thread_id` is `"{source}_{job_id}"`.

### HITL review loop

1. Generator node writes `nodes/<node>/approved/state.json` and `nodes/<node>/review/decision.md`.
2. Graph pauses (`interrupt_before` review node).
3. Human edits `decision.md` in Obsidian or any editor.
4. Human runs `--resume`; review node parses `decision.md`, validates `source_state_hash` against `proposed/state.json`, routes on `approve`/`request_regeneration`/`reject`.

The `RoundManager` (`src/core/round_manager.py`) tracks regeneration rounds under `nodes/match/review/rounds/round_<NNN>/`. Each regeneration round persists an immutable `decision.md` and `feedback.json`.

### Prompt rendering

`PromptManager` (`src/ai/prompt_manager.py`) loads node-local templates and renders them with Jinja2 (`StrictUndefined`). It validates required and optional XML tags (e.g. `<job_requirements>`, `<profile_evidence>`) in the rendered user prompt.

### Failure model

Nodes must fail closed — no silent fallback-to-success. Failure types are defined in `GraphState.ErrorContext`: `MODEL_FAILURE`, `TOOL_FAILURE`, `IO_FAILURE`, `INPUT_MISSING`, `SCHEMA_INVALID`, `POLICY_VIOLATION`, `PARSER_REJECTED`, `REVIEW_LOCK_MISSING`, `INTERNAL_ERROR`.

## Key documentation

- Graph topology and node roles: `docs/graph/nodes_summary.md`
- Node I/O contracts and artifact schemas: `docs/graph/node_io_matrix.md`, `docs/reference/artifact_schemas.md`
- Node template discipline: `docs/templates/node_template_discipline.md`
- Core I/O layer spec (target): `docs/architecture/core_io_and_provenance_manager.md`
- `sync_json_md` review surface service spec: `docs/business_rules/sync_json_md.md`
- Business rules: `docs/business_rules/claim_admissibility_and_policy.md`
- Step-by-step rebuild plan: `plan/phd2_stepwise_plan.md`

## Implementation status

The `core/io/` layer (`WorkspaceManager`, `ArtifactReader`, `ArtifactWriter`, `ProvenanceService`) is specified in docs but not yet implemented. Current nodes do inline path construction. When implementing new nodes, follow the target pattern from `docs/architecture/core_io_and_provenance_manager.md`.

The currently implemented subgraph is `prep_match`: scrape, translate_if_needed, extract_understand, match, review_match.
