# Graph Reactivity Protocol (Emergent Evidence vs Feedback Memory)

> Status note (2026-03-20): this protocol is mostly target-state. Current runtime does support run-scoped regeneration feedback and `PATCH_EVIDENCE:` extraction through `review_match`, but it does not implement the full `sync_json_md`, `feedback_distill`, or `feedback/active_memory.yaml` protocol described below.


Related references:

- `docs/runtime/graph_flow.md`
- `plan/runtime/sync_json_md.md`
- `docs/policy/feedback_memory.md`
- `docs/reference/matching_contract_case_matrix_and_escape_hatch.md`

## Purpose

This protocol defines how the graph reacts to two different review outcomes that are often confused:

1. missing present-case data (emergent evidence),
2. wrong evaluation criteria (feedback memory).

The distinction is critical for correctness and auditability.

## 1) Problem statement

During `match` review, operators may report two different failure classes:

- **Missing data**: the candidate evidence is real but absent from current structured inputs.
- **Wrong criteria**: the evidence exists, but the model's interpretation is poor.

These failures must not share the same reactivity channel.

## 2) Reactivity channels

| Reactivity Type | Markdown action (`review/decision.md`) | Data destination | Graph effect |
| --- | --- | --- | --- |
| Emergent Evidence | Fill explicit "Emergent Evidence" block | Run-scoped evidence set for current job (via patch artifact and input assembly) | Immediate: force regeneration of `match` |
| Feedback Memory | Add criterion notes/directives in review notes | `feedback/active_memory.yaml` (after distillation) | Deferred: affects future executions |

Important boundary:

- emergent evidence corrects data for the current run,
- feedback memory adjusts evaluation behavior over time.

## 3) Execution protocol

### A) Emergent evidence injection (present-case correction)

When operator fills the emergent-evidence section in review markdown:

1. `sync_json_md.md_to_json(...)` parses the block into normalized evidence entries.
2. Parser persists a patch artifact under review metadata (recommended: `nodes/review_match/meta/emergent_evidence_patch.json`).
3. Review routing is forced to `{"review_decision": "request_regeneration"}`.
4. On regeneration, `match` input assembly merges approved profile evidence + emergent evidence patch.
5. UI/audit should label these entries as `emergent` so operators can see they were not in original profile base.

Fail-closed rules:

- malformed emergent evidence block -> parser rejection,
- empty or invalid evidence ids -> parser rejection,
- no silent fallback to standard regeneration without patch visibility.

### B) Feedback distillation (future-case improvement)

When operator notes indicate interpretation quality problems:

1. Deterministic parser captures notes/directives in `decision.json`.
2. `feedback_distill` analyzes accepted review outcomes asynchronously.
3. Distilled `FeedbackRule` entries are written to `feedback/active_memory.yaml`.
4. Future `match` and `redact` inputs load these rules as `active_feedback`.

No immediate data mutation rule:

- feedback distillation must not mutate current approved source artifacts.

## 4) Control Plane / Data Plane binding

To preserve graph-state discipline:

- graph state carries reactivity signals only (for example `request_regeneration` and patch references),
- payload data remains in Data Plane artifacts,
- input builders materialize merged runtime inputs from approved artifacts + patch artifacts.

This keeps checkpoints small and replayable while allowing immediate corrective regeneration.

## 5) Audit guarantees

This protocol guarantees:

1. operators can fix present-case omissions without rewriting history,
2. future behavior improves through explicit feedback memory,
3. current-run correction and long-term learning remain traceable and separable,
4. no hidden mixing of data correction and policy correction.
