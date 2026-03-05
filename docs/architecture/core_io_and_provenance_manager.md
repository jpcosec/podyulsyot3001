# Core I/O and Provenance Manager (Data Plane)

Related references:

- `docs/philosophy/structure_and_rationale.md`
- `docs/reference/artifact_schemas.md`
- `docs/business_rules/sync_json_md.md`
- `docs/graph/graph_definition.md`

## Purpose

This document defines the centralized Data Plane for PhD 2.0.

To prevent LangGraph state bloat and preserve strict HITL auditability, the graph memory (Control Plane) must only carry lightweight execution signals. Actual document payloads, semantic state, and review surfaces must live on disk (Data Plane).

The Core I/O layer removes path boilerplate and ensures every node uses consistent read/write/provenance behavior.

## Location

- `src/core/io/`

## Control Plane vs Data Plane

## Control Plane (LangGraph state)

Only transport routing and orchestration fields, for example:

- `source`, `job_id`, `run_id`
- current node id / pending gate
- latest review decision (`approve`, `request_regeneration`, `reject`)
- error class and retry metadata

Do not store full draft bodies, mapping arrays, or long semantic payloads in graph state.

## Data Plane (workspace artifacts)

Store all canonical payload artifacts under:

- `data/jobs/<source>/<job_id>/...`

JSON is canonical state; Markdown is the human-facing surface.

## Module responsibilities

The I/O layer is split into three single-responsibility components:

1. `WorkspaceManager`: path resolution.
2. `ArtifactIO`: safe read/write/validation and review-surface synchronization.
3. `ProvenanceService`: hash-based trace metadata generation.

## 1) WorkspaceManager

Responsibilities:

- enforce canonical workspace layout,
- resolve all node/raw/profile/final paths,
- prevent manual path concatenation elsewhere.

API contract (target):

```python
from pathlib import Path


class WorkspaceManager:
    def __init__(self, source: str, job_id: str):
        self.base_path = Path(f"data/jobs/{source}/{job_id}")

    def get_node_dir(self, node: str, stage: str) -> Path:
        """stage in {'input', 'proposed', 'review', 'approved', 'meta'}"""

    def get_node_file(self, node: str, stage: str, filename: str) -> Path:
        """Convenience helper for files under nodes/<node>/<stage>/"""

    def get_profile_path(self) -> Path:
        """Returns profile/profile_base_data.json"""

    def get_raw_artifact(self, filename: str) -> Path:
        """Returns raw/<filename>"""

    def get_final_artifact(self, filename: str) -> Path:
        """Returns final/<filename>"""
```

Enforcement rule:

- no module outside `WorkspaceManager` may construct canonical paths using string concatenation.

## 2) ArtifactIO

`ArtifactIO` is split into read and write interfaces.

## ArtifactReader

Responsibilities:

- load canonical artifacts,
- validate schema at the boundary,
- fail closed on missing/malformed input.

API contract (target):

```python
from pydantic import BaseModel
from typing import Type


class ArtifactReader:
    def __init__(self, workspace: WorkspaceManager):
        self.workspace = workspace

    def load_approved_state(self, node: str, schema_class: Type[BaseModel]) -> BaseModel:
        """
        Loads nodes/<node>/approved/state.json.
        Raises INPUT_MISSING or SCHEMA_INVALID.
        """

    def load_proposed_state(self, node: str, schema_class: Type[BaseModel]) -> BaseModel:
        """Loads nodes/<node>/proposed/state.json with schema validation."""

    def load_review_decision_json(self, node: str, schema_class: Type[BaseModel]) -> BaseModel:
        """Loads nodes/<node>/review/decision.json with schema validation."""

    def load_profile(self, schema_class: Type[BaseModel] | None = None):
        """Loads canonical profile knowledge base."""
```

## ArtifactWriter

Responsibilities:

- persist canonical proposed/approved artifacts,
- generate review surfaces through `sync_json_md` for reviewable nodes,
- avoid duplicated per-node write boilerplate.

API contract (target):

```python
from pydantic import BaseModel


class ArtifactWriter:
    def __init__(self, workspace: WorkspaceManager):
        self.workspace = workspace

    def write_proposed_state(
        self,
        node: str,
        state: BaseModel,
        generate_review_surface: bool = True,
    ) -> None:
        """
        1. Writes nodes/<node>/proposed/state.json.
        2. If generate_review_surface is True, calls sync_json_md.json_to_md(...)
           to generate proposed/view.md and review/decision.md with source_state_hash.
        """

    def write_approved_state(self, node: str, state: BaseModel) -> None:
        """Writes nodes/<node>/approved/state.json."""

    def write_markdown(self, node: str, stage: str, filename: str, content: str) -> None:
        """Writes markdown artifact to canonical node path."""
```

Note:

- In this architecture, review nodes own approved artifacts (for example `nodes/review_motivation_letter/approved/state.json`).

## 3) ProvenanceService

Responsibilities:

- generate `meta/provenance.json` for approved artifacts,
- hash input dependencies (SHA-256),
- record code/model/prompt references when applicable.

API contract (target):

```python
class ProvenanceService:
    def __init__(self, workspace: WorkspaceManager):
        self.workspace = workspace

    def generate_provenance(
        self,
        node: str,
        run_id: str,
        input_paths: list[str],
        llm_context: dict | None = None,
    ) -> None:
        """
        1. Hashes files in input_paths (sha256).
        2. Resolves code_ref (git commit hash when available).
        3. Builds provenance payload per architecture schema.
        4. Writes nodes/<node>/meta/provenance.json.
        """
```

`llm_context` is optional and used only for LLM nodes (for example `model_ref`, `prompt_ref`, `prompt_version`).

## Node orchestration examples

## Example A: generator node

```python
def motivation_letter_node(graph_state: GraphState) -> dict:
    workspace = WorkspaceManager(graph_state.source, graph_state.job_id)
    reader = ArtifactReader(workspace)
    writer = ArtifactWriter(workspace)

    # 1. READ (Data Plane)
    context = reader.load_approved_state("review_application_context", AppContextSchema)
    profile = reader.load_profile(ProfileSchema)

    # 2. LOGIC (LLM or deterministic behavior)
    draft_state = logic.generate_draft(context, profile)

    # 3. WRITE (Data Plane)
    writer.write_proposed_state("generate_motivation_letter", draft_state, generate_review_surface=True)

    # 4. ROUTE (Control Plane)
    return {"current_status": "pending_review", "pending_node": "review_motivation_letter"}
```

## Example B: review node

```python
def review_motivation_letter_node(graph_state: GraphState) -> dict:
    workspace = WorkspaceManager(graph_state.source, graph_state.job_id)
    reader = ArtifactReader(workspace)
    writer = ArtifactWriter(workspace)
    provenance = ProvenanceService(workspace)

    decision = reader.load_review_decision_json("generate_motivation_letter", ReviewDecisionSchema)

    if decision.final == "approve":
        validated_state = logic.build_validated_review_state(decision)
        writer.write_approved_state("review_motivation_letter", validated_state)
        provenance.generate_provenance(
            node="review_motivation_letter",
            run_id=graph_state.run_id,
            input_paths=[
                str(workspace.get_node_file("generate_motivation_letter", "proposed", "state.json")),
                str(workspace.get_profile_path()),
            ],
            llm_context=None,
        )
        return {"review_decision": "approve"}

    if decision.final == "request_regeneration":
        return {"review_decision": "request_regeneration"}

    return {"review_decision": "reject"}
```

## Error model (mandatory)

`ArtifactReader` and `ArtifactWriter` must raise explicit typed errors aligned with failure taxonomy:

- `INPUT_MISSING`
- `SCHEMA_INVALID`
- `PARSER_REJECTED`
- `IO_FAILURE`

They must never return generic empty payloads.

## Architectural rules enforced by this module

1. **No manual path construction** outside `WorkspaceManager`.
2. **Fail-closed reads** in `ArtifactReader`.
3. **No independent provenance hashing** outside `ProvenanceService`.
4. **Strict isolation**: `src/core/io/` must not import from `src/ai/`.
5. **Review surface generation** flows through `sync_json_md`, not ad-hoc markdown builders.

## Why this is the first implementation dependency

Template discipline for nodes depends on this Data Plane being stable.

Without it:

- node templates cannot enforce consistent I/O boundaries,
- LangGraph state risks carrying payload data,
- review/provenance behavior diverges across nodes.

For this reason, `src/core/io/` is a prerequisite before implementing smart node templates.
