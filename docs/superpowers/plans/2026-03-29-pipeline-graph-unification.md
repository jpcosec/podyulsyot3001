# Pipeline Graph Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify the pipeline into a single LangGraph graph where `match_skill` is a native compiled subgraph with fully visible topology in Studio — no opaque wrapper nodes, no `Command`-based orphan edges.

**Architecture:** Fix `apply_review_decision` to use `add_conditional_edges` instead of `Command(goto=...)` so Studio can statically render all routing paths. Extend `GraphState` with `requirements` and `profile_evidence` fields so the match_skill subgraph receives inputs through normal state passing. Replace the opaque `make_match_skill_node` wrapper with a directly embedded compiled subgraph.

**Tech Stack:** LangGraph `StateGraph`, LangGraph subgraph embedding, Pydantic `TypedDict`, pytest-asyncio.

---

## File Map

| Action | File | Change |
|--------|------|--------|
| Modify | `src/core/ai/match_skill/graph.py` | Replace `Command`-based routing with `add_conditional_edges`; `apply_review_decision` returns plain dict |
| Modify | `src/core/state.py` | Add `requirements` and `profile_evidence` fields to `GraphState` |
| Modify | `src/graph/nodes/extract_bridge.py` | Return `requirements` and `profile_evidence` in state update |
| Modify | `src/graph/__init__.py` | Embed match_skill as compiled subgraph; remove wrapper import; remove TODO comment |
| Delete | `src/graph/nodes/match_skill.py` | Entire file removed |
| Modify | `tests/test_pipeline_graph.py` | Add assertion that match_skill node is a subgraph |
| Modify | `tests/test_match_skill.py` | Verify routing uses conditional edges (not Command) |
| Modify | `future_docs/issues/pipeline_graph_unification.md` | Mark resolved, move to changelog |
| Modify | `changelog.md` | Record the unification |

---

### Task 1: Fix `apply_review_decision` — `Command` → `add_conditional_edges`

**Files:**
- Modify: `src/core/ai/match_skill/graph.py`

The `apply_review_decision` node currently returns `Command(goto=...)` which LangGraph Studio cannot render as static edges. Replace it with a plain state-returning function and a routing function wired via `add_conditional_edges`.

- [ ] **Step 1.1: Write a failing test that asserts the graph has a visible edge from `apply_review_decision` to `prepare_regeneration_context`**

```python
# In tests/test_match_skill.py — add this test
def test_apply_review_decision_has_conditional_edges():
    """apply_review_decision must route via edges, not Command, so Studio sees topology."""
    from src.core.ai.match_skill.graph import build_match_skill_graph
    from langgraph.checkpoint.memory import InMemorySaver

    app = build_match_skill_graph(checkpointer=InMemorySaver())
    # LangGraph compiled graphs expose edges as a dict of source→list[dest]
    # If routing is via Command, the edge won't appear here
    graph_def = app.graph
    outgoing = {e[0] for e in graph_def.edges}
    # apply_review_decision must have a declared outgoing edge
    assert "apply_review_decision" in outgoing, (
        "apply_review_decision has no declared edges — routing is likely Command-based"
    )
```

Run: `pytest tests/test_match_skill.py::test_apply_review_decision_has_conditional_edges -v`
Expected: FAIL — `apply_review_decision` not in outgoing edges

- [ ] **Step 1.2: Replace `Command` return type with plain dict in `apply_review_decision`**

In `src/core/ai/match_skill/graph.py`, change `_make_apply_review_decision_node`:

```python
def _make_apply_review_decision_node(store: MatchArtifactStore):
    """Create the node that validates and applies a human review payload."""

    def apply_review_decision(state: MatchSkillState) -> MatchSkillState:
        raw_review_payload = state.get("review_payload")
        if not raw_review_payload:
            return {"status": "pending_review"}

        source = _require_non_empty_text(state, "source")
        job_id = _require_non_empty_text(state, "job_id")
        review_payload = ReviewPayload.model_validate(raw_review_payload)
        match_hash = _require_non_empty_text(state, "match_result_hash")
        if review_payload.source_state_hash != match_hash:
            raise ValueError(
                "review payload hash does not match the current match result"
            )

        match_result = MatchEnvelope.model_validate(state.get("match_result"))
        round_number = cast(int, state.get("round_number"))
        feedback_items = _build_feedback_items(review_payload, match_result)
        routing_decision = _route_from_feedback(feedback_items)
        refs = store.write_review_result(
            source=source,
            job_id=job_id,
            round_number=round_number,
            review_payload=review_payload,
            feedback_items=feedback_items,
            routing_decision=routing_decision,
        )
        status = (
            "pending_regeneration"
            if routing_decision == "request_regeneration"
            else "generating_documents"
            if routing_decision == "approve"
            else "completed"
        )
        return {
            "review_decision": routing_decision,
            "active_feedback": [item.model_dump() for item in feedback_items],
            "artifact_refs": {**state.get("artifact_refs", {}), **refs},
            "status": status,
        }

    return apply_review_decision
```

Also remove the `Command` and `Literal` imports that are no longer used in this function (keep `Literal` if used elsewhere in the file — check first).

- [ ] **Step 1.3: Add the routing function and `add_conditional_edges` in `build_match_skill_graph`**

Add this function near the other routing helpers at the bottom of `src/core/ai/match_skill/graph.py`:

```python
def _route_after_apply_review(state: MatchSkillState) -> str:
    """Route based on status set by apply_review_decision."""
    status = state.get("status")
    if status == "pending_review":
        return "human_review_node"
    if status == "pending_regeneration":
        return "prepare_regeneration_context"
    if status == "generating_documents":
        return "generate_documents"
    return "__end__"
```

In `build_match_skill_graph`, replace the direct edge after `apply_review_decision` (there isn't one currently — `Command` was doing the routing) with:

```python
# Remove this if it exists:
# workflow.add_edge("human_review_node", "apply_review_decision")

# Keep this edge (it already exists):
workflow.add_edge("human_review_node", "apply_review_decision")

# Replace Command routing with:
workflow.add_conditional_edges(
    "apply_review_decision",
    _route_after_apply_review,
    {
        "human_review_node": "human_review_node",
        "prepare_regeneration_context": "prepare_regeneration_context",
        "generate_documents": "generate_documents",
        "__end__": "__end__",
    },
)
```

Also remove the `TODO(future)` comment above `apply_review_decision` that was added in the docs commit.

- [ ] **Step 1.4: Run the new test to confirm it passes**

Run: `pytest tests/test_match_skill.py::test_apply_review_decision_has_conditional_edges -v`
Expected: PASS

- [ ] **Step 1.5: Run full test suite to verify nothing broke**

Run: `pytest tests/ -q`
Expected: all existing tests pass

- [ ] **Step 1.6: Commit**

```bash
git add src/core/ai/match_skill/graph.py tests/test_match_skill.py
git commit -m "refactor: replace Command routing with add_conditional_edges in match_skill"
```

---

### Task 2: Extend `GraphState` with match inputs

**Files:**
- Modify: `src/core/state.py`
- Modify: `src/graph/nodes/extract_bridge.py`

The match_skill subgraph requires `requirements` and `profile_evidence` in its input state. These must flow through `GraphState` so LangGraph passes them into the subgraph automatically.

- [ ] **Step 2.1: Write a failing test that verifies extract_bridge puts requirements in state**

```python
# In tests/test_extract_bridge.py — add this test
def test_extract_bridge_returns_requirements_in_state(tmp_path, monkeypatch):
    """extract_bridge must populate requirements in the returned state dict."""
    import json
    from src.core.data_manager import DataManager
    from src.graph.nodes.extract_bridge import make_extract_bridge_node

    # Arrange: write a fake translated state
    dm = DataManager(jobs_root=tmp_path / "jobs", source_root=tmp_path / "source")
    translated = {
        "job_title": "ML Engineer",
        "company_name": "Test Co",
        "requirements": ["Python experience", "ML background"],
        "responsibilities": [],
        "location": "Berlin",
        "employment_type": "full-time",
        "posted_date": "2026-01-01",
    }
    dm.write_json_artifact(
        source="test", job_id="001",
        node_name="translate", stage="proposed",
        filename="state.json", data=translated,
    )
    # Write a minimal profile evidence file
    profile_evidence = [{"id": "EV_001", "description": "5 years Python"}]
    profile_path = tmp_path / "profile_evidence.json"
    profile_path.write_text(json.dumps(profile_evidence))
    monkeypatch.setenv("PROFILE_EVIDENCE_PATH", str(profile_path))

    node = make_extract_bridge_node(dm)
    result = await node({"source": "test", "job_id": "001", "artifact_refs": {}})

    assert "requirements" in result, "requirements must be in state after extract_bridge"
    assert isinstance(result["requirements"], list)
    assert len(result["requirements"]) > 0
    assert "profile_evidence" in result, "profile_evidence must be in state after extract_bridge"
```

Mark test as async:

```python
import pytest

@pytest.mark.asyncio
async def test_extract_bridge_returns_requirements_in_state(tmp_path, monkeypatch):
    ...
```

Run: `pytest tests/test_extract_bridge.py::test_extract_bridge_returns_requirements_in_state -v`
Expected: FAIL — `requirements` not in returned dict

- [ ] **Step 2.2: Add `requirements` and `profile_evidence` to `GraphState`**

In `src/core/state.py`:

```python
class GraphState(TypedDict, total=False):
    """Lightweight control-plane state for the unified schema-v0 pipeline."""

    source: str
    job_id: str
    run_id: str
    current_node: str
    status: RunStatus
    artifact_refs: dict[str, str]
    profile_evidence_ref: str
    requirements: list[dict[str, Any]]          # populated by extract_bridge
    profile_evidence: list[dict[str, Any]]       # populated by extract_bridge
    generated_documents_summary: dict[str, Any]
    render_summary: dict[str, Any]
    error_state: ErrorContext | None
```

- [ ] **Step 2.3: Update `extract_bridge` node to return `requirements` and `profile_evidence` in state**

In `src/graph/nodes/extract_bridge.py`, update `_extract_bridge_node` to also load profile evidence and include both in the returned dict:

```python
import json
import os
from pathlib import Path

async def _extract_bridge_node(state: GraphState, data_manager: DataManager) -> dict:
    source = state["source"]
    job_id = state["job_id"]
    translated_state = data_manager.read_json_artifact(
        source=source,
        job_id=job_id,
        node_name="translate",
        stage="proposed",
        filename="state.json",
    )
    requirements = extract_requirements_from_job_posting(translated_state)
    requirements_dicts = [item.model_dump() for item in requirements]

    state_payload = {
        "source": source,
        "job_id": job_id,
        "requirements": requirements_dicts,
        "job_posting": translated_state,
    }
    refs = dict(state.get("artifact_refs", {}))
    bridge_state = data_manager.write_json_artifact(
        source=source,
        job_id=job_id,
        node_name="extract_bridge",
        stage="proposed",
        filename="state.json",
        data=state_payload,
    )
    refs["bridge_state"] = str(bridge_state)
    try:
        content = data_manager.read_text_artifact(
            source=source,
            job_id=job_id,
            node_name="translate",
            stage="proposed",
            filename="content.md",
        )
        content_ref = data_manager.write_text_artifact(
            source=source,
            job_id=job_id,
            node_name="extract_bridge",
            stage="proposed",
            filename="content.md",
            content=content,
        )
        refs["bridge_content"] = str(content_ref)
    except FileNotFoundError:
        pass

    profile_evidence = _load_profile_evidence(state, data_manager, source, job_id)

    return {
        "artifact_refs": refs,
        "requirements": requirements_dicts,
        "profile_evidence": profile_evidence,
        "current_node": "extract_bridge",
        "status": "running",
    }
```

Add the profile evidence loader helper to `src/graph/nodes/extract_bridge.py`:

```python
def _load_profile_evidence(
    state: GraphState, data_manager: DataManager, source: str, job_id: str
) -> list[dict]:
    """Load profile evidence from state ref, env path, or default location."""
    ref = state.get("profile_evidence_ref")
    if ref:
        return json.loads(Path(ref).read_text(encoding="utf-8"))

    path = os.getenv(
        "PROFILE_EVIDENCE_PATH",
        "data/reference_data/profile/base_profile/profile_base_data.json",
    )
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    evidence = payload.get("evidence", payload)
    ref_path = data_manager.write_json_artifact(
        source=source,
        job_id=job_id,
        node_name="pipeline_inputs",
        stage="proposed",
        filename="profile_evidence.json",
        data=evidence,
    )
    state["profile_evidence_ref"] = str(ref_path)
    return evidence
```

Add imports at the top of `src/graph/nodes/extract_bridge.py`:

```python
import json
import os
from pathlib import Path
```

- [ ] **Step 2.4: Run the new test to confirm it passes**

Run: `pytest tests/test_extract_bridge.py::test_extract_bridge_returns_requirements_in_state -v`
Expected: PASS

- [ ] **Step 2.5: Run full test suite**

Run: `pytest tests/ -q`
Expected: all pass

- [ ] **Step 2.6: Commit**

```bash
git add src/core/state.py src/graph/nodes/extract_bridge.py tests/test_extract_bridge.py
git commit -m "feat: propagate requirements and profile_evidence through GraphState"
```

---

### Task 3: Embed match_skill as native subgraph in pipeline

**Files:**
- Modify: `src/graph/__init__.py`
- Delete: `src/graph/nodes/match_skill.py`

Replace `workflow.add_node("match_skill", make_match_skill_node(manager))` with a compiled subgraph added directly. LangGraph will automatically pass overlapping state keys (`source`, `job_id`, `status`, `artifact_refs`, `requirements`, `profile_evidence`) into the subgraph and merge the subgraph's output back into `GraphState`.

- [ ] **Step 3.1: Write a failing test that asserts match_skill in the pipeline IS a subgraph**

```python
# In tests/test_pipeline_graph.py — add this test
def test_match_skill_is_subgraph():
    """match_skill must be embedded as a compiled subgraph, not an opaque function node."""
    from src.graph import build_pipeline_graph
    from langgraph.pregel import Pregel  # compiled subgraphs are Pregel instances

    app = build_pipeline_graph()
    match_skill_node = app.nodes.get("match_skill")
    assert match_skill_node is not None
    # A subgraph node wraps a Pregel (compiled graph) — check for subgraph marker
    # LangGraph stores the bound function; inspect its __self__ or check graph attribute
    assert hasattr(match_skill_node, "graph") or isinstance(
        getattr(match_skill_node, "bound", None), Pregel
    ), "match_skill must be a subgraph (Pregel), not an opaque function"
```

Run: `pytest tests/test_pipeline_graph.py::test_match_skill_is_subgraph -v`
Expected: FAIL

- [ ] **Step 3.2: Update `build_pipeline_graph` to embed the subgraph**

Replace the content of `src/graph/__init__.py` with:

```python
"""Top-level schema-v0 pipeline graph assembly."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from src.core.ai.match_skill.graph import build_match_skill_graph
from src.core.ai.match_skill.storage import MatchArtifactStore
from src.core.data_manager import DataManager
from src.core.state import GraphState
from src.graph.nodes.extract_bridge import extract_requirements_from_job_posting
from src.graph.nodes.generate_documents import make_generate_documents_node
from src.graph.nodes.package import make_package_node
from src.graph.nodes.render import make_render_node
from src.graph.nodes.scrape import make_scrape_node
from src.graph.nodes.translate import make_translate_node


async def _extract_bridge_node(state: GraphState, data_manager: DataManager) -> dict:
    source = state["source"]
    job_id = state["job_id"]
    translated_state = data_manager.read_json_artifact(
        source=source,
        job_id=job_id,
        node_name="translate",
        stage="proposed",
        filename="state.json",
    )
    requirements = extract_requirements_from_job_posting(translated_state)
    state_payload = {
        "source": source,
        "job_id": job_id,
        "requirements": [item.model_dump() for item in requirements],
        "job_posting": translated_state,
    }
    refs = dict(state.get("artifact_refs", {}))
    bridge_state = data_manager.write_json_artifact(
        source=source,
        job_id=job_id,
        node_name="extract_bridge",
        stage="proposed",
        filename="state.json",
        data=state_payload,
    )
    refs["bridge_state"] = str(bridge_state)
    try:
        content = data_manager.read_text_artifact(
            source=source,
            job_id=job_id,
            node_name="translate",
            stage="proposed",
            filename="content.md",
        )
        content_ref = data_manager.write_text_artifact(
            source=source,
            job_id=job_id,
            node_name="extract_bridge",
            stage="proposed",
            filename="content.md",
            content=content,
        )
        refs["bridge_content"] = str(content_ref)
    except FileNotFoundError:
        pass
    return {
        "artifact_refs": refs,
        "current_node": "extract_bridge",
        "status": "running",
    }


def make_extract_bridge_node(data_manager: DataManager):
    """Create the extract-bridge node adapter for schema-v0."""

    async def extract_bridge_node(state: GraphState) -> dict:
        return await _extract_bridge_node(state, data_manager)

    return extract_bridge_node


def _route_after_match_skill(state: GraphState) -> str:
    if state.get("status") in ("failed", "pending_review"):
        return END
    return "generate_documents"


def _route_after_generate(state: GraphState) -> str:
    if state.get("status") == "failed":
        return END
    return "render"


def _route_after_render(state: GraphState) -> str:
    if state.get("status") == "failed":
        return END
    return "package"


def build_pipeline_graph(*, data_manager: DataManager | None = None) -> Any:
    """Build the schema-v0 top-level pipeline graph."""

    manager = data_manager or DataManager()
    workflow = StateGraph(GraphState)

    match_skill_subgraph = build_match_skill_graph(
        artifact_store=MatchArtifactStore(manager.jobs_root),
        checkpointer=InMemorySaver(),
        interrupt_before=("human_review_node",),
    )

    workflow.add_node("scrape", make_scrape_node(manager))
    workflow.add_node("translate", make_translate_node(manager))
    workflow.add_node("extract_bridge", make_extract_bridge_node(manager))
    workflow.add_node("match_skill", match_skill_subgraph)
    workflow.add_node("generate_documents", make_generate_documents_node(manager))
    workflow.add_node("render", make_render_node(manager))
    workflow.add_node("package", make_package_node(manager))

    workflow.add_edge(START, "scrape")
    workflow.add_edge("scrape", "translate")
    workflow.add_edge("translate", "extract_bridge")
    workflow.add_edge("extract_bridge", "match_skill")
    workflow.add_conditional_edges("match_skill", _route_after_match_skill)
    workflow.add_conditional_edges("generate_documents", _route_after_generate)
    workflow.add_conditional_edges("render", _route_after_render)
    workflow.add_edge("package", END)

    return workflow.compile(checkpointer=InMemorySaver())


def create_studio_graph() -> Any:
    """Create a Studio-friendly compiled graph."""
    return build_pipeline_graph()


__all__ = ["GraphState", "build_pipeline_graph", "create_studio_graph"]
```

Note: `extract_bridge` state propagation of `requirements`/`profile_evidence` was moved to `src/graph/nodes/extract_bridge.py` in Task 2, but the inline `_extract_bridge_node` in `__init__.py` also needs to be updated to match (or kept as-is if Task 2 updated the `make_extract_bridge_node` factory — keep them consistent).

- [ ] **Step 3.3: Delete `src/graph/nodes/match_skill.py`**

```bash
git rm src/graph/nodes/match_skill.py
```

- [ ] **Step 3.4: Run the new test**

Run: `pytest tests/test_pipeline_graph.py::test_match_skill_is_subgraph -v`
Expected: PASS (or adjust assertion based on actual LangGraph subgraph node API)

- [ ] **Step 3.5: Run full test suite**

Run: `pytest tests/ -q`
Expected: all pass

- [ ] **Step 3.6: Commit**

```bash
git add src/graph/__init__.py tests/test_pipeline_graph.py
git commit -m "refactor: embed match_skill as native LangGraph subgraph in pipeline"
```

---

### Task 4: Clean up deferred markers and update docs

**Files:**
- Modify: `src/core/ai/match_skill/graph.py` (remove TODO comment)
- Modify: `src/graph/__init__.py` (remove TODO comment — already done by rewrite)
- Modify: `future_docs/issues/pipeline_graph_unification.md` (mark resolved)
- Modify: `changelog.md`

- [ ] **Step 4.1: Remove the remaining `TODO(future)` comment from `src/core/ai/match_skill/graph.py`**

The comment above `apply_review_decision` was added in the docs commit. It should now be removed since the issue is resolved.

- [ ] **Step 4.2: Update `future_docs/issues/pipeline_graph_unification.md`**

Delete the file — the issue is resolved. The `plan_docs/` entry that drove the work should be noted in changelog instead.

```bash
git rm future_docs/issues/pipeline_graph_unification.md
```

- [ ] **Step 4.3: Update `changelog.md`**

Add entry:

```markdown
## [unreleased]

### Refactored
- Pipeline graph: `match_skill` is now a native LangGraph compiled subgraph — inner topology (load_match_inputs → run_match_llm → persist_match_round → human_review_node → apply_review_decision → …) is fully visible in LangGraph Studio.
- Match skill graph: replaced `Command`-based routing in `apply_review_decision` with `add_conditional_edges` — all routing paths are now statically declared and visible in Studio.
- `GraphState` carries `requirements` and `profile_evidence` populated by `extract_bridge`, enabling clean subgraph state passing without wrapper nodes.
- Removed `src/graph/nodes/match_skill.py` opaque wrapper node.
```

- [ ] **Step 4.4: Run full test suite one final time**

Run: `pytest tests/ -q`
Expected: all pass

- [ ] **Step 4.5: Final commit**

```bash
git add src/core/ai/match_skill/graph.py future_docs/issues/pipeline_graph_unification.md changelog.md
git commit -m "chore: remove resolved TODOs and update changelog for graph unification"
```
