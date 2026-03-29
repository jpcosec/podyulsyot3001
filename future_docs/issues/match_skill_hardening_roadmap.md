# Match Skill Hardening Roadmap

**Why deferred:** Core match skill flow is working. These items improve production-readiness but are not blocking current development.
**Last reviewed:** 2026-03-29

This document lists the main follow-up work that should be done after the initial `match_skill` implementation.

It focuses on the gap between what is already working and what would make the system more production-ready, easier to operate, and easier to evolve.

## Current Baseline

Already implemented:

- LangGraph-native orchestration graph
- LangChain-native prompt and structured output boundary
- Studio exposure through `langgraph.json`
- CLI run/resume flow
- JSON-first review and persistence artifacts
- automated tests for the core paths
- browser-assisted Studio inspection

What remains is mostly hardening, scalability, ergonomics, and observability work.

## Priority 1: Reduce Graph State Size

### Problem

`MatchSkillState` still carries full semantic payloads such as:

- `requirements`
- `profile_evidence`
- `effective_profile_evidence`
- `match_result`
- `active_feedback`

This is convenient for the current implementation, but it makes checkpoint state heavier than necessary.

### Why It Matters

- larger checkpoints
- slower graph persistence
- harder-to-reason-about state transitions
- more coupling between nodes

### Recommended Change

Move toward refs-only or mostly-refs state.

Instead of carrying large payloads in state, carry:

- `source`
- `job_id`
- `run_id` if needed
- `round_number`
- `status`
- `review_decision`
- artifact refs such as:
  - `requirements_ref`
  - `profile_evidence_ref`
  - `effective_profile_ref`
  - `match_result_ref`
  - `review_surface_ref`
  - `feedback_ref`

Then let each node load the artifact it needs from `MatchArtifactStore`.

### Suggested Steps

1. extend `MatchArtifactStore` so it can persist and load all node inputs explicitly
2. update `load_match_inputs` to write refs instead of returning full payloads
3. update downstream nodes to reload data from refs
4. keep only routing signals in `MatchSkillState`

## Priority 2: Add Artifact Schema Versioning

### Problem

Persisted JSON artifacts currently have no explicit schema version field.

### Why It Matters

- future schema evolution becomes ambiguous
- backward compatibility is harder to reason about
- migrations become brittle

### Recommended Change

Add a version marker to all persisted top-level payloads, for example:

- `schema_version: 1`

Suggested files:

- `approved/state.json`
- `review/current.json`
- `review/decision.json`
- `review/rounds/round_<NNN>/proposal.json`
- `review/rounds/round_<NNN>/decision.json`
- `review/rounds/round_<NNN>/feedback.json`

### Suggested Steps

1. introduce constants for schema versions in `src/ai/match_skill/storage.py`
2. write schema version into all persisted payloads
3. update loaders to validate or at least tolerate the version field
4. document version semantics in the product guide

## Priority 3: Evidence Filtering / Ranking Before Matching

### Problem

The current implementation sends all effective evidence into the match prompt.

If the evidence corpus grows, the model call may become:

- too expensive
- too slow
- too large for the context window

### Why It Matters

This is the most important product/runtime scalability gap in the current implementation.

### Recommended Change

Add a deterministic pre-match selection step that reduces evidence to only what is relevant.

Possible strategies:

- keyword overlap scoring
- embeddings-based retrieval
- rule-based requirement-to-evidence ranking
- a separate summarization stage for oversized evidence clusters

### Suggested Graph Extension

Insert a new step before `run_match_llm`, such as:

- `rank_profile_evidence`

Updated flow:

```text
load_match_inputs
  -> rank_profile_evidence
  -> run_match_llm
```

### Suggested Steps

1. define a deterministic evidence ranking contract
2. persist the ranked evidence subset or its ref
3. update prompt inputs to use the selected subset
4. add tests for oversized evidence scenarios

## Priority 4: Improve HITL Input UX (Status: COMPLETED)

### Problem

The workflow is semantically correct, but Studio is not yet a polished review UI.

Today the real review action is the submission of `review_payload`, not just pressing `Continue`.

### Why It Matters

- operators need a clearer review experience
- raw payload editing is error-prone
- Studio is good for debugging, but not ideal as a production review surface

### Recommended Change: Textual TUI

Building a reactive terminal-based review TUI allows for structured decisions and evidence patching without manual JSON editing.

**Implementation Details:**
- `src.review_ui.app.MatchReviewApp`: Main Textual application.
- `src.review_ui.screens.ReviewScreen`: Structured review form with `MatchRow` widgets.
- `src.review_ui.bus.MatchBus`: Async bridge for LangGraph thread resumption.
- CLI entry point for human reviewers: planned, see `future_docs/issues/review_ui_wiring.md`.

### Minimum Useful UX

The reviewer should be able to:

- see requirement rows
- see matched evidence and reasoning
- choose `approve`, `request_regeneration`, or `reject`
- attach patch evidence when needed
- submit a valid `ReviewPayload`

### Suggested Steps

1. treat `review/current.json` as the UI source payload
2. build a form/table that maps directly to `ReviewPayload`
3. keep hash validation in the backend
4. preserve round history exactly as it works now

## Priority 5: Improve Review Validation Structure

### Problem

Some validation lives directly in graph node logic.

That is fine for now, but the validation path could become cleaner.

### Recommended Change

Introduce a small validation service or helper for review application, for example:

- `validate_review_payload(payload, expected_hash)`

This keeps graph nodes orchestration-focused rather than validation-heavy.

### Suggested Steps

1. extract payload + hash validation from `apply_review_decision`
2. centralize row-to-feedback conversion logic
3. keep `apply_review_decision` focused on persistence + routing

## Priority 6: Add Explicit LangSmith Metadata And Tracing

### Problem

Studio is connected, but observability is still fairly local and operationally thin.

### Why It Matters

We want to know:

- cost per run
- round count per job
- frequency of regeneration
- whether patch evidence improves outcomes

### Recommended Change

Add explicit tags/metadata to the model runnable and graph invocations.

Useful metadata:

- `source`
- `job_id`
- `round_number`
- `review_decision`
- `regeneration_scope_size`
- `used_demo_chain`

### Suggested Steps

1. tag the LangChain runnable
2. add per-run metadata on invoke/resume
3. document recommended LangSmith dashboards/queries

## Priority 7: Make Studio And CLI Workflows More Reproducible

### Problem

The local workflow works, but some knowledge is still implicit.

### Recommended Change

Improve reproducibility by making it easier to replay runs.

Suggested additions:

- more sample payload sets
- a script for launching Studio with the correct env
- a script for creating a demo thread automatically
- a sample `LANGSMITH_API_KEY` setup guide if tracing is desired

## Priority 8: Separate Demo Mode From Real Mode More Explicitly

### Problem

The Studio fallback chain is useful, but it should be very clear when the system is in demo mode.

### Recommended Change

Make demo mode explicit in state or metadata.

Possible additions:

- `mode: demo | live`
- a visible warning in the review surface
- explicit metadata in traces and persisted artifacts

### Suggested Steps

1. add a mode flag to `create_studio_graph()` output metadata or state
2. persist that mode in review artifacts
3. surface it in docs and review payload examples

## Priority 9: Expand Test Coverage Around Edge Cases

### Missing Or Thin Areas

- very large evidence sets
- malformed patch evidence
- duplicate patch ids across rounds
- repeated regeneration loops
- mixed approve/reject/regenerate decisions in one payload
- artifact version compatibility once schema versioning is added

### Recommended Change

Expand tests in:

- `tests/test_match_skill.py`
- future storage-specific tests if storage logic grows

## Suggested Implementation Order

Recommended sequence:

1. refs-only state
2. artifact schema versioning
3. review validation extraction
4. evidence ranking/filtering
5. LangSmith metadata/tracing
6. improved reviewer UX
7. explicit demo/live mode separation
8. broader test coverage

## Definition Of "Hardened Enough" For The Next Milestone

The next milestone should be considered complete when:

- graph state is slim and mostly ref-based
- persisted artifacts carry a schema version
- large evidence sets are handled safely
- review submission is easier than raw payload editing
- live vs demo execution is clearly visible
- traces can answer round/cost/regeneration questions

At that point, the implementation would move from a strong reference prototype toward a more production-ready workflow component.
