# Agent Entrypoint

This file is the fastest way for a new coding agent to understand and operate this repository.

## 1) What This Codebase Is For

This repo implements a human-in-the-loop pipeline for PhD/job application support.

Current implemented runtime scope:

1. Scrape one job posting.
2. Translate if needed.
3. Extract structured job requirements.
4. Match requirements against profile evidence.
5. Stop at review gate and require a human decision.
6. Resume with deterministic routing (`approve`, `request_regeneration`, `reject`).

The current executable subgraph is the prep+match flow, not the full end-to-end architecture target.

## 2) Core Runtime Surfaces

- Graph assembly: `src/graph.py`
- Graph state contract: `src/core/graph/state.py`
- Operator CLI (current bootstrap entrypoint): `src/cli/run_prep_match.py`
- Current node packages:
  - `src/nodes/scrape/`
  - `src/nodes/translate_if_needed/`
  - `src/nodes/extract_understand/`
  - `src/nodes/match/`
  - `src/nodes/review_match/`

## 3) What Each Implemented Step Does

1. `scrape`
   - Reads `source_url`, fetches posting content, and builds ingestion payload for downstream steps.
2. `translate_if_needed`
   - Detects/normalizes language and translates only when required.
3. `extract_understand` (LLM)
   - Produces structured job understanding (requirements and related metadata).
4. `match` (LLM)
   - Maps job requirements to profile evidence.
   - Writes `nodes/match/approved/state.json`.
   - Generates review markdown for human evaluation.
5. `review_match` (deterministic gate)
   - Reads and parses `nodes/match/review/decision.md`.
   - Enforces source hash checks to prevent stale decisions.
   - Emits routing decision:
     - `approve` -> `package` (prep terminal)
     - `request_regeneration` -> back to `match`
     - `reject` -> end
6. `package` (prep terminal in current graph)
   - Marks run as completed for this subgraph.

## 4) Exact Run Loop (Today)

Before running/resuming, export `.env` variables into the current shell:

```bash
set -a; source .env; set +a
```

Run until first review gate:

```bash
python -m src.cli.run_prep_match \
  --source tu_berlin \
  --job-id 201588 \
  --run-id run-local \
  --source-url https://www.jobs.tu-berlin.de/en/job-postings/201588 \
  --profile-evidence data/reference_data/profile/base_profile/profile_base_data.json
```

Then edit:

- `data/jobs/<source>/<job_id>/nodes/match/review/decision.md`

Resume:

```bash
python -m src.cli.run_prep_match --source <source> --job-id <job_id> --resume
```

Checkpoint path (default):

- `data/jobs/<source>/<job_id>/graph/checkpoint.sqlite`

Thread identity invariant:

- `thread_id = f"{source}_{job_id}"`

## 5) Required Environment Assumptions

- Use conda environment `phd-cv`:
  - `conda activate phd-cv`
- Export repository `.env` into the shell before any run/resume command:
  - `set -a; source .env; set +a`
- Python dependencies are expected to be installed in that environment.
- `langgraph` available (graph compile + sqlite checkpointing).
- `google-generativeai` available for LLM nodes.
- Valid API credentials for Gemini in environment.
- Optional model override:
  - `PHD2_GEMINI_MODEL` (default in code: `gemini-2.5-flash`).

## 6) Data and Artifact Conventions

Job workspace root:

- `data/jobs/<source>/<job_id>/`

Important artifacts in current flow:

- `nodes/match/approved/state.json`
- `nodes/match/review/decision.md`
- `nodes/match/review/decision.json` (written after parsing)
- `nodes/match/review/rounds/round_<NNN>/...` (round history)

Control plane vs data plane intent:

- `GraphState` should carry routing/control metadata.
- Heavy semantic payloads should live in on-disk artifacts.
- Current implementation still carries some transient payloads in state; this is a known transition state.

## 7) How To Extend The Codebase Safely

When adding a new step/node:

1. Create a node package under `src/nodes/<node_name>/` with:
   - `contract.py` (schemas/contracts)
   - `logic.py` (node behavior)
   - prompt files if LLM-driven
2. Keep deterministic parsing/validation fail-closed (no silent success fallbacks).
3. Add or update tests under `tests/nodes/<node_name>/`.
4. Wire the node into graph topology in `src/graph.py`:
   - register handler in node registry
   - add linear edge(s)
   - add review transitions if it is a review gate
5. Keep resume semantics stable:
   - same `thread_id` convention
   - decisions parsed from artifacts, not injected ad hoc
6. Update docs to reflect runtime truth:
   - `docs/runtime/graph_flow.md`
   - `docs/operations/tool_interaction_and_known_issues.md`
   - `README.md` if user-facing behavior changed

## 8) Known Reality: Implemented vs Target Graph

Implemented runtime graph is the prep-match flow through delivery: `scrape -> translate_if_needed -> extract_understand -> match -> review_match -> generate_documents -> render -> package`.

Target architecture docs still describe additional phases (`build_application_context`, motivation letter/CV/email review cycles, etc.). Treat those as target unless explicitly wired in `src/graph.py`.

## 9) First Commands A New Agent Should Run

```bash
conda activate phd-cv
set -a; source .env; set +a
rg --files
python -m pytest -q
python -m src.cli.run_prep_match --help
```

Then inspect:

- `src/graph.py`
- `src/cli/run_prep_match.py`
- `src/nodes/*/logic.py`
- `docs/operations/tool_interaction_and_known_issues.md`
