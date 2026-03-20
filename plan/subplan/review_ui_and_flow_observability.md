# Review UI and Flow Observability Plan

Date: 2026-03-12

## Purpose

Define a concrete UI plan for:

1. Human review operations (starting with `review_match`, then all review gates).
2. Flow visualization per job and at global portfolio level.

This document extends prior review UI notes and adds observability scope explicitly.

## Existing Inputs

Related docs:

- `plan/subplan/ui_review_cycle_adaptation_internal.md`
- `plan/subplan/ui_review_cycle_designer_handoff.md`
- `docs/runtime/graph_flow.md`
- `docs/runtime/data_management.md`

## Product Surfaces

## Surface A - Review Workbench (Per Job)

Primary user:

- Reviewer who decides approve/regenerate/reject.

Minimum capabilities:

1. Claim/assign review.
2. Inspect model proposal and evidence side by side.
3. Provide structured decisions per row/section.
4. Submit only when deterministic validation passes.
5. Access round history and previous reviewer directives.

## Surface B - Job Flow Timeline (Per Job)

Primary user:

- Operator tracking where one job is blocked or failing.

Minimum capabilities:

1. Node-by-node timeline with status (`pending`, `running`, `paused_review`, `completed`, `failed`).
2. Active checkpoint identity (`thread_id`) and latest artifact pointers.
3. Error context display aligned with `GraphState.ErrorContext` taxonomy.
4. Quick jump from node status to artifact files.

## Surface C - Global Portfolio Dashboard

Primary user:

- Operator managing many jobs and bottlenecks.

Minimum capabilities:

1. Queue by stage (e.g., pending `review_match`, pending `review_cv`).
2. Throughput and lead time metrics by source and by stage.
3. Failure distribution by error type.
4. Regeneration frequency and rounds per job.

## Data Model (UI-facing)

## Job Read Model

```json
{
  "source": "tu_berlin",
  "job_id": "201399",
  "thread_id": "tu_berlin_201399",
  "current_node": "review_match",
  "status": "paused_review",
  "review": {
    "node": "review_match",
    "round": 2,
    "review_status": "in_review",
    "source_state_hash": "sha256:..."
  },
  "latest_error": {
    "error_type": "PARSER_REJECTED",
    "message": "...",
    "at_node": "review_match"
  }
}
```

## Global Read Model

```json
{
  "snapshot_at": "2026-03-12T10:30:00Z",
  "totals": {
    "jobs": 120,
    "completed": 43,
    "paused_review": 29,
    "failed": 8
  },
  "queues": {
    "review_match": 17,
    "review_application_context": 6,
    "review_motivation_letter": 4,
    "review_cv": 1,
    "review_email": 1
  },
  "stage_latency_hours": {
    "match_to_review_match": 5.2,
    "review_match_to_next": 12.8
  }
}
```

## Backend Adapter Strategy

Use a thin deterministic adapter service between filesystem artifacts and UI:

1. Read-only adapters for node status/history.
2. Write adapters only for review submission payloads.
3. Validation-first writes (reject malformed payloads before persistence).

Recommended stack:

- API: FastAPI (or equivalent lightweight HTTP layer).
- Storage model: filesystem artifacts as source of truth, optional cached index for dashboard queries.
- No coupling to LLM runtime internals.

## UI Rollout Phases

## Phase 1 - Match Review UI MVP

Includes:

1. Review queue for `review_match`.
2. Match review workbench with row-level decisions.
3. Deterministic validation state and submit.

Excludes:

- Global dashboard and non-match review nodes.

Gate:

- One full `match -> review_match -> resume` loop runs with no markdown editing.

## Phase 2 - Multi-Review Generalization

Includes:

1. Reusable review components for all review nodes.
2. Shared decision envelope contract per review type.
3. Standardized round history UI.

Gate:

- Same UI interaction model works for at least `review_match` and `review_motivation_letter`.

## Phase 3 - Flow Observability

Includes:

1. Per-job timeline screen.
2. Global dashboard and filters.
3. Aggregated metrics export (CSV/JSON).

Gate:

- Operator can identify top bottleneck stage and top error class without CLI inspection.

## Validation and Safety Requirements

1. UI submit must fail closed if hash mismatch is detected.
2. Regeneration decision must include actionable patch payload.
3. No UI action can directly mutate checkpoint state.
4. UI lifecycle states are orthogonal to graph routing states.

## UX Requirements (Desktop and Mobile)

1. Desktop-first table for row-dense review data.
2. Mobile fallback with card layout and progressive disclosure.
3. Sticky validation summary for long review sessions.
4. Clear "what changed since last round" indicators.

## Definition of Done

1. Reviewers no longer edit markdown review inputs manually.
2. Operators can inspect flow status per job in one screen.
3. Operators can monitor portfolio-level queue/latency/failures in one screen.
4. Deterministic review guarantees remain unchanged.
