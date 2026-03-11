# Match Review UI - Designer Handoff

## Goal

Design a UI for the `match` review cycle so reviewers do not edit markdown files manually.

The UI should make decisions faster, safer, and auditable.

## Context

Current runtime review cycle:

`match -> review_match -> (approve | request_regeneration | reject)`

What reviewer decides:

- Per requirement row: `Approve`, `Regenerate`, or `Reject`
- Optional reviewer notes
- Optional patch evidence when requesting regeneration

## Key user outcomes

1. Reviewer can complete decisions without formatting errors.
2. Reviewer sees exactly which requirement/evidence pair they are deciding on.
3. Reviewer sees round history and current status.
4. Reviewer can submit only valid decisions.

## Core data structures the UI will face

### 1) Match payload (read)

Path:

- `data/jobs/<source>/<job_id>/nodes/match/approved/state.json`

Fields used in UI:

- `matches[]`
  - `req_id`
  - `match_score`
  - `evidence_id`
  - `reasoning`
- `total_score`
- `decision_recommendation`
- `summary_notes`

### 2) Review input payload (read/write)

Path:

- `data/jobs/<source>/<job_id>/nodes/match/review/decision_input.json`

Shape:

```json
{
  "node": "review_match",
  "job_id": "<job_id>",
  "round": 1,
  "source_state_hash": "sha256:<64hex>",
  "review_status": "pending_review | in_review | submitted | processed",
  "timing": {
    "assigned_at": "<iso8601>",
    "started_at": "<iso8601|null>",
    "submitted_at": "<iso8601|null>",
    "processed_at": "<iso8601|null>"
  },
  "reviewer": {
    "reviewer_id": "<optional>",
    "display_name": "<optional>"
  },
  "items": [
    {
      "req_id": "REQ001",
      "decision": "approve | request_regeneration | reject | pending",
      "notes": "...",
      "patch_evidence": {
        "id": "PATCH_001",
        "description": "..."
      }
    }
  ]
}
```

### 3) Processed decision artifacts (read, history)

Paths:

- `data/jobs/<source>/<job_id>/nodes/match/review/decision.json`
- `data/jobs/<source>/<job_id>/nodes/match/review/rounds/round_<NNN>/decision.json`
- `data/jobs/<source>/<job_id>/nodes/match/review/rounds/round_<NNN>/feedback.json`

## Proposed UI flow

### Screen A: Review Queue

Shows jobs waiting at `review_match`.

Columns (minimum):

- Job ID
- Source
- Round
- Status (`pending_review`, `in_review`, `submitted`, `processed`)
- Assigned reviewer
- Last updated

Primary actions:

- Open review
- Claim review

### Screen B: Match Review Workspace

Top summary:

- `total_score`
- model recommendation (`decision_recommendation`)
- current round
- hash indicator (`source_state_hash` valid/mismatch)

Main table (one row per requirement):

- Requirement ID / text
- Evidence summary
- Match score
- Model reasoning
- Decision control (`Approve` / `Regenerate` / `Reject`)
- Notes input
- Patch evidence input (enabled when `Regenerate`)

Footer actions:

- Save draft
- Validate
- Submit review

### Screen C: Validation State

Before submit, show explicit checks:

1. All rows decided (no pending)
2. Hash still valid
3. Regenerate rows have actionable patch data

If any check fails, block submission and show row-level errors.

### Screen D: Outcome

After backend processes submission:

- Show aggregate route:
  - `approve` or `request_regeneration` or `reject`
- If regenerate, show link/button to next round.
- Show processed timestamp and artifact references.

## Interaction and UX constraints

1. Never require free-form syntax knowledge.
2. Use controlled components for decisions (radio/select).
3. Keep row-level validation inline and immediate.
4. Make regeneration-specific fields appear contextually.
5. Preserve round history visibility to reduce repeated comments.

## State lifecycle model

UI lifecycle states:

1. `pending_review` - generated and waiting
2. `in_review` - reviewer has started
3. `submitted` - reviewer finalized
4. `processed` - backend parsed and routed

Important: these are UI workflow states; graph routing still comes from deterministic backend decision processing.

## Designer deliverables requested

1. Queue screen wireframe
2. Match review workspace wireframe
3. Validation/error state variants
4. Outcome state variants (`approve`, `regenerate`, `reject`)
5. Mobile-safe layout behavior for row-heavy review tables
