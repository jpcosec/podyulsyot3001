# PhD 2.0 Rebuild Index Checklist

> Status note (2026-03-20): this file is a historical execution/status snapshot, not current runtime truth. Several status lines below are outdated after the scraping facade, `src/core/io/`, and `generate_documents -> render -> package` wiring landed. For what actually runs now, use `docs/graph/nodes_summary.md`, `docs/reference/data_management_actual_state.md`, and `docs/operations/tool_interaction_and_known_issues.md`.


This is the execution index for the rebuild. Complete steps in order and do not advance without explicit human approval.

Reference docs:

- `plan/phd2_stepwise_plan.md`
- `plan/step6_13_delta_generation_and_text_reviewers.md`
- `plan/subplan/ui_review_cycle_adaptation_internal.md`
- `plan/subplan/ui_review_cycle_designer_handoff.md`
- `plan/subplan/deterministic_parity_migration_from_phd.md`
- `plan/subplan/review_ui_and_flow_observability.md`
- `plan/subplan/langchain_langgraph_adoption_evaluation.md` (superseded by ADR-001)
- `plan/template/README.md`
- `docs/philosophy/structure_and_rationale.md`
- `docs/operations/tool_interaction_and_known_issues.md`
- `plan/adr/adr_001_ui_first_knowledge_graph_langchain.md`

## Original Step Checklist (status as of 2026-03-16)

- [x] **Pre-Step S - Scraping Recovery**: Scraping service implemented in `src/core/tools/scraping/service.py` with listing crawl, language detection, markdown extraction. Run on 7 TU Berlin jobs with `raw/` artifacts verified. CLI partially integrated via `run_prep_match.py`.
- [x] **Step 0 - Non-Deterministic Runtime Recovery**: `LLMRuntime` (Gemini structured generation + Pydantic validation) and `PromptManager` (Jinja2 + XML-tag validation) implemented in `src/ai/`. Tests pass. No silent fallback paths.
- [x] **Step 1 - Ingest**: `scrape` and `translate_if_needed` nodes implemented with contracts. Approved artifacts written to `nodes/scrape/approved/` and `nodes/translate_if_needed/approved/`. Run on real TU Berlin jobs.
- [x] **Step 2 - Extract_Understand**: LLM-driven extraction node with `JobUnderstandingExtract` contract (requirements, themes, constraints). Prompts standardized to English. Run on real jobs with batch report. Known quality issues: Spanish leakage in `analysis_notes`, flat schema loses structured dates/salary/contact/institution.
- [x] **Step 3 - Translate**: Implemented as `translate_if_needed` node with conditional translation policy based on language detection. Tested and run on real data.
- [x] **Step 4 - Match (LLM)**: Full match node with `MatchEnvelope` contract, round management via `RoundManager`, scoped regeneration, feedback patch injection, `decision.md` rendering with hash-lock front matter. Run on real jobs.
- [x] **Step 5 - Review_Match**: Full deterministic review parser (26 helper functions) with strict `approve`/`request_regeneration`/`reject` routing, stale-hash validation, checkbox parsing, per-round immutable artifacts, `feedback.json` generation. Tested and hardened.
- [x] **Step 6-13 (collapsed) - Generate_Documents**: Implemented as single `generate_documents` node producing `DocumentDeltas` (CV injections + letter deltas + email), deterministic Jinja template rendering, and advisory text-review indicators. Diverges from original per-document plan per `plan/step6_13_delta_generation_and_text_reviewers.md`. Known quality issues: placeholder defaults in letter fields, alignment paragraph duplication, anti-fluff flags not enforced.
- [ ] **Step 6-13 gap - Individual review gates**: `review_application_context`, `review_motivation_letter`, `review_cv`, `review_email` not implemented. `generate_documents` currently flows directly to `package` in prep-match graph.
- [ ] **Step 6-13 gap - core/io layer**: `WorkspaceManager`, `ArtifactReader`, `ArtifactWriter`, `ProvenanceService` specified in `docs/architecture/core_io_and_provenance_manager.md` but not implemented. Nodes do inline path I/O.
- [ ] **Step 6-13 gap - sync_json_md**: JSON/Markdown review surface sync service specified in `docs/business_rules/sync_json_md.md` but not implemented.
- [ ] **Step 14 - Render**: Render tools exist (`src/core/tools/render/docx.py`, `letter.py`, `latex.py` with LaTeX templates) and CLI tools (`src/cli/render_cv.py`, `render_letter.py`), but not wired into graph node.
- [ ] **Step 15 - Package**: `_package_terminal_node` is a stub in `src/graph.py`. No real bundling, manifest, or provenance.

## Architecture Migration (ADR-001)

The remaining gaps above are now superseded by ADR-001, which redefines the architecture as UI-first with Neo4j knowledge graph and full LangChain migration. See `plan/adr/adr_001_ui_first_knowledge_graph_langchain.md`.

New execution phases:

- [~] **Phase 0**: Foundation (Neo4j + FastAPI + React scaffold, data migration) — ~45%. Scaffold done (compose, API routers, React app builds). Data migration to Neo4j not started. pip deps missing.
- [~] **Phase 1**: View 2 — Document-to-Graph (Scraping/Extraction Review) — ~40%. Read-only inspection works (source text + requirement highlighting). Node creation, editing, comments not started.
- [~] **Phase 2**: View 1 — Graph Explorer (Match Review) — ~35%. Read-only graph + match inspection. Mutation, decision UI, comments not started.
- [~] **Phase 3**: View 3 — Graph-to-Document (Generation Review) — ~20%. Display shell only. Slate editing, linking, feedback not started.
- [~] **Phase 4**: Portfolio Dashboard + Navigation — ~25%. Job tree + status badges work. Profile view, filtering, gating not started.
- [ ] **Phase 5**: LangChain Migration + Pipeline Adaptation — 0%.
- [ ] **Phase 6**: Multi-Source Scraping + Scale — 0%.

Detailed per-sub-objective tracking: `plan/adr_001_execution_tracker.md`

## Completion Rule

For every step above, mark complete only when all three are true:

1. deterministic checks for that step pass,
2. HITL run is executed on real job data,
3. human approval is explicitly recorded.
