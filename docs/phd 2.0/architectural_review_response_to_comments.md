# Architectural Review Response (PhD 2.0)

This document responds to the external architecture review comments and defines concrete protocol updates.

Reference baseline:

- `docs/phd 2.0/phd2_reset_decisions_and_protocol.md`

Status legend:

- `Accepted`: incorporated as mandatory design rule.
- `Accepted with constraints`: incorporated with implementation boundary.

## 1) Make `build_application_context` a first-class reviewable node

Status: `Accepted`

Decision:

- `build_application_context` is a mandatory reviewable node, not a hidden internal transform.
- It follows the standard review lifecycle:
  - `nodes/build_application_context/proposed/state.json`
  - `nodes/build_application_context/proposed/view.md`
  - `nodes/build_application_context/review/decision.md`
  - `nodes/build_application_context/review/decision.json`
  - `nodes/build_application_context/approved/state.json`

Gate rule:

- downstream generators (`generate_motivation_letter`, `tailor_cv`, `draft_email`) can only consume `approved/state.json` from this node.

## 2) Define explicit claim admissibility and evidence compatibility rules

Status: `Accepted`

### 2.1 Claim admissibility classes

- `direct`: explicitly supported by compatible evidence.
- `bridging`: partially supported; must include a limitation-safe phrasing strategy.
- `inadmissible`: unsupported, contradictory, or forbidden.

Admissibility checks (deterministic):

1. claim references an existing requirement id.
2. all cited evidence ids exist in approved evidence set.
3. claim does not violate forbidden-claim rules.
4. claim type is valid for available coverage/evidence.

### 2.2 Evidence compatibility (minimum v1)

Compatibility is evaluated by evidence type and requirement domain.

- strongly compatible: direct skill/role/publication match to requirement concept.
- weakly compatible: adjacent evidence requiring bridge language.
- incompatible: evidence unrelated to requirement concept.

Policy:

- `direct` claims require at least one strongly compatible evidence item.
- `bridging` claims may use weak compatibility but must include explicit bridge framing.
- incompatible evidence cannot be used to justify positive coverage.

## 3) Define formal coverage transition rules

Status: `Accepted`

Coverage state space: `none`, `partial`, `full`.

Transition policy from proposal to approved:

- `full -> partial|none` allowed on review downgrade.
- `partial -> full` allowed only if reviewer-approved edits include sufficient compatible evidence.
- `none -> partial` allowed only with explicit reviewer-approved bridge and valid evidence.
- `none -> full` disallowed in the same review round unless a verified new evidence set is present and parser validation passes strict compatibility checks.

Traceability:

- every transition must include `transition_reason` and `evidence_basis` in decision JSON.

## 4) Specify how reviewer notes become machine-usable semantics without guesswork

Status: `Accepted`

Rule:

- free text is never auto-interpreted into policy semantics.
- only explicitly tagged note directives are converted.

Directive format in `decision.md` (v1):

```text
@scope: local|global
@type: factual|strategic|stylistic|structural|process
@target: <req_id|node_field>
@action: keep|edit|drop|regenerate|forbid
@normalized_rule: <explicit reusable rule>
@confidence: <0..1>
```

Parsing behavior:

- tagged directives -> deterministic structured fields.
- untagged notes -> preserved as raw text only.
- missing required directive keys -> validation error, no semantic extraction.

## 5) Add downstream-usage policy for approved claims

Status: `Accepted`

Downstream policy:

1. only claims in approved artifacts (`decision in {approve, approve_with_edits}`) are usable.
2. rejected claims are blocked from all downstream nodes.
3. `request_regeneration` leaves requirement unresolved and blocks dependent claim usage.
4. downstream nodes must cite source claim ids and evidence ids in their own semantic outputs.

Consumption contract:

- all generated artifacts must include `consumed_claim_refs` and `consumed_evidence_refs`.

## 6) Add a conflict model for historical feedback memory

Status: `Accepted`

Conflict classes:

- `direct_contradiction`: two rules prescribe opposite actions.
- `scope_conflict`: local rule conflicts with global default.
- `priority_conflict`: competing rules for same target and stage.
- `temporal_conflict`: superseded guidance with unclear precedence.

Conflict schema fields (minimum):

- `conflict_id`
- `rule_ids`
- `conflict_type`
- `detected_at`
- `status` (`open|resolved|suppressed`)
- `resolution_policy`

Retrieval policy:

- unresolved conflicts are excluded from automatic prompt injection unless a deterministic precedence rule selects one unambiguously.

## 7) Add explicit node failure taxonomy and continuation rules

Status: `Accepted`

Failure taxonomy:

- `INPUT_MISSING`
- `SCHEMA_INVALID`
- `REVIEW_LOCK_MISSING`
- `POLICY_VIOLATION`
- `PARSER_REJECTED`
- `TOOL_FAILURE`
- `MODEL_FAILURE`
- `IO_FAILURE`
- `INTERNAL_ERROR`

Continuation policy:

- fail-stop categories: `SCHEMA_INVALID`, `POLICY_VIOLATION`, `PARSER_REJECTED`.
- retryable categories: `MODEL_FAILURE`, `TOOL_FAILURE`, transient `IO_FAILURE`.
- no implicit downstream continuation after fail-stop.
- retry attempts and final disposition must be logged in node `meta/`.

## 8) Add provenance requirements for every approved artifact

Status: `Accepted`

Each approved artifact must include (inline or in `meta/provenance.json`):

- `artifact_id`
- `node`
- `job_id`
- `run_id`
- `produced_at`
- `contract_version`
- `producer` (tool/node id)
- `inputs`: list of `{path, sha256, role}`
- `review_decision_ref` (if reviewable)
- `code_ref` (git commit)
- `prompt_ref` and `prompt_version` (for LLM nodes)
- `model_ref` (provider/model id, if applicable)

Approval gate:

- artifact is not considered approved if provenance block is missing or hash references cannot be resolved.

## 9) Reframe `sync_json_md` as safety-critical subsystem with adversarial parsing tests

Status: `Accepted with constraints`

Constraint:

- safety-critical regarding integrity/approval gating, not safety-critical in a life-critical regulatory sense.

Design posture:

- treat review markdown as untrusted input.
- parser must fail closed (reject on ambiguity).
- no fuzzy semantic inference.

Required test categories:

1. malformed checkbox variants and ambiguous multi-selection.
2. duplicate ids / missing ids / reordered blocks.
3. unicode confusables and normalization edge cases.
4. markdown injection-like payloads in notes/comments.
5. stale hash replay (`source_state_hash` mismatch).
6. roundtrip integrity (`json -> md -> json` invariant for deterministic fields).
7. large-input bounds and parser timeout behavior.

Operational rule:

- no `review/decision.json` generation on parse warnings; warnings are treated as hard errors in gating mode.

## Consolidated Additions to PhD 2.0 Protocol

The following become mandatory additions to the reset protocol:

1. `build_application_context` is review-gated.
2. deterministic admissibility + compatibility checks before approvals.
3. explicit coverage transition recording.
4. directive-only machine extraction from notes.
5. strict downstream consumption policy for approved claims.
6. feedback conflict registry with deterministic resolution policy.
7. shared node failure taxonomy with continuation matrix.
8. provenance hashes for all approved artifacts.
9. `sync_json_md` hardened with adversarial parser tests and fail-closed behavior.
