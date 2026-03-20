# PhD 2.0 Reset — Decisions and Protocol

This document captures the decisions agreed in the PhD 2.0 reset discussion.
It is the implementation baseline for the new branch.

## 1) Non-Negotiable Decisions

1. Prioritize `docs/phd 2.0/` as the canonical design source.
2. Implement a real review protocol as first-class pipeline behavior.
3. Split codebase into two major domains:
   - LLM/LangGraph side
   - deterministic code side
4. Start clean on a new branch and rebuild from contracts.
5. Preserve from prior job outputs only `raw/` artifacts.
6. Insert a `translate` stage immediately after extraction.
7. Keep prompts local to each LLM node (no global runtime prompt bucket).
8. JSON remains canonical machine state; Markdown is the human review UI.
9. Add `sync_json_md` service for deterministic JSON<->Markdown synchronization.

## 2) Canonical Pipeline (PhD 2.0)

Ordered stages:

1. `ingest`
2. `extract_understand`
3. `translate`
4. `match`
5. `review_match`
6. `build_application_context`
7. `generate_motivation_letter`
8. `review_motivation_letter`
9. `tailor_cv`
10. `draft_email`
11. `render`
12. `package`
13. `feedback_distill` (optional async/follow-up)

## 3) Source Tree Split

Target top-level structure:

```text
src/
  ai/            # LangGraph orchestration + LLM nodes + prompt wiring
  core/          # deterministic contracts, tools, validators, io
  interfaces/    # CLI/API entrypoints
```

### 3.1 `src/ai` intent

- Graph definitions, runtime policies, LLM adapters.
- Node packages for LLM stages only.
- Prompt files colocated with each node.

### 3.2 `src/core` intent

- Deterministic tools used by agents and non-agent stages.
- Contracts, artifact store, validation, parsing, rendering, packaging.
- Includes review parsing and JSON/Markdown sync utilities.

## 4) Uniform Node Writing Style (Mandatory)

Every node must follow the same internal structure. Avoid node-specific ad-hoc layouts.

```text
<domain>/nodes/<node_name>/
  __init__.py
  contract.py      # input/output schemas
  reader.py        # upstream artifact reads
  logic.py         # transformation logic
  writer.py        # deterministic artifact writes
  node.py          # run(context) entrypoint
  review.py        # only for reviewable nodes
```

Standard function shape:

- `read_inputs(job_ctx) -> NodeInput`
- `execute(node_input, runtime_ctx) -> NodeOutput`
- `write_outputs(job_ctx, node_output) -> PersistedRefs`
- `run(job_ctx, runtime_ctx) -> NodeResult`

## 5) Prompt Locality Rule

For every LLM node, prompts are local to that node package:

```text
src/ai/nodes/<node_name>/prompt/
  system.md
  user_template.md
  schema.json
  fewshots.jsonl
  meta.yaml
```

`meta.yaml` must include at least:

- `prompt_version`
- `contract_version`
- `owner_node`
- `last_updated`

## 6) Review Protocol v1

### 6.1 Canonical rule

- JSON is canonical truth.
- Markdown is review interface.
- No downstream continuation without validated review JSON.

### 6.2 Review artifact lifecycle

For each reviewable node:

- `proposed/state.json`
- `proposed/view.md` (human-readable)
- `review/decision.md` (human-edited)
- `review/decision.json` (parsed + validated)
- `approved/state.json`

### 6.3 Decision vocabulary (strict)

- `approve`
- `approve_with_edits`
- `request_regeneration`
- `reject`

### 6.4 Required decision metadata

- `node`
- `job_id`
- `round`
- `decision`
- `edits`
- `notes`
- `reusable_feedback`
- `updated_at`
- `source_state_hash`

### 6.5 Staleness protection

`source_state_hash` in `review/decision.md` and `review/decision.json` must match the latest `proposed/state.json`.
If mismatch: parser rejects decision as stale.

## 7) `sync_json_md` Service (Deterministic)

New service: `src/core/tools/sync_json_md/`.

Minimum API:

- `json_to_md(node, state_json_path, view_md_path, decision_md_path)`
- `md_to_json(node, decision_md_path, decision_json_path, proposed_state_json_path)`
- `validate_roundtrip(node, state_json_path, view_md_path)`

Behavior:

1. Node writes `proposed/state.json`.
2. `json_to_md` generates `proposed/view.md` and editable `review/decision.md`.
3. Human edits `review/decision.md` in Obsidian.
4. `md_to_json` parses and validates into `review/decision.json`.
5. Graph continues only if valid.

## 8) Obsidian and UI Strategy

Constraint: raw JSON is not practical for direct human review in Obsidian.

Agreed approach:

1. Primary interface: Markdown review files generated from JSON.
2. Optional enhancement: deterministic HTML views per node (`view.html`) from canonical JSON.
3. Potential deterministic service: `obsidian_service` for read/write/query convenience, but review truth remains in validated artifacts.

## 9) Graph-Aligned Data Layout

Target job-level layout:

```text
data/jobs/<source>/<job_id>/
  raw/
  nodes/
    <node_name>/
      input/
      proposed/
      review/
      approved/
      meta/
  runtime/
    checkpoints/
  final/
```

Standard artifact names per node (recommended):

- `proposed/state.json`
- `proposed/view.md`
- `review/decision.md`
- `review/decision.json`
- `approved/state.json`
- `meta/provenance.json`

## 10) Legacy Preservation Rules

1. From `data/pipelined_data/...`: preserve only `raw/`.
2. Do not preserve old test suite wholesale.
3. Keep only minimal deterministic tool smoke tests.
4. Recover legacy code selectively from git by contract fit, not by folder migration.

## 11) Parsing Robustness Note from Real Review Example

Reference file:

- `data/pipelined_data/tu_berlin/201397/planning/match_proposal.round1.md`

Observed decision checkbox variants in the file include inconsistent formatting, e.g.:

- `[x]`
- `[ x]`
- `[x ]`
- `[ x]`
- `x[ ]` (malformed placement)

Implication for `sync_json_md` parser:

- parser must normalize checkbox variants robustly,
- parser must detect and reject ambiguous/multiple active decisions,
- parser must return precise line-level validation errors.

## 12) Immediate Implementation Sequence

1. Create fresh branch for PhD 2.0 rebuild.
2. Scaffold `src/ai`, `src/core`, `src/interfaces`.
3. Implement core contracts + artifact store.
4. Implement `sync_json_md` and review schema validation.
5. Implement ingest -> extract_understand -> translate deterministic chain.
6. Implement first LLM node (`match`) with local prompt folder.
7. Implement review gate using `decision.json` lock.
8. Continue node-by-node migration using the uniform template.
