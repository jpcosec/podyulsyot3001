# Taxonomy Template Catalog

Related references:

- `docs/philosophy/execution_taxonomy_abstract.md`
- `docs/templates/node_template_discipline.md`
- `docs/architecture/core_io_and_provenance_manager.md`
- `docs/reference/contract_composition_framework.md`

## Purpose

This document provides implementation-ready templates for each taxonomy leaf.

Use it after classifying a step by taxonomy and before assigning it to a concrete node/subgraph.

Scope note:

- Non-LLM templates in this document are implementation-ready now.
- LLM templates are orchestration-level skeletons. Detailed LLM logic contracts and prompt composition are intentionally deferred to the future ad-hoc LLM structure.

## Shared base contract (all templates)

All templates assume:

- Graph state is control-plane only.
- Data payloads are read/written through `src/core/io/`.
- `logic.py` is pure behavior (no file I/O).
- `node.py` orchestrates `read -> logic -> write -> route`.
- `contract.py` uses envelope + primitive composition.

Base package shape:

```text
src/<domain>/nodes/<node_name>/
  __init__.py
  contract.py
  logic.py
  node.py
  prompt/        # LLM templates only
    system.md
```

## 1) Template: Non-LLM deterministic (`NLLM-D`)

Use when output must be reproducible under fixed inputs.

Examples: deterministic transforms, parser gates, render/package finalization.

```python
# node.py
from core.io import WorkspaceManager, ArtifactReader, ArtifactWriter, ProvenanceService
from .contract import InputSchema, OutputSchema
from .logic import run_logic


def node_fn(state: GraphState) -> dict:
    ws = WorkspaceManager(state["source"], state["job_id"])
    reader = ArtifactReader(ws)
    writer = ArtifactWriter(ws)
    prov = ProvenanceService(ws)

    data = reader.load_approved_state("upstream_node", InputSchema)
    result = run_logic(data)
    writer.write_proposed_state("<node_name>", OutputSchema.model_validate(result), generate_review_surface=False)
    writer.write_approved_state("<node_name>", OutputSchema.model_validate(result))
    prov.generate_provenance(node="<node_name>", run_id=state["run_id"], input_paths=["..."])

    return {"current_node": "<node_name>", "status": "running", "error_state": None}
```

## 2) Template: Non-LLM bounded-nondeterministic (`NLLM-ND`)

Use when there is external variability but no LLM dependency.

Examples: scraping, external translation backend.

```python
# node.py
from core.io import WorkspaceManager, ArtifactReader, ArtifactWriter
from .contract import InputSchema, OutputSchema
from .logic import run_logic, ExternalToolError
from core.tools.errors import ToolFailureError

MAX_RETRIES = 2

def node_fn(state: GraphState) -> dict:
    ws = WorkspaceManager(state["source"], state["job_id"])
    reader = ArtifactReader(ws)
    writer = ArtifactWriter(ws)

    data = reader.load_approved_state("upstream_node", InputSchema)

    try:
        result = run_logic(data)
        writer.write_proposed_state("<node_name>", OutputSchema.model_validate(result), generate_review_surface=False)
        writer.write_approved_state("<node_name>", OutputSchema.model_validate(result))
        return {"current_node": "<node_name>", "status": "running", "error_state": None}
    except ExternalToolError as exc:
        attempt = (state.get("error_state") or {}).get("attempt_count", 0) + 1
        if attempt >= MAX_RETRIES:
            raise ToolFailureError("bounded retry limit exceeded") from exc
        return {
            "error_state": {
                "failure_type": "TOOL_FAILURE",
                "message": str(exc),
                "attempt_count": attempt,
            }
        }
    except Exception:
        # unknown failures are fail-stop; never mask them as retryable success.
        raise
```

## 3) Template: LLM extracting

Use when LLM output is structured state distillation (no narrative draft as primary artifact).

Examples: context consolidation, feedback distillation.

```python
# node.py
from core.io import WorkspaceManager, ArtifactReader, ArtifactWriter
from .contract import InputSchema, OutputSchema
from .logic import run_logic, ModelParsingError 


def node_fn(state: GraphState) -> dict:
    ws = WorkspaceManager(state["source"], state["job_id"])
    reader = ArtifactReader(ws)
    writer = ArtifactWriter(ws)

    data = reader.load_approved_state("upstream_node", InputSchema)

    try:
        structured = run_logic(data)
        writer.write_proposed_state("<node_name>", OutputSchema.model_validate(structured), generate_review_surface=False)
        return {"current_node": "<node_name>", "status": "running", "error_state": None}
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

Notes:

- This section defines orchestration shape only.
- Prompt and logic internals are intentionally deferred to the LLM ad-hoc design phase.

## 4) Template: LLM matching

Use when LLM maps requirements to evidence and proposes claims.

Primary behavior: write structured JSON, then deterministic review surfaces via `sync_json_md`.

```python
# node.py
from core.io import WorkspaceManager, ArtifactReader, ArtifactWriter
from .contract import MatchInput, MatchOutput
from .logic import run_logic, ModelParsingError

def node_fn(state: GraphState) -> dict:
    ws = WorkspaceManager(state["source"], state["job_id"])
    reader = ArtifactReader(ws)
    writer = ArtifactWriter(ws)

    data = reader.load_approved_state("translate", MatchInput)

    try:
        proposal = run_logic(data)
        writer.write_proposed_state("match", MatchOutput.model_validate(proposal), generate_review_surface=True)
        return {"current_node": "match", "status": "pending_review", "error_state": None}
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

Notes:

- This template differs from other LLM templates by output contract: JSON proposal plus deterministic review-surface generation.
- Deep prompt/claim strategy is out of scope here and will be defined in the LLM-specific design phase.

## 5) Template: LLM redacting

Use when LLM drafts narrative markdown plus structured state for review.

Examples: motivation letter, CV draft, email draft.

```python
# node.py
from core.io import WorkspaceManager, ArtifactReader, ArtifactWriter
from .contract import InputSchema, StateSchema
from .logic import run_logic, ModelParsingError


def node_fn(state: GraphState) -> dict:
    ws = WorkspaceManager(state["source"], state["job_id"])
    reader = ArtifactReader(ws)
    writer = ArtifactWriter(ws)

    data = reader.load_approved_state("upstream_node", InputSchema)

    try:
        result = run_logic(data)  # expected: {"state": ..., "markdown": ..., "filename": ...}
        writer.write_proposed_state("<node_name>", StateSchema.model_validate(result["state"]), generate_review_surface=True)
        writer.write_markdown("<node_name>", "proposed", result["filename"], result["markdown"])
        return {"current_node": "<node_name>", "status": "pending_review", "error_state": None}
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

Notes:

- This template differs by dual output contract: structured state + markdown draft.
- Narrative style and rhetorical controls are intentionally deferred to node-specific LLM logic design.

## 6) Template: LLM reviewing (assistance, non-gating)

Use only for review assistance outputs (summaries, feedback distillation, analysis helpers).

It must not be used as approval gate authority.

```python
# node.py
from core.io import WorkspaceManager, ArtifactReader, ArtifactWriter
from .contract import InputSchema, OutputSchema
from .logic import run_logic, ModelParsingError


def node_fn(state: GraphState) -> dict:
    ws = WorkspaceManager(state["source"], state["job_id"])
    reader = ArtifactReader(ws)
    writer = ArtifactWriter(ws)

    data = reader.load_proposed_state("upstream_node", InputSchema)
    reviewed_md = reader.load_review_markdown("upstream_node", "decision.md")

    try:
        analysis = run_logic(data=data, reviewed_markdown=reviewed_md)
        writer.write_proposed_state("<node_name>", OutputSchema.model_validate(analysis), generate_review_surface=False)
        return {"current_node": "<node_name>", "status": "running", "error_state": None}
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

Notes:

- The "reviewing" aspect here is analysis of reviewed artifacts.
- It does not parse or authorize approval decisions.
- Deterministic review-gate parser nodes remain the only approval authority.

## Quick difference table for LLM templates

| LLM Category | Primary Output | Review Surface Generated | Gate Authority |
| --- | --- | --- | --- |
| `extracting` | JSON state | Usually no | No |
| `matching` | JSON mapping proposal | Yes | No |
| `redacting` | JSON state + markdown draft | Yes | No |
| `reviewing` (assistance) | JSON analysis/feedback | No | No |

All approval authority is handled by deterministic review-gate parser nodes.

## Mandatory complement: deterministic review gate parser template

Even with an LLM `reviewing` category, approval gates are deterministic non-LLM nodes.

```python
# node.py
from core.io import WorkspaceManager, ArtifactReader, ArtifactWriter, ProvenanceService
from core.tools.sync_json_md import md_to_json


def review_gate_node(state: GraphState) -> dict:
    ws = WorkspaceManager(state["source"], state["job_id"])
    writer = ArtifactWriter(ws)
    prov = ProvenanceService(ws)

    decision = md_to_json(node="<target_node>", decision_md_path="...", decision_json_path="...", proposed_state_json_path="...")

    if decision["final"] == "approve":
        validated = build_validated_state(decision)
        writer.write_approved_state("<review_node>", validated)
        prov.generate_provenance(node="<review_node>", run_id=state["run_id"], input_paths=["..."])
        return {"review_decision": "approve", "status": "running", "error_state": None}

    if decision["final"] == "request_regeneration":
        return {"review_decision": "request_regeneration", "status": "running", "error_state": None}

    return {"review_decision": "reject", "status": "failed", "error_state": None}
```

## Selection checklist

Before implementing a node, answer in order:

1. Does it use LLM? (`yes`/`no`)
2. If non-LLM: deterministic or bounded-nondeterministic?
3. If LLM: extracting, matching, reviewing, or redacting?
4. Is it review-gated?
5. Which template section above applies?
