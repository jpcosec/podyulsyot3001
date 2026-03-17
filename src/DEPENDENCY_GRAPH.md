# Source Dependency Graph

This file maps module dependencies and test impact to reduce discovery cost between sessions.

## API Subgraph (`src/interfaces/api`)

Nodes:

- `app.py`: FastAPI app factory, router wiring, CORS policy.
- `config.py`: runtime settings from environment.
- `models.py`: response dataclasses and `to_dict` conversion.
- `read_models.py`: filesystem-backed read models for timeline and View 1/2/3 payloads.
- `routers/health.py`: health endpoint.
- `routers/portfolio.py`: portfolio summary endpoint.
- `routers/jobs.py`: timeline, review payload, view payload endpoints.
- `routers/neo4j.py`: Neo4j health/bootstrap endpoints.
- `neo4j_client.py`: connectivity check.
- `neo4j_schema.py`: schema constraint application.

Edges:

- `app.py` -> `config.py`, `routers/*`
- `routers/portfolio.py` -> `config.py`, `models.py`, `read_models.py`
- `routers/jobs.py` -> `config.py`, `models.py`, `read_models.py`
- `routers/neo4j.py` -> `config.py`, `neo4j_client.py`, `neo4j_schema.py`
- `read_models.py` -> `models.py`, `src/core/graph/state.py`, filesystem artifacts under `data/jobs/`

Primary tests:

- `tests/interfaces/api/test_read_models.py`

Impact testing:

- If `read_models.py` changes: run `python -m pytest tests/interfaces/api -q`
- If `routers/*.py` changes: run `python -m pytest tests/interfaces/api -q` and API smoke checks
- If `config.py` changes: run API tests and boot app import check
- If `neo4j_*.py` changes: run API tests and Neo4j connectivity/bootstrap checks in local env

## Review Workbench Subgraph (`apps/review-workbench/src`)

Nodes:

- `App.tsx`: route root.
- `api/client.ts`: fetch layer for backend endpoints.
- `types/models.ts`: typed API contracts for UI.
- `pages/PortfolioPage.tsx`: portfolio dashboard.
- `pages/JobStagePage.tsx`: stage list and view selection.
- `views/ViewOneGraphExplorer.tsx`: match graph inspection.
- `views/ViewTwoDocToGraph.tsx`: source-to-requirement review panel.
- `views/ViewThreeGraphToDoc.tsx`: generated document review shell.
- `components/GraphCanvas.tsx`: Cytoscape rendering layer.
- `components/StageStatusBadge.tsx`: stage status presentation.
- `components/JobTree.tsx`: job navigation list.
- `components/RichTextPane.tsx`: standalone Slate editor component.

Edges:

- `App.tsx` -> `pages/*`
- `pages/PortfolioPage.tsx` -> `api/client.ts`, `components/JobTree.tsx`
- `pages/JobStagePage.tsx` -> `api/client.ts`, `components/StageStatusBadge.tsx`, `views/*`
- `views/*` -> `api/client.ts`, `components/GraphCanvas.tsx`, `types/models.ts`
- `api/client.ts` -> backend endpoints under `src/interfaces/api/routers`

Primary verification:

- `npm --prefix apps/review-workbench run build`

Impact testing:

- If `types/models.ts` changes: run build and manually verify all three views
- If `api/client.ts` changes: run build and endpoint smoke checks against running API
- If any `views/*` changes: run build and validate affected route in browser
- If `GraphCanvas.tsx` changes: verify View 1, View 2, and View 3 rendering

## Cross-Subgraph Contracts

- UI contract boundary: `apps/review-workbench/src/types/models.ts` <-> `src/interfaces/api/models.py`
- Endpoint boundary: `apps/review-workbench/src/api/client.ts` <-> `src/interfaces/api/routers/*.py`

When changing one side of a contract, validate the other side in the same session.

## Pipeline Subgraph (`src/core`, `src/ai`, `src/nodes`)

Nodes:

- `src/graph.py`: graph assembly and routing.
- `src/core/graph/state.py`: control-plane state contract and thread identity helpers.
- `src/ai/llm_runtime.py`: model runtime boundary.
- `src/ai/prompt_manager.py`: prompt rendering and tag validation.
- `src/nodes/scrape/logic.py`: ingestion step.
- `src/nodes/translate_if_needed/logic.py`: translation normalization step.
- `src/nodes/extract_understand/logic.py`: extraction LLM node.
- `src/nodes/match/logic.py`: matching LLM node and review artifact generation.
- `src/nodes/review_match/logic.py`: deterministic review parser and routing.
- `src/nodes/generate_documents/logic.py`: document delta generation and deterministic rendering outputs.

Edges:

- `src/graph.py` -> all registered node `run_logic` handlers.
- `extract_understand/match/generate_documents` -> `src/ai/llm_runtime.py`, `src/ai/prompt_manager.py`.
- `review_match` consumes match review artifacts and routes back to `match` or forward to `generate_documents`.
- `generate_documents` consumes match approval artifacts and profile data references.

Primary tests:

- `tests/core/graph/test_prep_match_helpers.py`
- `tests/nodes/match/test_match_logic.py`
- `tests/nodes/review_match/test_review_match_logic.py`
- `tests/nodes/generate_documents/test_generate_documents_logic.py`
- `tests/nodes/generate_documents/test_contract.py`

Impact testing:

- If `src/graph.py` changes: run graph helper tests and at least one prep-match run path test.
- If `src/ai/*` changes: run node tests that cover extraction/match/generation prompt/runtime calls.
- If `src/nodes/match/*` changes: run match + review_match tests together.
- If `src/nodes/review_match/*` changes: run review parser tests and regeneration loop tests.
- If `src/nodes/generate_documents/*` changes: run generate_documents contract + logic tests.
