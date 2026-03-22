# Backend / Pipeline Planning Template

Template for creating feature specs for backend nodes, API endpoints, or pipeline modifications. For UI specs, use `planning_template_ui.md`.

---

## Template

```markdown
# Plan: <Feature Name>

**Type:** backend | api | pipeline | core
**Domain:** [ui | api | pipeline | core | data]
**Stage:** [scrape | translate | extract | match | strategy | drafting | render | package | cross-cutting]
**Priority:** [critical | high | medium | low]
**Status:** draft | review | approved

---

## 1. Problem Statement

What problem does this solve? Why is it needed?

---

## 2. State Contract (LangGraph)

### Current State (what exists)

```json
// state.json before this feature
{
  // existing fields
}
```

### Required State Changes

```json
// state.json after this feature
{
  // existing fields
  // + new fields required
}
```

### Field Mapping

| Field | Type | Source | Target | Notes |
|-------|------|--------|--------|-------|
| `field_name` | string | node_a | node_b | Description |

---

## 3. Core Functions (Deterministic)

What functions in `src/core/` does this affect?

| Function | Module | Changes Needed |
|----------|--------|----------------|
| `function_name` | `src/core/module.py` | new / modified / none |

---

## 4. Node Implementation (LangGraph)

### Affected Nodes

| Node Name | File | Changes |
|-----------|------|---------|
| `node_name` | `src/nodes/stage/node.py` | new / modified |

### Node Contract

```python
# contract.py for this node
@dataclass
class NodeInput:
    # required inputs
    pass

@dataclass  
class NodeOutput:
    # guaranteed outputs
    pass
```

### Edge Transitions

```
[previous_node] → [this_node] → [next_node]

Conditions for transition:
- [condition 1]
- [condition 2]
```

---

## 5. HITL Requirements

Does this feature require human intervention?

| Gate | Required | Schema | UI Component |
|------|----------|--------|--------------|
| yes/no | yes/no | ReviewNode / Decision | component_name |

### If HITL Required

```json
// Required ReviewNode schema
{
  "etapa": "<stage>",
  "tipo": "CORRECTION | AUGMENTATION | STYLE | REJECTION",
  "index": "...",
  "comentario": "...",
  "valor_anterior": null,
  "valor_nuevo": {}
}
```

---

## 6. API Endpoints (if applicable)

| Method | Endpoint | Request | Response | Notes |
|--------|----------|---------|----------|-------|
| GET | `/api/...` | Schema | Schema | - |
| PUT | `/api/...` | Schema | Schema | - |

---

## 7. File Changes Summary

| Action | Path | Description |
|--------|------|-------------|
| CREATE | `src/nodes/stage/node.py` | New node |
| MODIFY | `src/graph.py` | Add edge |
| CREATE | `src/nodes/stage/contract.py` | Contract definition |
| MODIFY | `docs/runtime/stage.md` | Document new behavior |

---

## 8. Dependencies

| Dependency | Blocker? | Notes |
|------------|----------|-------|
| Other feature X | yes/no | - |

---

## 9. Testing Strategy

| Test Type | Location | What to Test |
|-----------|----------|--------------|
| Unit | `tests/unit/` | Function behavior |
| Integration | `tests/integration/` | Node transitions |
| Contract | `tests/contracts/` | state.json schema |

---

## 10. Rollback Plan

How to revert if this breaks production?

1. [Step 1]
2. [Step 2]
3. [Step 3]
```

---

## Field Guide

| Field | Required | Description |
|-------|----------|-------------|
| Type | Yes | backend (LangGraph), api (FastAPI), pipeline (edges), core (deterministic) |
| Domain | Yes | Which technical domain this belongs to |
| Stage | Yes | Pipeline stage or "cross-cutting" |
| State Contract | Yes | How state.json changes |
| Core Functions | If applicable | Which deterministic functions are affected |
| Node Implementation | If applicable | LangGraph node details |
| HITL | No | Whether this requires human review gate |
| API Endpoints | If applicable | FastAPI router changes |
| File Changes | Yes | Complete list of files to create/modify |
| Dependencies | Yes | What blocks this |
| Testing | Yes | How to verify |
| Rollback | Yes | How to undo |

---

## Example: Strategy Delta Node

```markdown
# Plan: Strategy Delta Node

**Type:** backend
**Domain:** pipeline
**Stage:** strategy
**Priority:** high
**Status:** draft

---

## 1. Problem Statement

Currently, the pipeline jumps from Match to Drafting without collecting user motivations. The Strategy stage should pause for user input on narrative points.

---

## 2. State Contract

### Current State (Match output)
```json
{
  "matched_requirements": [...],
  "evidence_links": [...]
}
```

### Required State (Strategy output)
```json
{
  "matched_requirements": [...],
  "evidence_links": [...],
  "strategy": {
    "motivations": [...],
    "delta": {
      "master_doc_id": "...",
      "puntos_narrativos": [...],
      "modificaciones": [...]
    }
  }
}
```

---

## 3. Core Functions

| Function | Module | Changes Needed |
|----------|--------|----------------|
| None | - | - |

---

## 4. Node Implementation

### Affected Nodes

| Node Name | File | Changes |
|-----------|------|---------|
| `build_application_context` | `src/nodes/strategy/build_context.py` | NEW |
| `review_application_context` | `src/nodes/strategy/review_context.py` | NEW |

### Edge Transitions

```
match → build_application_context → review_application_context → drafting

Conditions:
- build_application_context: Always (after match)
- review_application_context: Only if HITL required
- drafting: After review (or skip if no HITL)
```

---

## 5. HITL Requirements

| Gate | Required | Schema | UI Component |
|------|----------|--------|--------------|
| yes | yes | ReviewNode tipo=STYLE | StrategyForm |

---

## 7. File Changes Summary

| Action | Path |
|--------|------|
| CREATE | `src/nodes/strategy/__init__.py` |
| CREATE | `src/nodes/strategy/build_context.py` |
| CREATE | `src/nodes/strategy/review_context.py` |
| CREATE | `src/nodes/strategy/contract.py` |
| MODIFY | `src/graph.py` |

---

## 9. Rollback Plan

1. Disable `PREP_MATCH_LINEAR_EDGES` in `src/graph.py`
2. Revert edge to direct `match → drafting`
```
