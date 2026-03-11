# Graph State Contract (Control-Plane Ledger)

Related references:

- `docs/templates/node_template_discipline.md`
- `docs/architecture/core_io_and_provenance_manager.md`
- `docs/architecture/graph_reactivity_protocol.md`
- `docs/graph/nodes_summary.md`

## Purpose

Define GraphState as the control-plane single source of truth for execution and routing.

GraphState is a ledger of run identity, progress, gate status, and error context.
It is not a container for heavy business payloads.

## Non-negotiable boundary

1. GraphState stores control metadata and lightweight artifact pointers.
2. Node payloads (`ExtractEnvelope`, `MatchEnvelope`, `RedactEnvelope`, etc.) remain in Data Plane artifacts.
3. Resume/retry logic depends on GraphState + checkpoint store, not embedded payload copies.

## Canonical shape

Implementation path:

- `src/core/graph/state.py`
- `src/graph.py`

Reference shape:

```python
class GraphState(TypedDict):
    source: str
    job_id: str
    run_id: str

    current_node: str
    status: Literal["running", "pending_review", "failed", "completed"]

    review_decision: NotRequired[Literal["approve", "request_regeneration", "reject"] | None]
    pending_gate: NotRequired[str | None]

    ingested_data: NotRequired[dict[str, Any]]
    extracted_data: NotRequired[dict[str, Any]]
    matched_data: NotRequired[dict[str, Any]]
    my_profile_evidence: NotRequired[list[dict[str, Any]]]

    error_state: NotRequired[ErrorContext | None]
    artifact_refs: NotRequired[ArtifactRefs]
```

`artifact_refs` stores pointers such as:

- `last_proposed_state_ref`
- `last_decision_ref`
- `emergent_evidence_patch_ref`
- `active_feedback_ref`

## Why this is auditable and resilient

1. Lazy recovery: if one node fails, prior approved artifacts remain intact on disk.
2. Replayability: checkpoints remain small and deterministic.
3. HITL clarity: pending gate and latest decision pointer are explicit.
4. Traceability: payload evolution is visible in artifact history, not hidden inside graph memory blobs.

## Node pattern example (`extract_understand`)

```python
def extract_node(state: GraphState) -> dict:
    ws = WorkspaceManager(state["source"], state["job_id"])
    reader = ArtifactReader(ws)
    writer = ArtifactWriter(ws)

    raw = reader.load_raw_text("source_text.md")
    logic_input = ExtractingInput(job_id=state["job_id"], source_text_md=raw)

    pm = PromptManager(base_path="src/ai/nodes")
    llm = LLMRuntime()
    system_prompt, user_prompt = pm.build_prompt("extract_understand", logic_input)

    result = llm.generate_structured(system_prompt, user_prompt, JobUnderstandingExtract)
    writer.write_proposed_state("extract_understand", result, generate_review_surface=False)
    writer.write_approved_state("extract_understand", result)

    return {
        "current_node": "extract_understand",
        "status": "running",
        "error_state": None,
        "artifact_refs": {
            "last_proposed_state_ref": "nodes/extract_understand/proposed/state.json",
        },
    }
```

## Practical rule

If a field is large, semantic, or reviewable by humans, it belongs in Data Plane artifacts, not in GraphState.

## Bootstrap note (current implementation)

Current bootstrap ingestion nodes may pass a transient `ingested_data` object through state while `src/core/io/` integration is still being completed.

Target steady state remains unchanged:

- ingestion payloads should move to Data Plane artifacts,
- GraphState should keep only pointers in `artifact_refs`.
