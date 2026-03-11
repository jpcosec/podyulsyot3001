# UI Review Cycle Adaptation - Internal Engineering Subplan

## Purpose

Migrate `match <-> review_match` from Markdown-authored review input (`decision.md`) to structured UI-authored JSON input, while preserving deterministic routing and fail-closed guarantees.

## Codebase baseline (actual current state)

Anchors:

- `src/nodes/match/logic.py`
- `src/nodes/review_match/logic.py`
- `src/nodes/review_match/contract.py`
- `src/core/round_manager.py`
- `src/core/graph/state.py`
- `src/graph.py`

Current behavior:

1. `match` writes `nodes/match/approved/state.json` and review markdown (`decision.md`) per round.
2. `review_match` parses markdown checkboxes, validates `source_state_hash`, writes `decision.json` and `feedback.json`, and sets route.
3. Regeneration loop feeds `feedback.json` back into `match` via `RoundManager`.

## Migration objective

### Replace review input source of truth

From:

- `nodes/match/review/decision.md` (human-edited)

To:

- `nodes/match/review/decision_input.json` (UI-authored)

### Preserve existing machine outputs

Keep these outputs for compatibility and audit:

- `nodes/match/review/decision.json`
- `nodes/match/review/rounds/round_<NNN>/decision.json`
- `nodes/match/review/rounds/round_<NNN>/feedback.json`

## Proposed canonical review input schema

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

Validation requirements:

1. `source_state_hash` is mandatory and must match current `nodes/match/approved/state.json`.
2. One decision item per requirement ID.
3. `review_status == submitted` cannot contain `pending` decisions.
4. `request_regeneration` route must include at least one actionable patch.

## Engineering changes

### A) Contracts (`src/nodes/review_match/contract.py`)

Add:

- `ReviewInputEnvelope`
- `ReviewInputItem`
- `ReviewLifecycle`

Keep existing:

- `ParsedDecision`
- `DecisionEnvelope`

### B) Match node (`src/nodes/match/logic.py`)

1. Continue writing `nodes/match/approved/state.json`.
2. Seed `nodes/match/review/decision_input.json` for each new round.
3. During compatibility phase, optionally render `decision.md` as read-only mirror.

### C) Review node (`src/nodes/review_match/logic.py`)

1. Read `decision_input.json` as primary source.
2. Parse deterministic route from JSON items (no markdown parser path).
3. Keep stale-hash validation logic.
4. Keep feedback generation contract consumed by `match`.

### D) Graph/CLI behavior

No routing changes required in `src/graph.py` and `src/cli/run_prep_match.py`; only review artifact contract changes.

### E) Tests

Add/update tests in:

- `tests/nodes/match/test_match_logic.py`
- `tests/nodes/review_match/test_review_match_logic.py`

Must cover:

1. JSON schema validation errors,
2. stale hash rejection,
3. pending decisions rejection on submit,
4. missing patch rejection for regeneration,
5. route precedence (`reject` > `request_regeneration` > `approve`).

## Rollout strategy

### Phase 1 (compatibility)

- `review_match` accepts JSON as primary, markdown as temporary fallback.
- UI writes JSON only.

### Phase 2 (cutover)

- Remove markdown parser and markdown-input assumptions.
- Keep optional markdown generation only for human-readable audit, not control plane.

## Acceptance criteria

1. End-to-end review can run without markdown editing.
2. Deterministic fail-closed behavior remains unchanged.
3. Regeneration continues to enrich evidence through `patch_evidence`.
4. Round immutability remains append-only (`round_<NNN>`).
5. Review lifecycle timing/state is persisted and observable.
