# Match Skill Studio Implementation Guide

This guide explains how the new `match_skill` was implemented, how it is exposed through LangGraph Studio, how we interacted with it during development, and what operational workflow now exists for testing and review.

## Goal

The objective was to copy the `dev` branch match-review-regeneration behavior in a more LangGraph + LangChain-native way.

The intended result was:

- explicit LangGraph orchestration instead of a mostly monolithic custom node flow,
- LangChain-native prompt and structured-output handling,
- LangGraph-native human-in-the-loop pause/resume,
- Studio visibility for the graph,
- a local CLI and replayable payloads for testing,
- a clean path for browser-assisted Studio interaction.

## What Was Built

The implementation lives primarily in `src/match_skill/` and `src/cli/run_match_skill.py`.

Key files:

- `src/match_skill/contracts.py`
- `src/match_skill/prompt.py`
- `src/match_skill/storage.py`
- `src/match_skill/graph.py`
- `src/match_skill/__init__.py`
- `src/cli/run_match_skill.py`
- `langgraph.json`
- `tests/test_match_skill.py`
- `tests/test_run_match_skill.py`

## File Roles

This section describes what each file is responsible for and why the logic is split this way.

### Core Match Skill Files

- `src/match_skill/contracts.py`
  - owns all typed schemas,
  - defines the model input/output contract,
  - defines the review payload contract,
  - defines the persisted review-surface contract.

- `src/match_skill/prompt.py`
  - owns prompt construction only,
  - converts typed inputs into serialized prompt blocks,
  - keeps prompt logic separate from orchestration logic.

- `src/match_skill/storage.py`
  - owns file persistence only,
  - writes round artifacts and current review state,
  - computes hashes and collects patch evidence across rounds.

- `src/match_skill/graph.py`
  - owns orchestration,
  - wires nodes, edges, interrupts, and resume behavior,
  - contains the default real model chain and the Studio-safe fallback chain.

- `src/match_skill/__init__.py`
  - exposes the public API,
  - gives external callers a stable import surface.

### Entry and Integration Files

- `src/cli/run_match_skill.py`
  - runs a new thread from JSON inputs,
  - resumes a paused thread from a review payload,
  - manages the SQLite checkpointer path for local use.

- `langgraph.json`
  - tells LangGraph Studio which graph to load,
  - points Studio to `src.match_skill.graph:create_studio_graph`.

### Validation and Replay Files

- `tests/test_match_skill.py`
  - tests the graph behavior directly,
  - covers approve, regenerate, stale hash rejection, and safe bare-continue behavior.

- `tests/test_run_match_skill.py`
  - tests the CLI run/resume flow.

- `test_assets/match_assets/*.json`
  - provides replayable inputs and sample review payloads for Studio or CLI demos.

## Logic Structure

The implementation is intentionally split by responsibility instead of placing all logic into one graph file.

### 1. Contract Layer

The contract layer lives in `src/match_skill/contracts.py`.

Its role is to define the shape of data at every important boundary:

- before the model call,
- after the model call,
- before the human review step,
- after the human review step,
- on disk in persisted artifacts.

This keeps validation close to the boundary where it matters.

### 2. Prompt Layer

The prompt layer lives in `src/match_skill/prompt.py`.

Its role is to:

- build a `ChatPromptTemplate`,
- serialize requirements/evidence/feedback/scope into consistent text blocks,
- avoid mixing prompt formatting with graph node code.

### 3. Persistence Layer

The persistence layer lives in `src/match_skill/storage.py`.

Its role is to:

- persist each round proposal,
- persist each review decision,
- persist deterministic feedback,
- compute `source_state_hash`,
- rebuild patch evidence across rounds.

### 4. Orchestration Layer

The orchestration layer lives in `src/match_skill/graph.py`.

Its role is to:

- load and validate state,
- invoke the model chain,
- stop at the review gate,
- apply structured review decisions,
- route either to `END` or back into regeneration.

### 5. Interaction Layer

The interaction layer is split between:

- `src/cli/run_match_skill.py` for terminal-driven runs,
- LangGraph Studio for graph-driven debugging and manual review,
- the local LangGraph API for scripted control.

## Node-by-Node Logic

### `load_match_inputs`

This node prepares all inputs needed for the current round.

It:

- validates `source` and `job_id`,
- validates requirements,
- validates base profile evidence,
- merges prior patch evidence when needed,
- computes `effective_profile_evidence`.

This is a deterministic preparation step.

### `run_match_llm`

This node is the LLM boundary.

It:

- builds prompt variables,
- invokes the LangChain runnable,
- validates the returned `MatchEnvelope`,
- stores the structured result into graph state.

### `persist_match_round`

This node persists the current proposal.

It:

- allocates the next round number,
- writes `approved/state.json`,
- computes the proposal hash,
- writes the current and round-scoped review surface,
- exposes refs and `match_result_hash` in graph state.

### `human_review_node`

This node is mostly a breakpoint target.

It exists so the graph can pause before review is applied.

It does not perform heavy logic by design. Its job is to provide a stable HITL pause point.

### `apply_review_decision`

This node applies the structured human review.

It:

- validates `review_payload`,
- rejects stale payloads using `source_state_hash`,
- converts row-level decisions into deterministic `FeedbackItem`s,
- computes the aggregate route,
- persists `decision.json` and `feedback.json`,
- returns a `Command` that routes either to `__end__` or `prepare_regeneration_context`.

It now also safely handles the case where Studio resumes without any payload by returning to review instead of failing.

### `prepare_regeneration_context`

This node prepares the next generation pass.

It:

- validates that regeneration was actually requested,
- computes the regeneration scope,
- merges patch evidence into the effective evidence set,
- carries forward deterministic feedback,
- clears the previous `review_payload`,
- routes back to `run_match_llm`.

## Architecture

### Graph Shape

The graph is defined in `src/match_skill/graph.py` and compiled by `build_match_skill_graph()`.

Nodes:

- `load_match_inputs`
- `run_match_llm`
- `persist_match_round`
- `human_review_node`
- `apply_review_decision`
- `prepare_regeneration_context`

Flow:

```text
__start__
  -> load_match_inputs
  -> run_match_llm
  -> persist_match_round
  -> human_review_node
  -> apply_review_decision
     -> __end__
     -> prepare_regeneration_context -> run_match_llm
```

This gives a proper LangGraph orchestration graph with an explicit regeneration loop.

### LangChain Boundary

The LLM side is intentionally narrow.

- `src/match_skill/prompt.py` builds the prompt with `ChatPromptTemplate`
- `build_default_match_chain()` in `src/match_skill/graph.py` uses `ChatGoogleGenerativeAI(...).with_structured_output(MatchEnvelope)`

This means prompt rendering and structured parsing are handled in native LangChain style instead of a custom prompt/runtime wrapper.

### Structured Contracts

`src/match_skill/contracts.py` defines:

- model input types like `RequirementInput` and `ProfileEvidence`
- model output types like `RequirementMatch` and `MatchEnvelope`
- human review types like `ReviewPayload`
- persisted UI/persistence types like `ReviewSurface`

This keeps the model boundary, review boundary, and persistence boundary explicit.

### Persistence

`src/match_skill/storage.py` writes JSON-first artifacts under:

`output/match_skill/<source>/<job_id>/nodes/match_skill/`

Key artifact files:

- `approved/state.json`
- `review/current.json`
- `review/decision.json`
- `review/rounds/round_<NNN>/proposal.json`
- `review/rounds/round_<NNN>/decision.json`
- `review/rounds/round_<NNN>/feedback.json`

The review surface is intentionally JSON-first rather than markdown-first so Studio, a custom UI, or a CLI can all consume the same persisted shape.

## Human Review Model

### Breakpoint Strategy

The graph is compiled with:

- `interrupt_before=["human_review_node"]`

That means the graph pauses right before the review node executes.

The normal resume pattern is:

1. run the graph until it pauses,
2. inspect state and/or `review/current.json`,
3. write `review_payload` into the thread state,
4. resume the graph.

### Review Payload

The expected payload is the `ReviewPayload` schema. It contains:

- `source_state_hash`
- `items[]`
  - `requirement_id`
  - `decision`
  - `note`
  - optional `patch_evidence`

### How HITL Is Intended To Work

The intended human-in-the-loop model is structured review, not freeform continuation.

The expected operator workflow is:

1. let the graph run until it pauses before `human_review_node`,
2. inspect the graph state and/or `review/current.json`,
3. decide row by row whether each requirement should be approved, regenerated, or rejected,
4. submit a typed `review_payload`,
5. resume the graph,
6. repeat if regeneration creates another review round.

The important design choice is that the human is not editing hidden internal state blindly. The human is expected to provide an explicit typed decision payload that the graph can validate and normalize.

### HITL Responsibilities

The human review step is responsible for:

- checking whether the model selected the right evidence,
- deciding whether weak or missing matches need regeneration,
- supplying patch evidence when regeneration is requested,
- rejecting the run when the proposal should not continue.

### HITL Responsibilities Of The System

The system is responsible for:

- pausing at the correct review point,
- preserving enough context for the reviewer,
- rejecting stale review payloads,
- translating human actions into deterministic graph routing,
- keeping an immutable round history.

### Why This Is Not Just "Click Continue"

`Continue` alone is not meant to be the decision mechanism.

In this design, `Continue` is only the transport action that resumes execution after the human decision has already been supplied. The real semantic action is the submission of `review_payload`.

That is why:

- a valid review payload advances the workflow,
- bare continue now safely does nothing meaningful and returns to review.

### Important UX Fix

During Studio testing we discovered that pressing `Continue` without submitting a `review_payload` caused the next node to validate `None` as `ReviewPayload` and fail.

That was fixed in `src/match_skill/graph.py` so a bare continue now safely returns to the review pause with `status = pending_review` instead of crashing.

## LangGraph Studio Integration

### Studio Exposure

The graph is exposed through `langgraph.json`:

```json
{
  "dependencies": [
    "."
  ],
  "graphs": {
    "match_skill": "src.match_skill.graph:create_studio_graph"
  }
}
```

Studio uses `create_studio_graph()` rather than the generic builder directly.

### Why a Studio Factory Exists

`create_studio_graph()` exists so Studio can always load the graph.

Behavior:

- if `GOOGLE_API_KEY` or `GEMINI_API_KEY` is present, Studio uses the real Gemini-backed chain,
- otherwise Studio uses a deterministic demo chain so the graph can still be explored and exercised end-to-end.

This was necessary because otherwise Studio would show the topology but fail at runtime for anyone missing model credentials.

## Browser Bridge and Studio Interaction

### Why the Browser Bridge Was Needed

We wanted not only to run the graph through the API, but also to inspect and navigate the Studio UI directly from the agent.

That required the OpenCode browser bridge.

### Setup

Required installation step:

```bash
npx @different-ai/opencode-browser install
```

After installation:

- restart the CLI session,
- ensure the extension/backend is running,
- confirm the broker socket exists at `~/.opencode-browser/broker.sock`.

### What We Verified

We confirmed:

- browser bridge loaded,
- broker connected,
- Studio tab could be opened,
- the current graph page could be inspected,
- the live thread page could be navigated.

## Local LangGraph Server Workflow

### Dependency Setup

To make local Studio/dev-server work, `requirements.txt` was updated to include:

- current direct runtime versions,
- `langgraph-cli[inmem]`,
- `pytest`.

The `phd-cv` conda environment was then removed and recreated from `requirements.txt`.

### Launch Command

The local dev server was launched with:

```bash
conda run -n phd-cv langgraph dev --config langgraph.json --no-browser --port 8124
```

Useful endpoints:

- API root: `http://127.0.0.1:8124`
- API docs: `http://127.0.0.1:8124/docs`
- Studio: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8124`

### Important Runtime Note

The current setup uses the in-memory LangGraph runtime for local development. That means thread ids do not survive server restarts.

This came up during testing: a previously valid thread id opened in Studio later returned `404` after the server had been restarted.

That is expected behavior for the in-memory dev server.

## How We Tested the Flow

### Automated Tests

The following tests were added:

- `tests/test_match_skill.py`
- `tests/test_run_match_skill.py`

They cover:

- approve path,
- regeneration path,
- stale review hash rejection,
- continue-without-payload safety,
- CLI run/resume flow.

### Manual API Exercise

We also exercised the graph through the local LangGraph API by:

1. searching assistants,
2. creating a thread,
3. invoking `/threads/{thread_id}/runs/wait`,
4. inspecting `/threads/{thread_id}/state`,
5. posting `review_payload` into `/threads/{thread_id}/state`,
6. resuming the thread,
7. verifying regeneration state and pending review transitions.

### Manual Studio Exercise

We then opened Studio against the local server and confirmed:

- the graph topology renders,
- the assistant is connected,
- a live thread can be opened,
- the node history is visible,
- the graph pauses at `human_review_node`,
- the right-hand thread panel shows turn history and current node progression.

## Sample Payloads

Replayable examples live under `test_assets/match_assets/`:

- `sample_requirements.json`
- `sample_profile_evidence.json`
- `sample_review_payload_approve.json`
- `sample_review_payload_regenerate.json`

Important:

- replace `REPLACE_WITH_MATCH_RESULT_HASH` with the actual `match_result_hash` from the current paused thread before using the review payload examples.

## CLI Usage

### Start a New Run

```bash
python -m src.cli.run_match_skill \
  --source demo \
  --job-id 123 \
  --requirements test_assets/match_assets/sample_requirements.json \
  --profile-evidence test_assets/match_assets/sample_profile_evidence.json
```

### Resume a Paused Run

```bash
python -m src.cli.run_match_skill \
  --source demo \
  --job-id 123 \
  --resume \
  --review-payload test_assets/match_assets/sample_review_payload_regenerate.json
```

The CLI persists checkpoints in:

`output/match_skill/<source>/<job_id>/graph/checkpoint.sqlite`

## Planning and Implementation Approach

The implementation process followed this sequence:

1. inspect the `dev` branch match flow,
2. separate product behavior from framework plumbing,
3. preserve the behavior that matters,
4. replace the custom prompt/runtime layer with LangChain-native primitives,
5. express review/regeneration as explicit LangGraph nodes,
6. expose the graph to Studio,
7. validate through tests, API runs, and Studio/browser interaction,
8. harden the UX after discovering the bare-continue failure mode.

In practical terms, the planning decisions were:

- keep deterministic review and regeneration logic custom,
- let LangGraph own orchestration and pause/resume,
- let LangChain own prompt + structured output,
- keep persisted artifacts JSON-first,
- support Studio even without model credentials.

## Operational Caveats

- The local dev server is in-memory; thread ids do not survive restarts.
- Studio can continue a thread without a payload; this is now safe, but it will not advance the review.
- To advance beyond review meaningfully, a valid `review_payload` must be submitted.
- Local `.langgraph_api/` and `output/` runtime state are ignored in `.gitignore` because they are generated during local operation.

## Current Status

For the current scope, the implementation is complete.

Completed:

- LangGraph-native orchestration graph,
- LangChain-native structured-output boundary,
- Studio exposure,
- CLI run/resume path,
- browser-assisted Studio inspection,
- fresh environment rebuild from `requirements.txt`,
- automated tests.

Future improvements that are optional rather than blocking:

- a better Studio-native review form,
- a custom lightweight review UI,
- wiring the skill into a larger pipeline graph,
- replacing the demo chain with mandatory real model execution if desired.
