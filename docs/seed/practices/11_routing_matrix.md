# Routing Documentation Matrix (PhD 2.0)

Master matrix for AI Context Routing. Maps every document to orthogonal coordinates (domain, stage, nature) with code paths.

---

## Matrix Schema

Each entry contains:

| Field | Type | Description |
|-------|------|-------------|
| `domain` | string | Technical domain (ui, api, pipeline, core, data, policy) |
| `stage` | string | Pipeline stage or "all" for cross-cutting |
| `nature` | string | philosophy, implementation, development, testing, expected_behavior |
| `doc_path` | string | Exact path to Markdown documentation |
| `target_code` | string[] | Glob patterns for source code (e.g., `["src/**/*.py"]`) |
| `keywords` | string[] | Triggers that route queries here |
| `description` | string | What this document contains |
| `not_contains` | string | What NOT to look for here + where to go |

---

## Complete Matrix

| Domain | Stage | Nature | Doc Path | Target Code | Keywords | Description | What It Does NOT Contain |
|--------|-------|--------|----------|-------------|----------|-------------|-------------------------|
| **pipeline** | all | philosophy | `docs/seed/product/04_pipeline_stages_phd2.md` | - | scrape, extract, match, generate, render, package, langgraph, stages, flow | 8-stage pipeline definition with HITL gates | Specific node contracts (→ `core/contracts.md`) |
| **pipeline** | all | implementation | `docs/reference/graph_state_contract.md` | `src/graph.py`, `src/nodes/*/contract.py` | state.json, graph state, LangGraph edges, transitions | Graph state contract: fields in each state.json | HTTP endpoints (→ `api/spec.md`) |
| **pipeline** | scrape | implementation | `docs/seed/product/09_autopostulation_deployment.md` | `src/nodes/scrape/` | scrape, source, capture, html, url | Scrape stage implementation | Translation logic (→ extract) |
| **pipeline** | extract | implementation | `docs/seed/product/09_autopostulation_deployment.md` | `src/nodes/extract/` | extract, spans, text, requirements, tagging | Extract stage with Text Tagger | Match logic (→ match) |
| **pipeline** | match | implementation | `docs/seed/product/09_autopostulation_deployment.md` | `src/nodes/match/` | match, evidence, alignment, links, graph | Match stage with evidence linking | Delta generation (→ strategy) |
| **pipeline** | strategy | implementation | `docs/seed/product/08_document_delta.md` | `src/nodes/strategy/` | strategy, delta, motivations, narrative | Strategy stage with document_delta.json | Document drafting (→ drafting) |
| **pipeline** | drafting | implementation | `docs/seed/product/09_autopostulation_deployment.md` | `src/nodes/drafting/` | drafting, documents, markdown, templates | Drafting stage with Markdown output | Rendering (→ render) |
| **pipeline** | render | implementation | `docs/seed/product/09_autopostulation_deployment.md` | `src/core/render/` | render, pdf, latex, docx, conversion | Render stage with PDF generation | Packaging (→ package) |
| **pipeline** | package | implementation | `docs/seed/product/09_autopostulation_deployment.md` | `src/core/package/` | package, zip, email, submission | Package stage for deployment | - |
| **ui** | all | implementation | `docs/seed/product/10_ui_dev_integration_map.md` | `apps/review-workbench/src/` | react, components, views, hitl, tagger, editor, match canvas | React component specs for all stages | Backend logic (→ `pipeline`) |
| **ui** | all | development | `docs/seed/product/02_system_architecture.md` | `apps/review-workbench/src/` | ui, frontend, workbench, react | UI architecture overview | API contracts (→ `api`) |
| **api** | all | implementation | `docs/api/spec.md` | `src/interfaces/api/` | endpoints, http, get, post, put, patch, fastapi, bridge | FastAPI endpoints and contracts | Pipeline logic (→ `pipeline`) |
| **api** | all | development | `docs/seed/product/10_ui_dev_integration_map.md` | `src/interfaces/api/` | api, models, pydantic, request, response | API development guide | UI rendering (→ `ui`) |
| **core** | all | implementation | `docs/core/README.md` | `src/core/` | scraping, pdf, render, io, deterministic, functions | Core deterministic functions | LLM prompts (→ `pipeline`) |
| **core** | all | implementation | `docs/core/contracts.md` | `src/nodes/*/contract.py` | contract.py, schema, validation, input, output | Node input/output contracts | Execution logic (→ `pipeline`) |
| **data** | all | implementation | `docs/seed/product/canonical_path_registry.md` | - | data/jobs, local-first, files, folders, persistence | **Canonical path registry** | HTTP endpoints (→ `api`) |
| **data** | all | implementation | `docs/seed/product/05_data_architecture.md` | - | data structure, json schemas, folders | Data folder structure and conventions | API endpoints (→ `api`) |
| **data** | all | philosophy | `docs/seed/product/07_evidence_tree_feedback_loop.md` | - | evidence_bank, profile.json, cv profile, skills, augment | Evidence tree philosophy | Stage-specific review (→ `pipeline`) |
| **data** | all | implementation | `docs/seed/product/06_review_node_schema.md` | - | review_node, correction, augmentation, style, rejection | Generic ReviewNode schema | Specific gate (→ `pipeline`) |
| **policy** | all | philosophy | `docs/seed/product/03_methodology.md` | - | determinism, decoupling, cli > api > ui, progressive | PhD 2.0 philosophy | Implementation details (→ `core`) |
| **policy** | all | philosophy | `docs/seed/product/implementation_status.md` | - | implemented, partial, planned, blocked, gaps | **Implementation status tracker** | - |
| **practices** | all | development | `docs/seed/practices/planning_template_ui.md` | - | planning, template, spec, feature, ui | **UI planning template** | - |
| **practices** | all | development | `docs/seed/practices/12_context_router_protocol.md` | `src/tools/context_router.py` | router, context, fetch, orthogonal, mcp | **Context router protocol** | - |
| **practices** | all | development | `docs/seed/practices/13_agent_intervention_templates.md` | - | agent, workflow, sync, implement, design, hotfix | **Agent intervention templates** | - |

---

## JSON Schema (for machine parsing)

```json
{
  "matrix": [
    {
      "domain": "string",
      "stage": "string",
      "nature": "string",
      "doc_path": "string",
      "target_code": ["pattern1", "pattern2"],
      "keywords": ["keyword1", "keyword2"],
      "description": "string",
      "not_contains": "string"
    }
  ]
}
```

---

## Quick Lookups

### By Domain

| Domain | Key Docs |
|--------|----------|
| ui | `10_ui_dev_integration_map.md`, `02_system_architecture.md` |
| api | `docs/api/spec.md`, `10_ui_dev_integration_map.md` |
| pipeline | `04_pipeline_stages_phd2.md`, `canonical_path_registry.md` |
| core | `docs/core/README.md`, `docs/core/contracts.md` |
| data | `canonical_path_registry.md`, `05_data_architecture.md`, `06_review_node_schema.md` |
| policy | `03_methodology.md`, `implementation_status.md` |
| practices | `planners/planning_template*.md`, `12_context_router_protocol.md` |

### By Stage

| Stage | Doc | Target Code |
|-------|-----|-------------|
| scrape | `04_pipeline_stages_phd2.md` | `src/nodes/scrape/` |
| extract | `04_pipeline_stages_phd2.md` | `src/nodes/extract/` |
| match | `04_pipeline_stages_phd2.md` | `src/nodes/match/` |
| strategy | `04_pipeline_stages_phd2.md` | `src/nodes/strategy/` |
| drafting | `04_pipeline_stages_phd2.md` | `src/nodes/drafting/` |
| render | `04_pipeline_stages_phd2.md` | `src/core/render/` |
| package | `04_pipeline_stages_phd2.md` | `src/core/package/` |

---

## Cross-Domain Links

- `ui` → `data` (ReviewNode schema for UI components)
- `api` → `data` (what files each endpoint exposes)
- `pipeline` → `data` (state.json contracts)
- `core` → `data` (canonical paths)
