# Claim Admissibility and Policy

Related references:

- `docs/reference/artifact_schemas.md`
- `docs/graph/graph_definition.md`
- `docs/philosophy/structure_and_rationale.md`

## Purpose

This document defines the deterministic rules that govern which claims may enter the pipeline, how evidence supports them, how coverage transitions work during review, and how downstream nodes consume approved claims.

These rules are mandatory. They are checked deterministically before any claim is approved.

---

## Claim admissibility classes

Every proposed claim must be classified into one of three admissibility classes:

### `direct`

Fully supported by compatible evidence.

- At least one strongly compatible evidence item exists.
- No forbidden-claim rules are violated.
- Claim can be used as-is in downstream generation.

### `bridging`

Partially supported; requires limitation-safe phrasing.

- Evidence is weakly compatible (adjacent but not direct).
- Claim must include explicit bridge framing that acknowledges the gap.
- Downstream usage must preserve the bridge language.

### `inadmissible`

Unsupported, contradictory, or forbidden.

- No compatible evidence exists, or
- claim violates a forbidden-claim rule, or
- evidence is incompatible with the requirement concept.
- Inadmissible claims are blocked from all downstream nodes.

---

## Evidence compatibility rules

Compatibility is evaluated by evidence type and requirement domain.

### Strongly compatible

Direct skill, role, publication, or education match to the requirement concept.

- Example: requirement asks for "experience with eye-tracking paradigms" and evidence is a publication on eye-tracking methodology.

### Weakly compatible

Adjacent evidence requiring bridge language.

- Example: requirement asks for "EEG data collection" and evidence is "EEG data processing and analysis" (related but not the same activity).

### Incompatible

Evidence unrelated to the requirement concept.

- Example: requirement asks for "clinical trial design" and evidence is "web application deployment."

### Policy

- `direct` claims require at least one strongly compatible evidence item.
- `bridging` claims may use weak compatibility but must include explicit bridge framing.
- Incompatible evidence cannot be used to justify positive coverage.

---

## Admissibility checks (deterministic)

Before any claim is approved, these checks must pass:

1. Claim references an existing requirement id.
2. All cited evidence ids exist in the approved evidence set.
3. Claim does not violate forbidden-claim rules.
4. Claim type is valid for available coverage/evidence:
   - `direct` requires strongly compatible evidence.
   - `bridging` requires at least weakly compatible evidence.
   - `inadmissible` claims are rejected outright.

These checks are deterministic and do not involve LLM judgment.

---

## Coverage transition rules

Coverage state space: `none`, `partial`, `full`.

### Transition policy (proposal to approved)

- `full -> partial` or `full -> none`: allowed on review downgrade.
- `partial -> full`: allowed only after regeneration produces sufficient compatible evidence and review decision is `approve`.
- `none -> partial`: allowed only after regeneration produces explicit bridge framing with valid evidence and review decision is `approve`.
- `none -> full`: disallowed in the same review round unless a verified new evidence set is present and parser validation passes strict compatibility checks.

### Traceability

Every coverage transition must include:

- `transition_reason`: why coverage changed.
- `evidence_basis`: which evidence items justify the new level.

These fields are required in `review/decision.json`.

---

## Downstream claim consumption policy

### Rules

1. Only claims in approved artifacts (decision = `approve`) are usable downstream.
2. Rejected claims are blocked from all downstream nodes.
3. `request_regeneration` leaves the requirement unresolved and blocks dependent claim usage until the regeneration cycle completes.
4. Downstream nodes must cite source claim ids and evidence ids in their own semantic outputs.

### Consumption contract

All generated artifacts must include:

- `consumed_claim_refs`: list of claim ids consumed from upstream approved state.
- `consumed_evidence_refs`: list of evidence ids referenced.

This ensures full traceability from final output back to source evidence.

---

## Review directive format

Review directives allow reviewer notes in `decision.md` to become machine-usable semantics without guesswork.

### Rule

- Free text is never auto-interpreted into policy semantics.
- Only explicitly tagged note directives are converted to structured fields.

### Directive format (v1)

In `review/decision.md`, tagged directives use this format:

```text
@scope: local|global
@type: factual|strategic|stylistic|structural|process
@target: <req_id|node_field>
@action: keep|edit|drop|regenerate|forbid
@normalized_rule: <explicit reusable rule>
@confidence: <0..1>
```

### Parsing behavior

- Tagged directives are converted to deterministic structured fields in `decision.json`.
- Untagged notes are preserved as raw text only (no semantic extraction).
- Missing required directive keys result in a validation error; no partial semantic extraction.

### Example

```text
Notes:
The candidate should not claim direct data collection experience.
@scope: global
@type: factual
@target: R4
@action: forbid
@normalized_rule: Do not claim hands-on EEG data collection unless explicitly verified in profile.
@confidence: 0.99
```

In this example, the first line is raw text (preserved but not parsed). The tagged block becomes a structured directive in `decision.json`.

---

## Integration with pipeline

- Admissibility checks run at `review_match` and `review_application_context`.
- Coverage transitions are recorded in `review/decision.json` at every review node.
- Downstream consumption refs are required in `nodes/build_application_context/proposed/state.json` and all generation node outputs.
- Review directives are parsed by `sync_json_md` during the `md_to_json` step.
