# PhD 2.0 Structure and Rationale

Related references:

- `docs/architecture/graph_definition.md`
- `docs/architecture/execution_taxonomy_abstract.md`
- `docs/overview/project_overview.md`
- `docs/overview/document_glossary.md`

## Why this architecture exists

PhD 2.0 is rebuilt to prevent two failure modes observed in the previous attempt:

1. **Wax-modeling**: code that looks complete but is behaviorally shallow.
2. **Style drift**: node implementations diverging in structure, reliability, and review semantics.

The architecture is intentionally strict so that each node is inspectable, testable, and replaceable without hidden side effects.

## Design goals

1. Make LLM-usage boundaries explicit first, then determinism class inside non-LLM steps.
2. Keep all reviewable state in canonical artifacts (JSON as source of truth).
3. Enforce human approval gates where semantic quality matters.
4. Keep the graph resumable and auditable.
5. Make failures loud and actionable.

## Execution classification model (authoritative)

Classification is two-stage:

1. **LLM usage**: does the step use an LLM? (`yes` / `no`)
2. **Determinism class** (only for `no`): `deterministic` or `bounded_nondeterministic`

Why this model:

- "deterministic vs non-deterministic" alone is not enough for design decisions.
- the operational boundary that matters most is LLM dependency.
- non-LLM steps can still be non-deterministic when they depend on external services.

Example:

- `translate` is **non-LLM** but often **bounded_nondeterministic** (external translation backend).
- `render` is **non-LLM deterministic** under fixed toolchain/template inputs.
- `match` is **LLM** and therefore semantically non-deterministic.

## Layered structure

## `src/core/` (non-LLM domain)

Responsibilities:

- contracts and validators,
- artifact persistence and canonical paths,
- provenance/hashing,
- markdown/json sync for review surfaces,
- non-LLM nodes (`ingest`, `extract_understand`, `translate`, review nodes, `render`, `package`).

Rule:

- `src/core` must never depend on `src/ai`.

Reason:

- correctness and safety-critical gating must not depend on model availability or model behavior.

## `src/ai/` (LLM domain)

Responsibilities:

- shared LLM runtime and schema-aware parsing,
- prompt-local AI nodes,
- graph routing for generation and review interrupts.

Rule:

- AI nodes consume only approved upstream artifacts.

Reason:

- prevents semantic propagation from unreviewed outputs.

## `src/interfaces/` (operator domain)

Responsibilities:

- CLI commands for running, resuming, validating reviews, and inspecting status.

Reason:

- keeps user interaction stable while internal nodes evolve.

## Node package shape (mandatory)

Every node follows a fixed package structure:

- `contract.py`: strict input/output schema.
- `logic.py`: pure node behavior (deterministic or LLM).
- `node.py`: orchestration glue for runtime context.
- `prompt/`: only for LLM nodes (node-local prompt assets).

I/O responsibilities are centralized in `src/core/io/` (WorkspaceManager, ArtifactReader/Writer, ProvenanceService), not per-node reader/writer files.

Reason:

- this separation prevents hidden file I/O in logic, makes behavior testable, and limits regressions.

## Data model and artifact lifecycle

Canonical workspace layout per job:

`data/jobs/<source>/<job_id>/`

- `raw/` imported or scraped source artifacts.
- `nodes/<node>/input/` optional frozen inputs for reproducibility.
- `nodes/<node>/proposed/` machine proposal artifacts.
- `nodes/<node>/review/` human-editable decision artifacts.
- `nodes/<node>/approved/` canonical approved state.
- `nodes/<node>/meta/` provenance and metadata.
- `runtime/checkpoints/` graph resume state.
- `final/` final deliverables.

JSON is canonical. Markdown exists for human review and must roundtrip through the sync tool.

## Review protocol and gating

Reviewable nodes must support decisions:

- `approve`
- `request_regeneration`
- `reject`

Critical controls:

1. source-state hash checks to detect stale decisions,
2. exactly one marked decision per requirement block,
3. deterministic parser behavior (fail closed on ambiguity),
4. explicit graph routing based on reviewed decision.

Reason:

- without strict review semantics, HITL becomes cosmetic and unsafe.

## Provenance policy

Every approved artifact should include provenance metadata with:

- producer node,
- run id,
- code reference,
- hashed input references,
- review decision reference when applicable.

Reason:

- supports auditability, replay diagnostics, and trust boundaries between nodes.

## Acceptance policy by execution class

LLM steps:

- automated checks validate shape/gating/error behavior,
- semantic acceptance is HITL-only on real job data.

Non-LLM deterministic steps:

- require automated tests,
- require reproducibility checks,
- require HITL artifact inspection before closure.

Non-LLM bounded-nondeterministic steps (for example, external translation service):

- require deterministic contract checks around inputs/outputs,
- require tolerance-aware assertions for backend variability,
- require HITL artifact inspection before closure.

Reason:

- this keeps testing strict without pretending external service responses are fully reproducible.

## Style consistency rules

1. Keep functions small and explicit.
2. Avoid generic catch-all comments and hidden mutations.
3. Avoid broad exception swallowing that returns success.
4. Keep business logic out of `node.py` and file I/O out of `logic.py`.
5. Keep imports boundary-safe by design and checks.

Reason:

- style consistency is a reliability feature, not only a readability preference.

## Node failure taxonomy

Every node failure must be classified. The taxonomy determines whether execution can retry or must stop.

### Failure types

| Type | Description |
|------|------------|
| `INPUT_MISSING` | Required upstream artifact does not exist |
| `SCHEMA_INVALID` | Artifact exists but fails contract validation |
| `REVIEW_LOCK_MISSING` | Review decision required but not found |
| `POLICY_VIOLATION` | Admissibility or forbidden-claim rule violated |
| `PARSER_REJECTED` | Review markdown parser rejected input |
| `TOOL_FAILURE` | External tool (scraper, translator, renderer) failed |
| `MODEL_FAILURE` | LLM returned unparseable or invalid output |
| `IO_FAILURE` | File system or network transient error |
| `INTERNAL_ERROR` | Unexpected code-level exception |

### Continuation matrix

Fail-stop (no implicit downstream continuation):

- `SCHEMA_INVALID`
- `POLICY_VIOLATION`
- `PARSER_REJECTED`

Retryable (bounded retry with logging):

- `MODEL_FAILURE`
- `TOOL_FAILURE`
- Transient `IO_FAILURE`

All others require operator intervention before resuming.

### Retry logging

Every retry attempt and final disposition must be logged in the node's `meta/` directory. The log must include:

- failure type,
- attempt number,
- timestamp,
- error detail,
- final outcome (success or escalation).

Reason:

- explicit failure classification prevents silent fallback-to-success and makes debugging reproducible.

## Flow rationale

The graph is intentionally split into stages:

1. source preparation and deterministic normalization,
2. LLM generation with explicit review gates,
3. deterministic render/package delivery.

Reason:

- this split isolates failure domains and keeps semantics reviewable before final delivery.

## Definition of architectural done

Architecture is considered healthy when:

1. all nodes obey package shape and boundary rules,
2. all reviewable nodes enforce strict parse and stale-hash protections,
3. no placeholder logic remains in approved paths,
4. deterministic outputs are reproducible,
5. LLM semantic quality is accepted only through HITL execution.
