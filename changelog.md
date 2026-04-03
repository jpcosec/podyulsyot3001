# Changelog

## 2026-04-03

- Added repo map documents under `docs/repo_maps/` covering the current repo and the `feat-apply-module` worktree, focused on scraping, Crawl4AI, BrowserOS, applying docs, and Ariadne-related files.
- Added pre-migration automation reference docs under `plan_docs/automation/` defining the target directory glossary and asset-placement rules before any runtime move.
- Added `plan_docs/automation/superpowers_audit.md` to classify the remaining `docs/superpowers/` files as implemented, partial, stale, or broken-reference material before deleting that folder.
- Removed the old `docs/superpowers/` tree after preserving current behavior in `src/core/ai/generate_documents_v2/README.md`, moving deferred work into `future_docs/issues/`, and fixing broken apply-doc references.

## 2026-03-31

- Added `docs/superpowers/specs/2026-03-31-generate-documents-spec.md` as a consolidated, quick-reference specification distilled from the exploratory generate-documents delta design notes.
- Added a split spec set for generate-documents under `docs/superpowers/specs/`: graph flow, Pydantic contracts, HITL behavior, regional cases, examples, and extension guidance for faster lookup by topic.
- Implemented `src/core/ai/generate_documents_v2/` Plan 1 with new contracts, stage artifact storage, profile loading, canonical section mapping fixture, and the first job-side nodes for ingestion (`J1 -> J2`) and requirement filtering (`J2 -> J3`).
- Expanded `generate_documents_v2` ingestion to consume a bundled ingest surface (`state.json`, `listing.json`, `listing_case.json`) instead of a single reconstructed raw string, and updated `JobKG` to preserve original titles while keeping audit-facing semantic fields in English.
- Extended `generate_documents_v2` with the next pipeline layer: profile-job alignment, blueprint generation, document drafting, and deterministic Markdown assembly, plus tests and a real end-to-end smoke run over a Stepstone artifact with live Gemini calls.
- Integrated final-stage localization, render-compatible Markdown persistence, LangGraph wiring with HITL checkpoints and profile patch persistence, updated the CLI and top-level pipeline to use `generate_documents_v2`, and removed obsolete match-skill-era tests after validating the new path with live API calls and PDF output generation.

## 2026-03-29 (future follow-up notes)

- Added `future_docs/issues/profile_input_loading_node.md` to capture a pipeline design gap: profile evidence loading and legacy normalization are currently embedded in orchestration glue instead of a dedicated node with a single canonical contract.

## 2026-03-29 (canonical ingest refactor)

- Moved the scraper implementation to `src/scraper/` and removed the old `src/core/ai/scraper/` package.
- Refactored scraper persistence to write canonical raw artifacts directly under `data/jobs/<source>/<job_id>/nodes/ingest/proposed/` through `DataManager`.
- Added `DataManager.ingest_raw_job()` and `DataManager.has_ingested_job()` to centralize raw-ingestion storage and existence checks.
- Replaced the pipeline's source-wide `scrape` wrapper behavior with a canonical `ingest` node that reuses existing artifacts or performs explicit single-job fetches from `source_url`.
- Updated translator CLI and runtime docs to consume canonical ingest artifacts instead of `data/source/...`.
- Tightened CSS schema generation prompts to focus on the main detail page and avoid related-job teaser selectors; added XING-specific hints to ignore `similar-jobs` and sticky teaser layouts.
- Added `docs/standards/code/crawl4ai_usage.md` to define the repository rule: new scraper sources may bootstrap with Crawl4AI-assisted LLM extraction, but stable sources must converge to saved deterministic schemas.
- Added `plan_docs/issues/crawl4ai_scraper_correction.md` to capture the correction plan for listing/detail separation, Crawl4AI-native LLM fallback, and source-specific merge before validation.
- Scraper ingest now preserves broader raw Crawl4AI surfaces per job, including raw plus cleaned detail HTML, listing context, raw plus cleaned listing HTML, listing markdown, and raw structured extraction output.
- XING discovery now isolates the job-specific listing card, persists `listing_case.*` artifacts, and anchors relative listing dates to the scrape timestamp when possible.
- Scraper ingestion now fails closed for success accounting: invalid extractions persist diagnostics under `nodes/ingest/failed/` and no longer count as successful ingests.
- Extended the scraper contract with optional application-routing fields so sources can capture whether to apply by email or portal, plus direct application URLs and instructions when present.
- Added `future_docs/issues/application_routing_extraction.md` and linked a `TODO(future)` in `src/scraper/models.py` because application routing may belong in a later interpretation stage rather than deterministic scrape-time extraction.
- Added `future_docs/issues/logging_layer_conflicts.md` to track the mixed logging setup and the need for a shared application logging bootstrap.

## 2026-03-29 (data manager standardization)

- Moved `src/ai/` under `src/core/ai/` and `src/tools/` under `src/core/tools/` so graph nodes remain orchestration-only and deterministic runtime helpers live under `core`.
- Centralized runtime file IO behind `src/core/data_manager.py` and removed direct filesystem bypasses from `src/graph/`, `src/core/ai/`, and `src/core/tools/`.
- Added `tests/test_file_management_guardrails.py` to fail if runtime code reintroduces direct `Path.read_text()`, `write_text()`, `mkdir()`, or similar bypasses outside `DataManager`.

## 2026-03-29 (API-only CLI control plane)

- Refactored `src/cli/main.py` around an API-first workflow: added `api`, `search`, and `run-batch` commands, made `review` support true explorer mode, and removed local SQLite fallbacks from CLI-driven LangGraph execution.
- Updated `src/core/api_client.py` to start or reuse `langgraph dev`, flatten thread metadata for the TUI explorer, invoke graph-specific assistants, and resume threads using the assistant recorded in API state metadata.
- Removed local graph mutation from `src/review_ui/bus.py`; review submissions now resume threads through the LangGraph API only.
- Updated `src/core/ai/match_skill/main.py` and launcher scripts so stateful match/pipeline workflows go through the LangGraph API instead of local `SqliteSaver` execution.

## 2026-03-29 (pipeline graph unification)

- **Pipeline graph unification:**
  - `match_skill` is now a native LangGraph compiled subgraph — inner topology (`load_match_inputs → run_match_llm → persist_match_round → human_review_node → apply_review_decision → prepare_regeneration_context / generate_documents`) is fully visible in LangGraph Studio.
  - Replaced `Command`-based routing in `apply_review_decision` with `add_conditional_edges` so all routing paths are statically declared and Studio renders them as connected edges.
  - `GraphState` now carries `requirements` and `profile_evidence`; `extract_bridge` populates both so state flows into the subgraph without wrapper glue.
  - Removed `src/graph/nodes/match_skill.py` opaque wrapper node.
  - Added `include_document_generation` param to `build_match_skill_graph` — pipeline embeds the subgraph without internal doc-gen duplication; standalone use retains it.
  - Reject decision now surfaces as `status="rejected"` (was `"completed"`).

## 2026-03-29

- Finished the schema-v0 runtime migration: `match_skill`, `review`, `extract_bridge`, and document generation now use `data/jobs/<source>/<job_id>/...` instead of the legacy `output/match_skill` bridge.
- Updated repository docs and module READMEs so CLI examples and storage references point to the schema-v0 runtime roots.
- Added `docs/runtime/data_management.md` and introduced schema-v0 data-plane rules centered on `data/jobs/<source>/<job_id>/` plus per-job `meta.json` lifecycle metadata.
- Added `src/core/data_manager.py`, `src/core/state.py`, and `tests/test_data_manager.py` as the first central schema-v0 runtime layer.
- Refactored `src/graph/` into thinner node adapters under `src/graph/nodes/` and moved top-level shared state imports to `src/core/state.py`.
- Reworked `src/core/ai/generate_documents/graph.py` around `generate_documents_bundle()` so generation can run on in-memory inputs while persistence happens at the orchestration layer.
- Updated the generate-documents CLI and runtime docs to use the new schema-v0 data manager flow.
- Created `plan_docs/pipeline_unification.md` — implementation plan for orchestrating all modules under a single LangGraph pipeline with unified CLI and TUI wiring.
- Updated plan with critical corrections: (1) never call main.py from nodes — call adapters directly, (2) subgraph resume requires app.get_state() to obtain nested thread_id, (3) added fragility handling with dummy requirement on parse failure.
- Updated `plan_docs/2026-03-29-pipeline-unification-design.md` to be consistent with implementation plan: (1) keep existing module paths (src/core/ai/, src/core/tools/, src/review_ui/), (2) use summary payloads + refs for Studio compatibility, (3) call adapters directly in nodes, (4) resolved all open questions.
- **Implemented pipeline unification:**
  - Stage 1: extract_bridge node (src/graph/nodes/extract_bridge.py)
  - Stage 2: top-level pipeline graph (src/graph/__init__.py)
  - Stage 3: unified CLI (src/cli/main.py) with pipeline/scrape/translate/match/generate/render/review commands
  - Stage 4: TUI wiring (MatchBus.get_resume_config() for subgraph routing)
  - Stage 5: E2E tests (tests/e2e/test_pipeline.py)
- Fixed imports: src.ui.* → src.review_ui.*, src.translator.* → src.core.tools.translator.*
- Standardized CLI: translator and render main() accept argv parameter

## 2026-03-28

- Reorganized `src/render` into `documents/`, `engines/`, and `shared/` to separate document orchestration from rendering backends.
- Added a Pandoc-based rendering engine with initial Lua filter scaffolding for Markdown-first CV and letter generation.
- Preserved the legacy LaTeX CV compiler and DOCX post-processing helpers under engine-specific modules.
- Added `test_assets/` Markdown examples for CV and motivation letter rendering and verified PDF/DOCX generation end-to-end.
- Updated the Pandoc LaTeX path so sample metadata-driven images and CV semantic blocks render successfully to PDF.
- Rebased the `classic` CV template on the proven `Legacy_assets/general_cv` moderncv structure so the new Markdown pipeline uses the more familiar legacy layout.
- Added `src/core/ai/match_skill/` as a JSON-first LangGraph/LangChain-native reference implementation of the dev-branch match-review-regeneration loop.
- Replaced markdown review as the control surface in the new match skill with checkpointed HITL state updates plus structured review payloads.
- Added `src/core/ai/match_skill/main.py` so the new match skill can be run and resumed with JSON inputs plus SQLite-backed checkpoints.
- Added `langgraph.json` and a Studio-specific graph factory so `match_skill` can be inspected in LangGraph Studio.
- Refreshed `requirements.txt` to current direct dependency versions, added Studio/dev-server support via `langgraph-cli[inmem]`, and added `pytest` for clean env rebuild verification.
- Added sample match-skill payloads under `test_assets/match_assets/` and ignored local LangGraph/output runtime state.
- Added `docs/runtime/match_skill_studio_implementation_guide.md` documenting the implementation, Studio workflow, browser bridge setup, and validation path for the new match skill.
- Split the match skill runtime guide into separate product and methodology documents for easier navigation.
- Added `docs/runtime/match_skill_hardening_roadmap.md` detailing the recommended next hardening steps for the match skill.
- Reworked `src/render` around `RenderRequest` and `RenderCoordinator` so document type, engine, style, and language are resolved independently.
- Added typed modular language bundles for `en`, `es`, and `de`, with document-specific locale modules and style-aware metadata lookup.
- Moved active render templates to root-level `src/render/templates/` with explicit style manifests that declare templates, assets, and Lua filters.
- Added six localized Markdown render fixtures under `test_assets/cv/` and `test_assets/letter/`, and verified multilingual PDF rendering for CV and letter outputs.
