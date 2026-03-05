# Smart Template Discipline

Related references:

- `docs/philosophy/template_problem_statement.md`
- `docs/philosophy/execution_taxonomy_abstract.md`
- `docs/templates/taxonomy_template_catalog.md`
- `docs/philosophy/structure_and_rationale.md`
- `docs/graph/graph_definition.md`
- `docs/architecture/core_io_and_provenance_manager.md`

## Purpose

This document defines the strict implementation discipline for all pipeline nodes in PhD 2.0.

By enforcing one GraphState contract, one error-routing pattern, and one package shape, we reduce style drift and block wax-model behaviors (especially silent fallback-to-success).

## 1) GraphState contract (Control Plane)

LangGraph state must carry only control metadata and routing signals. Heavy payloads stay on disk in the Data Plane.

Canonical GraphState:

```python
from typing import TypedDict, Literal, Optional


class ErrorContext(TypedDict):
    failure_type: Literal[
        "MODEL_FAILURE",
        "TOOL_FAILURE",
        "IO_FAILURE",
        "INPUT_MISSING",
        "SCHEMA_INVALID",
        "POLICY_VIOLATION",
        "PARSER_REJECTED",
        "REVIEW_LOCK_MISSING",
        "INTERNAL_ERROR",
    ]
    message: str
    attempt_count: int


class GraphState(TypedDict):
    # Identity
    source: str
    job_id: str
    run_id: str

    # Progress tracking (control signals only)
    current_node: str
    status: Literal["running", "pending_review", "failed", "completed"]

    # Routing signal set by review nodes
    review_decision: Optional[Literal["approve", "request_regeneration", "reject"]]

    # Retry context
    error_state: Optional[ErrorContext]
```

Hard rule:

- Nodes must never place semantic payloads (for example `profile_data`, `cv_text`, `html_content`) in GraphState.

## 2) Error handling and retry pattern

The runtime uses two error classes:

## Fail-stop errors

Examples:

- `SCHEMA_INVALID`
- `POLICY_VIOLATION`
- `PARSER_REJECTED`

Node behavior:

- raise typed exceptions immediately.

Graph behavior:

- no retry loop; run fails loudly for operator inspection.

## Retryable errors

Examples:

- `MODEL_FAILURE`
- `TOOL_FAILURE`
- transient `IO_FAILURE`

Node behavior:

- catch expected retryable exception,
- increment `error_state.attempt_count`,
- write retry log entry to node metadata,
- return updated `error_state`.

Graph behavior:

- conditional edge `should_retry` loops to same node while attempts are below configured max,
- on max exceeded, escalate to fail-stop exception.

Anti-wax rule:

- no retry handler may return a fake success payload.

## 3) Base node template structure

Every node follows this package shape:

```text
src/<domain>/nodes/<node_name>/
  contract.py    # input/output schemas
  logic.py       # pure business logic (no file I/O)
  node.py        # LangGraph entrypoint: read -> logic -> write -> route
  prompt/        # LLM nodes only
    system.md
```

`<domain>` is:

- `ai` for LLM nodes,
- `core` for non-LLM nodes.

Node-local `reader.py` and `writer.py` are intentionally removed. I/O is centralized in `src/core/io/`.

## Standard `node.py` orchestration

```python
from core.io import WorkspaceManager, ArtifactReader, ArtifactWriter
from .logic import run_logic


def my_node(state: GraphState) -> dict:
    workspace = WorkspaceManager(state["source"], state["job_id"])
    reader = ArtifactReader(workspace)
    writer = ArtifactWriter(workspace)

    context = reader.load_approved_state("review_application_context", AppContextSchema)

    try:
        proposal = run_logic(context)
        writer.write_proposed_state("my_node", proposal, generate_review_surface=True)
        return {
            "current_node": "my_node",
            "status": "pending_review",
            "error_state": None,
        }
    except ModelParsingError as exc:
        attempt = (state.get("error_state") or {}).get("attempt_count", 0) + 1
        return {
            "error_state": {
                "failure_type": "MODEL_FAILURE",
                "message": str(exc),
                "attempt_count": attempt,
            }
        }
```

## 4) Prompt locality (LLM nodes)

Rules:

1. prompts are node-local (`src/ai/nodes/<node_name>/prompt/`),
2. no global prompt folder coupling,
3. `logic.py` loads prompt assets relative to its own module path,
4. provenance records `prompt_ref` and `prompt_version`.

## 5) Taxonomy-to-template mapping

All nodes share the base shape, but behavior and routing depend on taxonomy leaf.

## 5.1 Non-LLM deterministic (`NLLM-D`)

Goal:

- predictable and reproducible transformations.

Examples:

- `ingest`, `render`, `package`.

Pattern:

- no `prompt/`, no external network dependency,
- read/write canonical artifacts,
- direct routing to next node.

## 5.2 Non-LLM bounded-nondeterministic (`NLLM-ND`)

Goal:

- handle bounded variability from external services.

Examples:

- `scraping`, `translate`.

Pattern:

- no `prompt/`, strict timeout and retry policies,
- explicit `TOOL_FAILURE` routing behavior,
- direct routing on success.

## 5.3 LLM extracting

Goal:

- distill or consolidate into validated structured state.

Examples:

- `application_context_builder`, `feedback_distiller`.

Pattern:

- JSON-first output,
- usually no review surface generation,
- direct routing unless matrix marks explicit review gate.

## 5.4 LLM matching

Goal:

- map evidence to requirements and propose claims.

Examples:

- `match`.

Pattern:

- logic returns structured JSON only,
- writer persists JSON and deterministically generates review markdown via `sync_json_md`,
- route to `pending_review`.

## 5.5 LLM redacting

Goal:

- draft narrative content intended for human review and later delivery.

Examples:

- `motivation_letter_writer`, `cv_tailorer`, `email_drafter`.

Pattern:

- logic returns both structured state and native markdown draft,
- writer persists both and generates decision surface,
- route to `pending_review`.

## 5.6 Reviewing parser nodes (non-LLM gatekeepers)

Goal:

- parse human decisions, enforce policy, and promote validated artifacts.

Examples:

- `review_match`, `review_motivation_letter`, `review_cv`, `review_email`.

Pattern:

1. call `sync_json_md.md_to_json()` for deterministic parsing,
2. fail-stop on stale hash or parse ambiguity (`PARSER_REJECTED`),
3. on `approve`, write approved artifact and provenance,
4. return `review_decision` routing signal.

Note:

- LLM "reviewing" task type (prompt-level summarization/interpretation) is not allowed to replace deterministic gate parsing.

## 6) HITL interrupt contract

The review loop is intentionally asynchronous:

1. proposing node writes artifacts and returns `status: "pending_review"`,
2. graph checkpoint is persisted,
3. operator edits `review/decision.md` and runs validation,
4. operator resumes graph,
5. corresponding review node parses decision and emits routing signal.

This contract is mandatory for all review-gated flows.

## 7) Macro-node (subgraph) discipline

To keep top-level orchestration clear, related node states should be grouped as LangGraph subgraphs.

Required macro-nodes:

1. `prep_subgraph`: `ingest -> extract_understand -> translate`
2. `match_cycle_subgraph`: `match -> review_match` (+ regeneration loop)
3. `context_cycle_subgraph`: `build_application_context -> review_application_context` (+ regeneration loop)
4. `motivation_cycle_subgraph`: `generate_motivation_letter -> review_motivation_letter` (+ regeneration loop)
5. `cv_cycle_subgraph`: `tailor_cv -> review_cv` (+ regeneration loop)
6. `email_cycle_subgraph`: `draft_email -> review_email` (+ regeneration loop)
7. `delivery_subgraph`: `render -> package`

Subgraph rules:

- internal nodes keep full audit semantics (no hidden combined logic),
- subgraph input/output through GraphState control fields only,
- payload data remains in Data Plane artifacts,
- review decisions are consumed inside the corresponding cycle subgraph,
- unresolved `error_state` must not leak silently across macro-node boundaries.

`prep_subgraph` note:

- this phase is not review-gated; it is a preprocessing macro-node where `translate` can be `NLLM-ND` with bounded retry semantics.
