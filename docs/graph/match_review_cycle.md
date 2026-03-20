# Match-Review Cycle (Actual Runtime Behavior)

Related references:

- `src/nodes/match/logic.py`
- `src/nodes/review_match/logic.py`
- `src/core/round_manager.py`
- `src/cli/run_prep_match.py`
- `src/graph.py`
- `docs/graph/node_io_matrix.md`
- `docs/reference/data_management_actual_state.md`

## Purpose

This document explains how the `match <-> review_match` loop works in the current codebase.

It is implementation-first and describes the runtime behavior of the prep-match graph used today.

## Scope

Current wired path (`create_prep_match_app()`):

`scrape -> translate_if_needed -> extract_understand -> match -> review_match -> generate_documents -> render -> package`

Review routing for this subgraph:

- `approve` -> `generate_documents` -> `render` -> `package`
- `request_regeneration` -> `match`
- `reject` -> end

## Inputs and prerequisites

### `match` node required state

- `state.job_id`
- `state.extracted_data.requirements` (non-empty list)
- `state.my_profile_evidence` (non-empty list)

On regeneration (`state.review_decision == "request_regeneration"`), `match` additionally requires latest review feedback from:

- `data/jobs/<source>/<job_id>/nodes/match/review/rounds/<latest>/feedback.json`

Fail-closed checks:

- feedback file must exist and parse as mapping,
- `round_n >= 1`,
- non-empty feedback list,
- at least one actionable patch entry (`action == "patch"` or valid `patch_evidence`).

### `review_match` node required state

- `state.source`
- `state.job_id`
- `state.matched_data.matches`

## Round storage model

`RoundManager` stores immutable review artifacts under:

- `nodes/match/review/rounds/round_<NNN>/`

Active review surface is mirrored at:

- `nodes/match/review/decision.md`

So each generation creates a new immutable round file and updates the active review file.

## Cycle walkthrough

### 1) `match` generates assessment and persists round

`match` calls the LLM with:

- `<job_requirements>` and `<profile_evidence>` always,
- optional `<round_feedback>` when regeneration feedback exists.

Then it persists:

1. `nodes/match/approved/state.json` (current canonical persisted match payload)
2. `nodes/match/review/rounds/round_<NNN>/decision.md`
3. mirrored `nodes/match/review/decision.md`

`decision.md` includes front matter:

- `source_state_hash: "sha256:<...>"`
- `node: "match"`
- `job_id`
- `round`

and a review table with per-requirement action checkboxes:

`[ ] Proceed / [ ] Regen / [ ] Reject`

The actionable table now includes a `Req ID` column so parser routing can remain stable even when only a subset of requirements is reviewed.

If regeneration context exists, the markdown also includes a "Feedback Applied from Round X" section.

### 2) Graph pauses at `review_match`

The graph is configured to interrupt before `review_match` in CLI runs.

Operator edits:

- `data/jobs/<source>/<job_id>/nodes/match/review/decision.md`

### 3) `review_match` validates and parses decisions

On resume, `review_match`:

1. Computes expected hash from `nodes/match/approved/state.json`.
2. Validates `source_state_hash` in `decision.md`.
3. Parses checkbox decisions deterministically.

Parsing order:

1. table format (`Action` and `Comments` columns),
2. per-block lines (`Decision [REQ_ID]: ...`),
3. global fallback (`Decision: ...` or `Decision [global]: ...`).

Accepted checkbox marks are strict but tolerant to spacing (for example `[]` and `[ x]`).

### 4) `review_match` writes machine artifacts

When decisions are valid and complete, it writes:

- `nodes/match/review/decision.json`
- `nodes/match/review/rounds/round_<NNN>/decision.json`
- `nodes/match/review/rounds/round_<NNN>/feedback.json`

`feedback.json` maps parsed decisions to actions:

- `approve` -> `proceed`
- `request_regeneration` -> `patch`
- `reject` -> `reject`

Route aggregation rule:

- any `reject` => route `reject`
- else any `request_regeneration` => route `request_regeneration`
- else all `approve` => route `approve`

### 5) Regeneration loop (`request_regeneration`)

When route is `request_regeneration`, graph returns to `match`.

`match` then:

1. loads latest round feedback,
2. appends valid `patch_evidence` items to effective evidence set,
3. derives regeneration scope from feedback entries with `action == "patch"`,
4. includes normalized feedback plus scope in prompt context,
5. generates a new match payload,
6. creates next immutable round (`round_<NNN+1>`).

During regeneration rounds, `decision.md` is split into:

- context section (non-scoped requirements, read-only),
- regeneration scope section (actionable rows only, revalidation loop input).

This avoids revalidating already approved requirements while still keeping full visibility in the review file.

## Hash lock behavior

`review_match` protects against stale review decisions:

- If checked decisions exist but `source_state_hash` is missing -> error.
- If embedded hash differs from current match payload hash -> error.
- If hash is missing and no boxes are checked (legacy blank review file) -> regenerate clean review markdown and remain pending.

This prevents applying human decisions to a different match state.

## Patch evidence injection format

Reviewer can attach extra evidence in comments using:

`PATCH_EVIDENCE: {"id":"<PATCH_ID>","description":"<TEXT>"}`

Valid patch evidence is extracted into `feedback.json` and later merged by `match` into effective profile evidence for next rounds.

## Common failure modes (fail closed)

1. Missing/invalid regeneration feedback file.
2. No actionable patch entries for regeneration.
3. Invalid checkbox markup (for example multiple checked options in one row).
4. Hash mismatch between reviewed markdown and current match payload.
5. Missing required state fields (`source`, `job_id`, `matched_data`, requirements, evidence).

## Operator loop (CLI)

Initial run:

```bash
python -m src.cli.run_prep_match \
  --source <source> \
  --job-id <job_id> \
  --source-url <url> \
  --profile-evidence <path_to_json>
```

Edit review markdown:

- `data/jobs/<source>/<job_id>/nodes/match/review/decision.md`

Resume:

```bash
python -m src.cli.run_prep_match --source <source> --job-id <job_id> --resume
```

Repeat until route is `approve` or `reject`.

## Current-state notes

- In the current prep graph, `review_match.approve` now continues into document generation and markdown delivery (`generate_documents -> render -> package`).
- The larger multi-stage target architecture still exists in planning docs, but this match-review loop is the operational gate in the runnable CLI flow today.
