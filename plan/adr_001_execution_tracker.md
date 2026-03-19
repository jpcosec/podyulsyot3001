# ADR-001 Execution Tracker

Source of truth for ADR-001 implementation progress.
Reference: `plan/adr/adr_001_ui_first_knowledge_graph_langchain.md`
Next actions: `plan/adr_001_next_actions.md`

Status key: `[x]` done, `[~]` partial, `[ ]` not started.

---

## Phase 0: Foundation (Neo4j + FastAPI + React scaffold)

**Objective**: Stand up the full local dev stack (database, API, frontend) and migrate one real dataset into Neo4j.

### Sub-objectives

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 0.1 | Neo4j Docker setup | [~] | `docker-compose.neo4j.yml` exists. Schema constraints defined in `src/interfaces/api/neo4j_schema.py` (17 uniqueness constraints). Not verified running — `neo4j` pip driver not installed in current env. |
| 0.2 | Neo4j schema bootstrap (CLI + API) | [~] | CLI `src/cli/bootstrap_neo4j_schema.py` and API endpoint `POST /api/v1/neo4j/bootstrap-schema` exist. Gracefully handles missing driver. Not end-to-end tested against a live Neo4j instance. |
| 0.3 | FastAPI backend with Neo4j driver + CRUD | [~] | App factory in `src/interfaces/api/app.py` with CORS, 4 routers (health, portfolio, jobs, neo4j). Read-only filesystem endpoints work (5 tests pass). No Neo4j CRUD — all read models are filesystem-based. `fastapi` not installed in current conda env. |
| 0.4 | React app scaffold with routing | [x] | `apps/review-workbench/` — Vite + React 18 + TypeScript. Routes: `/` (Portfolio), `/jobs/:source/:jobId` (Job). Builds clean (`tsc -b && vite build` passes, 51 modules). |
| 0.5 | Graph visualization integration | [x] | `GraphCanvas.tsx` renders nodes/edges via `diagrammatic-ui` (`Graph` component). Used in all three views with active-node styling and tree auto-layout. |
| 0.6 | Slate.js integration | [~] | `RichTextPane.tsx` exists with basic Slate editor instance. Not wired into any view (placeholder only). |
| 0.7 | Import profile data into Neo4j | [ ] | `data/profile/base_profile/profile_base_data.json` exists on disk. No migration script to load it into Neo4j. |
| 0.8 | Import one job artifact chain into Neo4j | [ ] | Job artifacts exist under `data/jobs/tu_berlin/`. No migration script to import into Neo4j nodes/edges. |

**Phase 0 overall: ~45%** — Infrastructure scaffolding done, data migration not started, Neo4j not verified end-to-end.

**Blockers**:
- `fastapi` and `neo4j` pip packages not installed in active environment.
- No data migration scripts exist (profile or job).
- Neo4j uniqueness constraints cover identity but no relationship or property constraints yet.

---

## Phase 1: View 2 — Document to Graph (Scraping/Extraction Review)

**Objective**: Split-pane showing source document alongside extracted graph nodes with bidirectional highlighting, node creation from text selection, property editing, and comment system.

### Sub-objectives

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 1.1 | Split-pane: source document + graph panel | [x] | `ViewTwoDocToGraph.tsx` — left: source lines, right: requirement list + Diagrammatic-UI graph. CSS grid layout in `styles.css`. |
| 1.2 | Bidirectional highlighting (text <-> node) | [~] | Click requirement -> source lines highlight (yellow). Click source line -> linked requirement selects (blue). Spans derived from heuristic text matching (`_derive_spans` in `read_models.py`), NOT from Neo4j `TextSpan` nodes. |
| 1.3 | Text selection to node creation dialog | [ ] | Not implemented. No selection handler, no dialog component. |
| 1.4 | Node property editor | [ ] | Not implemented. Requirements are read-only display. |
| 1.5 | Comment system on nodes | [ ] | Not implemented. No comment model, no UI for adding/viewing comments. |
| 1.6 | Wire to existing scrape/extract pipeline output | [x] | Backend `build_view_two_payload` reads from filesystem `nodes/extract_understand/approved/state.json` and `raw/source_text.md`. API endpoint `GET /{source}/{job_id}/view2` serves it. React client calls it. Test coverage exists (span derivation test passes). |

**Phase 1 overall: ~40%** — Read-only inspection works end-to-end (filesystem -> API -> React). Interactive editing features not started.

**Blockers**:
- Bidirectional highlighting uses heuristic text matching, not `TextSpan` provenance from Neo4j. A migration to Neo4j-backed spans is required before this can be considered ADR-compliant.
- No comment data model exists anywhere (neither Python nor TypeScript).

---

## Phase 2: View 1 — Graph Explorer (Match Review)

**Objective**: Interactive graph showing profile-job-match relationships, edge inspection with scores/reasoning, node/edge editing, review decision UI (approve/regen/reject), comment system.

### Sub-objectives

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 2.1 | Interactive graph visualization | [x] | `ViewOneGraphExplorer.tsx` renders profile, job, and per-requirement nodes with match edges via `GraphCanvas`. |
| 2.2 | Match edge inspection (score, reasoning, evidence) | [x] | Match rows below graph show `source -> target`, score, reasoning text. Edge labels include score. |
| 2.3 | Node/edge editing and deletion | [ ] | Not implemented. Graph is read-only. |
| 2.4 | Review decision interface (approve/regen/reject) | [ ] | Not implemented. No decision buttons, no state mutation endpoint. |
| 2.5 | Comment system on edges | [ ] | Not implemented. |

**Phase 2 overall: ~35%** — Read-only visualization and inspection work. All mutation/interaction features missing.

**Blockers**:
- Requires write endpoints (PATCH/POST) on the API layer, which don't exist.
- Review decision flow currently only works via filesystem `decision.md` editing — no API bridge yet.

---

## Phase 3: View 3 — Graph to Document (Generation Review)

**Objective**: Split-pane with generated document (left) + contributing graph nodes (right), bidirectional text-to-node linking, direct Slate editing, comment categorization, feedback routing.

### Sub-objectives

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 3.1 | Split-pane: generated document + graph nodes | [x] | `ViewThreeGraphToDoc.tsx` — left: document textarea with doc-type tabs (motivation/cv/email), right: Diagrammatic-UI graph. |
| 3.2 | Bidirectional linking (text <-> source nodes) | [ ] | Not implemented. Document text and graph are displayed side by side but not linked. |
| 3.3 | Direct text editing with Slate.js | [ ] | Document is a read-only `<textarea>`. `RichTextPane` component exists but is not wired here. |
| 3.4 | Comment categorization (profile/redaction/match/other) | [ ] | Not implemented. |
| 3.5 | Feedback routing pipeline | [ ] | Not implemented. |

**Phase 3 overall: ~20%** — Display shell only. No editing, linking, or feedback features.

---

## Phase 4: Portfolio Dashboard + Navigation

**Objective**: Job tree with status indicators, profile knowledge graph view, base document templates, cross-job filtering, configurable gating policies.

### Sub-objectives

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 4.1 | Job tree with stage status indicators | [x] | `PortfolioPage.tsx` shows totals grid + `JobTree` component with links. `JobStagePage.tsx` shows per-stage status via `StageStatusBadge`. API `GET /api/v1/portfolio/summary` serves data. |
| 4.2 | Profile view with editable knowledge graph | [ ] | Not implemented. No profile route, no profile API endpoint. |
| 4.3 | Base document template views | [ ] | Not implemented. |
| 4.4 | Cross-job filtering and querying | [ ] | Not implemented. No search/filter UI or Cypher query integration. |
| 4.5 | Configurable stage gating policies | [ ] | Not implemented. Gating is hardcoded in pipeline graph, not configurable via UI. |

**Phase 4 overall: ~25%** — Basic navigation and status display work. All advanced features missing.

---

## Phase 5: LangChain Migration + Pipeline Adaptation

**Objective**: Replace custom AI layer with LangChain, add LangSmith tracing, pipeline writes to Neo4j, TextSpan provenance in scrapers.

### Sub-objectives

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 5.1 | Replace `LLMRuntime` with `ChatGoogleGenerativeAI` | [ ] | `src/ai/llm_runtime.py` still in use. |
| 5.2 | Replace `PromptManager` with `ChatPromptTemplate` wrappers | [ ] | `src/ai/prompt_manager.py` still in use. |
| 5.3 | Add LangSmith tracing | [ ] | No tracing integration. |
| 5.4 | Pipeline nodes write to Neo4j instead of JSON | [ ] | All nodes write to filesystem. |
| 5.5 | Scraper nodes produce `TextSpan` provenance | [ ] | Scraper outputs raw markdown, no span tracking. |

**Phase 5 overall: 0%** — Not started.

---

## Phase 6: Multi-Source Scraping + Scale

**Objective**: Per-source adapter framework, LLM fallback scraper, batch CLI, scale test with 1000+ jobs.

### Sub-objectives

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 6.1 | Per-source adapter framework | [ ] | Single TU Berlin scraper only. |
| 6.2 | LLM fallback scraper for unknown sites | [ ] | Not implemented. |
| 6.3 | Batch scraping CLI | [ ] | `run_available_jobs.py` exists for match batching, not scraping. |
| 6.4 | Scale testing with 1000+ jobs | [ ] | 7 jobs in current dataset. |

**Phase 6 overall: 0%** — Not started.

---

## Summary

| Phase | Fulfillment | Key blocker |
|-------|-------------|-------------|
| 0 Foundation | ~45% | Neo4j not running, data migration scripts missing, pip deps missing |
| 1 View 2 Doc-to-Graph | ~40% | Text-to-node creation, comments, Neo4j-backed spans |
| 2 View 1 Graph Explorer | ~35% | All mutation features, review decision UI |
| 3 View 3 Graph-to-Doc | ~20% | Slate editing, bidirectional linking, feedback routing |
| 4 Portfolio Dashboard | ~25% | Profile view, filtering, gating policies |
| 5 LangChain Migration | 0% | Full AI layer replacement |
| 6 Multi-Source Scraping | 0% | Adapter framework, scale |

## What actually works end-to-end today

1. React app builds and serves (`npm run build` passes, `npm run dev` starts Vite).
2. FastAPI API has 5 passing read-model tests (timeline, list jobs, view1/2/3 payloads).
3. View 2 (Doc-to-Graph) read-only inspection: source text + requirement highlighting + Diagrammatic-UI graph, wired to filesystem artifacts via API.
4. View 1 (Graph Explorer) read-only: match graph + score/reasoning table from match artifacts.
5. View 3 (Graph-to-Doc) read-only: document tabs (CV/letter/email) + contributing graph from generation artifacts.
6. Portfolio page: totals + job list navigating to per-job pages with stage status badges.
7. Neo4j schema constraints defined (17 uniqueness constraints) with bootstrap CLI/API endpoint ready.

## What does NOT work yet

1. Neo4j is not running and has never been populated with data.
2. No write/mutation endpoints exist on the API.
3. No comment system anywhere (no data model, no UI).
4. No review decision UI (approve/regen/reject only works via filesystem editing).
5. No Slate.js editing in any view (component exists, not integrated).
6. No profile view or cross-job querying.
7. No LangChain migration or TextSpan provenance.
8. `fastapi` and `neo4j` pip packages not in current environment.
