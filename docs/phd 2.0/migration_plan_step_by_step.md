# PhD 2.0 Migration Plan (Step-by-Step)

This is the execution plan to migrate from the current codebase to the PhD 2.0 architecture.

Design sources:

- `docs/phd 2.0/phd2_reset_decisions_and_protocol.md`
- `docs/phd 2.0/architectural_review_response_to_comments.md`

Scope assumptions:

- new branch rebuild
- preserve only legacy `raw/` job artifacts
- prompts live inside each LLM node
- `translate` stage is mandatory after extraction
- review protocol + `sync_json_md` are first-class

---

## Phase 0 — Freeze and Branch

Goal: create a safe migration baseline.

Steps:

1. Tag current repository state (pre-PhD2 reset).
2. Create new branch (example: `phd2-rebuild`).
3. Add migration tracker doc with checklist and decision log.

Deliverables:

- git tag for pre-migration recovery
- new branch
- migration tracker markdown

Exit criteria:

- branch exists and is the active development branch
- rollback path verified (tag can be checked out)

---

## Phase 1 — New Skeleton and Import Boundaries

Goal: establish target structure and stop architecture drift.

Steps:

1. Create top-level modules:
   - `src/ai/`
   - `src/core/`
   - `src/interfaces/`
2. Add package readme files defining allowed responsibilities.
3. Add boundary checks (lint/simple CI script) to prevent forbidden imports:
   - `core` must not import `ai`
   - `interfaces` can import both
4. Add baseline runtime config module in `src/core/io/`.

Deliverables:

- new folder structure with import policy docs
- basic boundary check script

Exit criteria:

- all new modules import cleanly
- boundary checks pass

---

## Phase 2 — Graph-Aligned Data Layout + Artifact Store

Goal: make data layout mirror graph nodes.

Steps:

1. Implement `ArtifactStore` in `src/core/io/` with canonical paths:
   - `data/jobs/<source>/<job_id>/nodes/<node>/input|proposed|review|approved|meta`
   - `data/jobs/<source>/<job_id>/runtime/checkpoints`
   - `data/jobs/<source>/<job_id>/final`
2. Implement helper APIs:
   - `read_json`, `write_json`, `read_md`, `write_md`
   - `compute_sha256`
   - `list_node_artifacts`
3. Add migration helper to import legacy `raw/` only.

Deliverables:

- deterministic artifact store module
- raw import utility

Exit criteria:

- can create/read/write canonical node paths for a sample job
- legacy import copies only `raw/*`

---

## Phase 3 — Shared Contracts and Failure Taxonomy

Goal: lock strict machine contracts before implementing nodes.

Steps:

1. Add shared contracts in `src/core/contracts/`:
   - `NodeInput`, `NodeOutput`, `NodeResult`
   - `ReviewDecision`
   - `ProvenanceRecord`
   - `FailureRecord`
2. Add claim/evidence contracts:
   - admissibility class (`direct|bridging|inadmissible`)
   - compatibility class (`strong|weak|incompatible`)
3. Add coverage transition contract with mandatory reason fields.
4. Add failure taxonomy enum and continuation matrix.

Deliverables:

- typed schemas with validation

Exit criteria:

- schema validation tests pass for happy + invalid examples

---

## Phase 4 — `sync_json_md` Safety-Critical Subsystem

Goal: deterministic, fail-closed review bridge.

Steps:

1. Implement `src/core/tools/sync_json_md/`:
   - `json_to_md`
   - `md_to_json`
   - `validate_roundtrip`
2. Implement `source_state_hash` embedding + stale replay protection.
3. Implement strict directive extraction format for reusable semantics.
4. Implement parser diagnostics with line-level errors.
5. Add adversarial test set:
   - malformed checkboxes
   - ambiguous decisions
   - unicode confusables
   - duplicate/missing ids
   - stale hash replay
   - markdown injection-like content

Deliverables:

- working sync service
- adversarial parser test suite

Exit criteria:

- parser fails closed on ambiguity
- roundtrip invariant holds for deterministic fields

---

## Phase 5 — Provenance and Approval Gate

Goal: no approved artifact without reproducible lineage.

Steps:

1. Implement provenance writer in `src/core/io/provenance.py`.
2. Required fields for every approved artifact:
   - input refs + sha256 hashes
   - contract version
   - producer node id
   - code ref (git sha)
   - prompt/model refs for LLM nodes
3. Add approval gate validator that blocks missing/invalid provenance.

Deliverables:

- `meta/provenance.json` support across nodes
- approval gate validator

Exit criteria:

- gate fails when provenance is absent or hash mismatch exists

---

## Phase 6 — Core Deterministic Tools Migration

Goal: preserve deterministic value, re-homed into `src/core`.

Steps:

1. Move/refactor deterministic modules into `src/core/tools/`:
   - scraping helpers
   - extraction/parsing helpers
   - rendering + packaging
   - ATS deterministic evaluator
2. Add translation tool in `src/core/tools/translation/`.
3. Define deterministic tool API signatures so AI nodes can call them.

Deliverables:

- reusable deterministic tool layer

Exit criteria:

- tool smoke tests pass (minimal, focused)

---

## Phase 7 — Node Template Scaffolding (All Nodes)

Goal: enforce uniform node writing style.

Steps:

1. Add node template generator script (optional) or copy baseline package.
2. Scaffold all canonical nodes with identical shape:
   - `contract.py`, `reader.py`, `logic.py`, `writer.py`, `node.py`
   - `review.py` for reviewable nodes
3. Reviewable nodes include both proposed/review/approved flow.

Deliverables:

- all node packages exist with standard structure

Exit criteria:

- no node deviates from required package layout

---

## Phase 8 — AI Node Prompt Locality

Goal: every LLM node owns its own prompts.

Steps:

1. For each LLM node create `prompt/` subfolder:
   - `system.md`
   - `user_template.md`
   - `schema.json`
   - `fewshots.jsonl`
   - `meta.yaml`
2. Remove runtime dependencies on global prompt paths.
3. Implement prompt loader that resolves prompt assets from node package only.

Deliverables:

- prompt-local LLM nodes

Exit criteria:

- node execution succeeds without shared global runtime prompts

---

## Phase 9 — Implement First End-to-End Slice

Goal: prove architecture with minimal vertical flow.

Slice:

- `ingest -> extract_understand -> translate -> match -> review_match`

Steps:

1. Implement deterministic nodes for ingest/extract/translate.
2. Implement LLM `match` node with local prompts and machine contract output.
3. Implement review gate using `sync_json_md` + decision validation.
4. Ensure reviewed output writes approved state + provenance.

Deliverables:

- first end-to-end review-gated subgraph

Exit criteria:

- can run slice on one real job with manual review in Obsidian

---

## Phase 10 — Implement Context + Writing Nodes

Goal: complete core semantic generation chain.

Steps:

1. Implement `build_application_context` as reviewable first-class node.
2. Implement `generate_motivation_letter` + `review_motivation_letter`.
3. Implement `tailor_cv` and `draft_email` with downstream-usage policy enforcement.
4. Enforce only approved claim consumption in these nodes.

Deliverables:

- complete semantic generation chain with review locks

Exit criteria:

- all downstream nodes reject unresolved/rejected claims

---

## Phase 11 — Render, Package, and Final Outputs

Goal: reattach deterministic delivery tail.

Steps:

1. Implement/port `render` node consuming approved content artifacts.
2. Implement/port `package` node for final outputs.
3. Write `final/manifest.json` referencing produced files + provenance.

Deliverables:

- `final/` outputs from PhD 2.0 pipeline

Exit criteria:

- complete run produces CV, motivation PDF, and final package

---

## Phase 12 — Historical Feedback Memory with Conflict Model

Goal: make feedback reusable safely.

Steps:

1. Implement feedback event writer per reviewable node.
2. Implement active memory store and retrieval filters.
3. Implement conflict registry:
   - conflict detection
   - resolution policy
   - unresolved conflict handling in retrieval

Deliverables:

- `feedback/events/*`
- `feedback/active_memory.yaml`
- `feedback/conflicts.*`

Exit criteria:

- retrieval excludes unresolved ambiguous conflicts by default

---

## Phase 13 — LangGraph Runtime Rebuild

Goal: compile PhD 2.0 nodes into graph runtime with strict gating.

Steps:

1. Build graph in `src/ai/graph/` from new node packages.
2. Add interruption points at all reviewable nodes.
3. Store checkpoints under `runtime/checkpoints/`.
4. Implement `graph-status` from new state model.

Deliverables:

- PhD 2.0 runtime graph orchestration

Exit criteria:

- pause/resume works for every review gate

---

## Phase 14 — Interfaces (CLI + Obsidian workflow)

Goal: clean operator UX for day-to-day use.

Steps:

1. Implement commands in `src/interfaces/cli/`:
   - run, resume, graph-status
   - review-validate
   - node-run (targeted)
2. Add deterministic helper to open/locate review markdown files.
3. Optional: generate per-node `view.html` for richer visual review.

Deliverables:

- operator-ready CLI for PhD 2.0

Exit criteria:

- reviewer can complete full cycle using markdown review files only

---

## Phase 15 — Verification, Hardening, and Cutover

Goal: production readiness for PhD 2.0 branch.

Steps:

1. Run tool smoke tests + parser adversarial suite + graph smoke runs.
2. Run at least 2 real job dry-runs using preserved `raw/` artifacts.
3. Compare outputs and policy compliance against protocol.
4. Freeze migration report and cut release tag.

Deliverables:

- migration report
- release tag for PhD 2.0 baseline

Exit criteria:

- all mandatory gates pass
- documented runbook is complete

---

## Commit Strategy (Recommended)

One commit per phase (or subphase), in strict order:

1. scaffold/boundaries
2. artifact store
3. contracts/failures
4. sync_json_md
5. provenance
6. deterministic tools
7. node templates
8. prompt locality
9. first vertical slice
10. context + writing nodes
11. render/package
12. feedback conflict model
13. graph runtime
14. interfaces
15. hardening/cutover

---

## Risks and Mitigations

1. Contract drift between nodes
   - mitigation: schema version checks + CI validation.
2. Parser ambiguity in review markdown
   - mitigation: fail-closed parser + adversarial tests.
3. Legacy behavior leakage
   - mitigation: rebuild-only policy, selective git recovery by contract.
4. Prompt/version mismatch
   - mitigation: node-local `meta.yaml` and prompt-contract checks.
5. Incomplete provenance
   - mitigation: approval gate blocks missing hashes.
