# Smart Template Discipline

> Status note (2026-03-20): this is now a target-state implementation discipline document, not an exact description of how every node in the repo is currently structured. Some examples and package-shape rules below are ahead of current implementation. Use it as guidance, and cross-check current runtime patterns in `src/nodes/`, `src/core/io/`, and `docs/index/canonical_map.md`.


Related references:

- `docs/philosophy/template_problem_statement.md`
- `docs/philosophy/execution_taxonomy_abstract.md`
- `docs/templates/taxonomy_template_catalog.md`
- `docs/philosophy/structure_and_rationale.md`
- `docs/graph/nodes_summary.md`
- `docs/architecture/core_io_and_provenance_manager.md`
- `docs/reference/contract_composition_framework.md`
- `docs/architecture/graph_state_contract.md`

## Purpose

This document defines the strict implementation discipline for all pipeline nodes in PhD 2.0.

By enforcing one GraphState contract, one error-routing pattern, and one package shape, we reduce style drift and block wax-model behaviors (especially silent fallback-to-success).

## Authority scope

- Canonical owner for node implementation discipline (package shape, orchestration contract, HITL contract).
- Not the canonical owner for taxonomy leaf definitions, failure taxonomy matrix, or graph routing topology.

## 1) GraphState contract (Control Plane)

LangGraph state must carry only control metadata and routing signals. Heavy payloads stay on disk in the Data Plane.

Canonical control-plane ledger reference:

- `docs/architecture/graph_state_contract.md`

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

The canonical failure taxonomy and continuation matrix are defined in:

- `docs/philosophy/structure_and_rationale.md` (Node failure taxonomy)

Template discipline requirement:

1. nodes must classify failures using canonical taxonomy names,
2. fail-stop classes must raise typed exceptions without implicit continuation,
3. retryable classes must use bounded retry with explicit `error_state` updates,
4. retry handlers must never return fake success payloads.

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

`contract.py` composition rule:

- prefer envelope + primitive composition from `docs/reference/contract_composition_framework.md` over bespoke monolithic models.

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

This document does not redefine taxonomy leaves.

Canonical taxonomy source:

- `docs/philosophy/execution_taxonomy_abstract.md`

Canonical per-leaf implementation templates:

- `docs/templates/taxonomy_template_catalog.md`
- `docs/templates/llm/README.md`

Template discipline requirement:

1. classify node intent using the canonical taxonomy first,
2. choose one leaf template from the catalog,
3. implement node package shape and orchestration rules from this document.

## 6) HITL interrupt contract

The review loop is intentionally asynchronous:

1. proposing node writes artifacts and returns `status: "pending_review"`,
2. graph checkpoint is persisted,
3. operator edits `review/decision.md` and runs validation,
4. operator resumes graph,
5. corresponding review node parses decision and emits routing signal.

This contract is mandatory for all review-gated flows.

## 7) Macro-node (subgraph) discipline

This document does not own graph routing topology.

Canonical source for primary flow and macro-node composition:

- `docs/graph/nodes_summary.md`

Template discipline requirement:

- node implementations must be compatible with graph-level routing contracts and review-cycle boundaries defined in the graph doc.
