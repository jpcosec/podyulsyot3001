# `sync_json_md` Service

Related references:

- `docs/reference/artifact_schemas.md`
- `docs/business_rules/claim_admissibility_and_policy.md`
- `docs/graph/graph_definition.md`

## Purpose

`sync_json_md` is the deterministic service that bridges JSON canonical state and Markdown review surfaces. It is the mechanism that makes human review possible without requiring operators to edit raw JSON.

Location: `src/core/tools/sync_json_md/`

---

## API surface

### `json_to_md(node, state_json_path, view_md_path, decision_md_path)`

Generates the human-readable view and editable decision form from canonical JSON state.

- Reads `proposed/state.json`.
- Writes `proposed/view.md` (read-only review surface).
- Writes `review/decision.md` (editable decision form with checkboxes).
- Embeds `source_state_hash` (SHA-256 of `proposed/state.json`) into generated markdown.

### `md_to_json(node, decision_md_path, decision_json_path, proposed_state_json_path)`

Parses a human-edited decision markdown back into validated JSON.

- Reads `review/decision.md`.
- Validates `source_state_hash` against current `proposed/state.json`.
- Parses decision checkboxes, notes, and tagged directives.
- Writes `review/decision.json` on success.
- Fails closed on any ambiguity or validation error.

### `validate_roundtrip(node, state_json_path, view_md_path)`

Verifies that `json -> md -> json` produces equivalent deterministic fields.

- Used as a development and CI check.
- Ensures no information loss in the sync cycle for machine-critical fields.

---

## Behavior lifecycle

The sync service operates in a strict sequence within the review protocol:

1. **Node writes `proposed/state.json`**: the canonical machine proposal.
2. **`json_to_md` generates review surfaces**: `proposed/view.md` (human-readable) and `review/decision.md` (editable form).
3. **Human edits `review/decision.md`**: typically in Obsidian or any text editor.
4. **`md_to_json` parses and validates**: produces `review/decision.json` or fails with actionable error.
5. **Graph continues only if valid**: the graph runtime checks for a valid `decision.json` before proceeding.

---

## Source state hash and staleness protection

Every generated `review/decision.md` embeds a `source_state_hash` in its YAML front matter:

```yaml
---
source_state_hash: "sha256:abc123..."
node: "match"
job_id: "201397"
round: 1
---
```

### Staleness check

During `md_to_json`, the parser:

1. Reads `source_state_hash` from `decision.md` front matter.
2. Computes SHA-256 of current `proposed/state.json`.
3. If mismatch: **rejects the decision as stale** with an actionable error.

This prevents applying review decisions made against an outdated proposal.

### Recovery

If staleness is detected:

1. Regenerate `review/decision.md` from current `proposed/state.json` using `json_to_md`.
2. Re-apply review decisions manually.
3. Re-run `md_to_json` (or `review-validate` CLI command).

---

## Parser robustness requirements

The parser must handle real-world human editing behavior robustly.

### Checkbox normalization

Real review files contain inconsistent checkbox formatting:

- `[x]`, `[ x]`, `[x ]`, `[ x ]` must all normalize to "checked."
- `[ ]` must normalize to "unchecked."
- Malformed variants like `x[ ]` must be rejected with a line-level error.

### Ambiguity rejection

- Multiple checked decisions in a single block: **reject**.
- Zero checked decisions in a required block: **reject**.
- The parser never guesses intent.

Allowed decisions are exactly:

- `approve`
- `request_regeneration`
- `reject`

### Line-level errors

All validation errors must report:

- The exact line number in `decision.md`.
- The block id where the error occurred.
- A human-readable description of the problem.

---

## Safety-critical posture

`sync_json_md` is safety-critical regarding pipeline integrity and approval gating (not in a life-critical regulatory sense).

### Design posture

- Treat review markdown as **untrusted input**.
- Parser must **fail closed** (reject on ambiguity).
- No fuzzy semantic inference.
- No `review/decision.json` generation on parse warnings; warnings are treated as hard errors in gating mode.

---

## Required adversarial test categories

The parser must be tested against these categories:

1. **Malformed checkbox variants**: inconsistent formatting, ambiguous multi-selection.
2. **Duplicate/missing/reordered ids**: block ids that don't match proposed state.
3. **Unicode confusables**: normalization edge cases (e.g., Unicode checkmarks vs ASCII).
4. **Markdown injection payloads**: notes/comments containing markdown that could confuse the parser.
5. **Stale hash replay**: `source_state_hash` mismatch detection.
6. **Roundtrip integrity**: `json -> md -> json` invariant for deterministic fields.
7. **Large-input bounds**: parser timeout behavior and memory limits.

Each category must have dedicated test cases. No category may be deferred.

---

## Integration points

- **CLI**: `phd2 review-validate` calls `md_to_json` internally.
- **Graph runtime**: checks for valid `review/decision.json` before allowing continuation.
- **Review directives**: tagged directives in `decision.md` (see `docs/business_rules/claim_admissibility_and_policy.md`) are parsed during `md_to_json`.
- **Obsidian workflow**: `decision.md` files are designed for editing in Obsidian (see `docs/operations/tool_interaction_and_known_issues.md`).
