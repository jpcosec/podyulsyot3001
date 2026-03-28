# Match Skill Product Guide

This guide documents the implemented `match_skill` itself: its purpose, file structure, orchestration logic, persistence model, Studio exposure, and the intended human-in-the-loop workflow.

## Goal

The `match_skill` is a LangGraph + LangChain-native implementation of the `dev` branch match-review-regeneration workflow.

It is designed to provide:

- structured requirement-to-evidence matching,
- a checkpointed human review gate,
- deterministic regeneration with patch evidence,
- JSON-first persisted artifacts,
- LangGraph Studio visibility,
- CLI and API-driven replay for testing.

## Main Files And Their Roles

### `src/match_skill/contracts.py`

Owns the typed contracts for the whole feature.

It defines:

- input models like `RequirementInput` and `ProfileEvidence`,
- LLM output models like `RequirementMatch` and `MatchEnvelope`,
- human review models like `ReviewPayload`,
- persistence/UI models like `ReviewSurface`.

This file is the schema backbone of the feature.

### `src/match_skill/prompt.py`

Owns prompt construction only.

It:

- builds the `ChatPromptTemplate`,
- serializes requirements, evidence, feedback, and regeneration scope into prompt blocks,
- keeps prompt formatting separated from graph orchestration.

### `src/match_skill/storage.py`

Owns persistence only.

It:

- allocates round numbers,
- writes `approved/state.json`,
- writes `review/current.json`,
- writes per-round proposal/decision/feedback JSON,
- computes `source_state_hash`,
- reloads patch evidence from prior rounds.

### `src/match_skill/graph.py`

Owns orchestration.

It:

- defines the LangGraph state,
- creates the graph nodes and edges,
- builds the real LangChain model chain,
- provides the Studio-safe fallback chain,
- defines how review, resume, and regeneration work.

### `src/match_skill/__init__.py`

Owns the public import surface.

It exposes the important contracts, graph builders, and storage types without requiring consumers to import deep internal modules.

### `src/cli/run_match_skill.py`

Owns local operator entrypoints.

It:

- starts a new run from JSON inputs,
- resumes a paused run from a structured review payload,
- wires the graph to a SQLite checkpoint store,
- prints a compact JSON summary for the operator.

### `langgraph.json`

Owns LangGraph Studio discovery.

It exposes the graph as:

- `match_skill: src.match_skill.graph:create_studio_graph`

### `tests/test_match_skill.py`

Owns graph-level behavior verification.

It tests:

- approval,
- regeneration,
- stale hash rejection,
- safe continue-without-payload behavior.

### `tests/test_run_match_skill.py`

Owns CLI-level verification.

It tests the run/resume behavior of the local CLI wrapper.

### `test_assets/match_assets/*.json`

Owns replayable example payloads for Studio or CLI demos.

## Logic Structure

The implementation is intentionally split by responsibility.

### Contract Layer

`src/match_skill/contracts.py` defines the shapes of data at each boundary.

This ensures that:

- the LLM output is validated,
- review input is validated,
- persistence payloads are stable,
- changes remain explicit rather than implicit.

### Prompt Layer

`src/match_skill/prompt.py` keeps all prompt serialization in one place.

This means prompt changes do not require changing graph logic.

### Persistence Layer

`src/match_skill/storage.py` isolates file operations from graph logic.

This keeps node behavior easier to reason about and easier to test.

### Orchestration Layer

`src/match_skill/graph.py` is the workflow controller.

It is responsible for:

- state transitions,
- model invocation,
- breakpoint placement,
- review routing,
- regeneration routing.

### Interaction Layer

Interaction happens through:

- the local CLI,
- the LangGraph API,
- LangGraph Studio,
- **The Match Review TUI** (a structured terminal interface for operators),
- the persisted JSON review surface.

## Graph Structure

The main graph nodes are:

- `load_match_inputs`
- `run_match_llm`
- `persist_match_round`
- `human_review_node`
- `apply_review_decision`
- `prepare_regeneration_context`
- **`generate_documents`**

Flow:

```text
__start__
  -> load_match_inputs
  -> run_match_llm
  -> persist_match_round
  -> human_review_node
  -> apply_review_decision
     -> generate_documents -> __end__
     -> reject -> __end__
     -> prepare_regeneration_context -> run_match_llm
```

This is a real orchestration graph, not just a single function pretending to be a workflow.

## Node-By-Node Responsibilities

### `load_match_inputs`

This node prepares the round input.

It:

- validates `source` and `job_id`,
- validates requirements,
- validates base profile evidence,
- rebuilds `effective_profile_evidence`,
- merges patch evidence from previous rounds when needed.

### `run_match_llm`

This node is the LLM boundary.

It:

- builds prompt variables,
- invokes the LCEL chain,
- validates the returned `MatchEnvelope`,
- stores the structured result in graph state.

### `persist_match_round`

This node materializes the current proposal to disk.

It:

- assigns the next round number,
- writes the approved proposal JSON,
- computes the current proposal hash,
- writes the review surface JSON,
- returns refs and hash into state.

### `human_review_node`

This node is primarily a breakpoint anchor.

It exists so the graph can pause before semantic review is applied. It is intentionally thin.

### `apply_review_decision`

This node applies the structured review payload.

It:

- validates the payload,
- checks the `source_state_hash`,
- converts review rows into deterministic `FeedbackItem`s,
- persists decision and feedback artifacts,
- aggregates the route,
- returns a `Command` to either finish, generate documents, or regenerate.

It also safely handles the case where Studio resumes with no payload by returning to review instead of raising an error.

### `prepare_regeneration_context`

This node prepares another model pass.

It:

- confirms that regeneration was requested,
- computes the regeneration scope,
- merges patch evidence,
- carries deterministic feedback forward,
- clears stale review input,
- routes back into `run_match_llm`.

### `generate_documents`

This node triggers once the match phase is approved.

It:

- loads the candidate base profile,
- builds a tailored document generation prompt using approved matches,
- invokes a structured-output LLM chain (`DocumentDeltas`),
- runs deterministic review indicators (anti-fluff, line limits),
- renders Jinja2 templates for CV, Cover Letter, and Email,
- persists the final Markdown artifacts.

## LangChain Boundary

The model boundary is intentionally narrow.

- prompt building happens through `ChatPromptTemplate`,
- model invocation happens through `with_structured_output(MatchEnvelope)`.

This keeps the model interaction idiomatic and strongly typed.

## Persistence Model

Artifacts are written under:

`output/match_skill/<source>/<job_id>/nodes/match_skill/`

Important files:

- `approved/state.json`
- `review/current.json`
- `review/decision.json`
- `review/rounds/round_<NNN>/proposal.json`
- `review/rounds/round_<NNN>/decision.json`
- `review/rounds/round_<NNN>/feedback.json`

This structure gives:

- a canonical latest proposal,
- a current review surface,
- immutable round history.

## How HITL Is Intended To Work

The HITL model is structured, not ad hoc.

The intended workflow is:

1. run the graph until it pauses before `human_review_node`,
2. inspect the graph state and/or `review/current.json`,
3. review each requirement row,
4. submit a typed `review_payload`,
5. resume the graph,
6. repeat if regeneration creates another review round.

The human is expected to make explicit semantic decisions, not just press continue.

### Human Responsibilities

The reviewer is responsible for:

- checking whether the selected evidence is correct,
- deciding whether a row is acceptable,
- deciding whether regeneration is needed,
- providing patch evidence when regeneration is requested,
- rejecting the run if it should not continue.

### System Responsibilities

The system is responsible for:

- pausing at the right moment,
- preserving enough review context,
- validating payload shape,
- rejecting stale review payloads,
- translating review into deterministic routing,
- preserving round history.

### Why `Continue` Alone Is Not Enough

In this design, `Continue` is only a transport action.

The semantic decision comes from `review_payload`. Without that payload, the graph does not know whether the reviewer wants:

- approval,
- regeneration,
- rejection.

That is why the system now treats a bare continue as a safe no-op that returns to `pending_review`.

## LangGraph Studio Exposure

The graph is exposed through `langgraph.json` and loaded by `create_studio_graph()`.

Studio behavior:

- with Gemini credentials, it uses the real model chain,
- without credentials, it uses a deterministic demo chain so the graph can still be exercised.

This makes Studio useful both for real runs and for graph-level debugging.

## CLI Usage

### Start A New Run

```bash
python -m src.cli.run_match_skill \
  --source demo \
  --job-id 123 \
  --requirements test_assets/match_assets/sample_requirements.json \
  --profile-evidence test_assets/match_assets/sample_profile_evidence.json
```

### Resume A Paused Run

```bash
python -m src.cli.run_match_skill \
  --source demo \
  --job-id 123 \
  --resume \
  --review-payload test_assets/match_assets/sample_review_payload_regenerate.json
```

Checkpoint file:

`output/match_skill/<source>/<job_id>/graph/checkpoint.sqlite`

## Sample Payloads

Replayable examples live under `test_assets/match_assets/`:

- `sample_requirements.json`
- `sample_profile_evidence.json`
- `sample_review_payload_approve.json`
- `sample_review_payload_regenerate.json`

Replace `REPLACE_WITH_MATCH_RESULT_HASH` with the active thread's `match_result_hash` before using the review payload examples.

## Operational Caveats

- The local Studio/dev server is in-memory, so thread ids do not survive restarts.
- To advance the workflow meaningfully, a valid `review_payload` must be supplied.
- `.langgraph_api/` and `output/` are local runtime state and are ignored in `.gitignore`.
