# Changelog

## 2026-04-09

- Restored the documented default profile seed for `generate_documents_v2` by adding `data/reference_data/profile/base_profile/profile_base_data.json`; added a unit test in `tests/unit/core/ai/generate_documents_v2/test_profile_loader.py` to verify the checked-in default profile path loads successfully, so default pipeline startup no longer fails immediately on a fresh clone due to a missing base profile file.
- Updated `generate_documents_v2` Gemini model selection so every LLM stage reads from environment configuration instead of hardcoding `gemini-2.5-flash`; stage-specific overrides now take precedence via variables such as `GEMINI_MODEL_INGESTION` and `GEMINI_MODEL_REQUIREMENT_FILTER`, with `GEMINI_MODEL=gemini-2.5-flash` as the shared default.
- Reworked the Textual review UI to target the active `generate_documents_v2` HITL flow instead of the removed `match_skill` module. The review bus now resolves pending `hitl_*` nodes, loads persisted stage artifacts from `generate_documents_v2`, and resumes the correct checkpoint with simple approve/reject actions. Added focused unit tests for review-stage mapping and API helper logic.
- Hardened the LangGraph API client and CLI pipeline flow so failed remote runs are normalized into explicit `status="failed"` results derived from thread state. `pipeline` now exits non-zero on remote errors instead of logging `status: None`, and helper tests cover failed-run normalization and CLI exit behavior.
- Improved manual review discovery for `generate_documents_v2`: the API client now inspects subgraph state when listing jobs and pending reviews, maps review checkpoints to `pending_review`, and the `review` command attaches to the existing LangGraph server instead of restarting it. This makes fresh manual runs discoverable again from the explorer/direct review surfaces.
- Fixed the top-level `generate` command so it matches the current `generate_documents_v2` pipeline API again. It now uses the checked-in default base profile, stops passing stale kwargs, and optionally renders CV and letter outputs through the shared render CLI. Added CLI tests covering both generation-only and generation-plus-render flows.
- Fixed the top-level `translate` command path by aligning translator CLI flag aliases (`--target_lang` and `--target-lang`), importing the missing `os` module, and returning proper exit codes from the translator entrypoint. Added a focused translator CLI test covering the operator-facing alias used by `src.cli.main`.
- Removed implicit self-approval for profile writeback. HITL patches with `persist_to_profile=True` now accumulate into `pending_profile_updates`, a dedicated `hitl_4_profile_updates` approval gate persists the proposed changes for operator review, and only explicit approval moves them into `approved_profile_updates` for the profile updater to write. Added focused tests for pending-update accumulation, profile-review preparation, and approval/rejection handling.
- Quarantined the archived legacy `match_skill` E2E suite with a module-level skip so the full test run reflects the supported `generate_documents_v2` runtime instead of failing collection on removed modules. `python -m pytest tests/ -q` now completes successfully in the current repository state.
- Refreshed the key runtime docs to match the current architecture: `src/core/ai/generate_documents_v2/README.md` now documents the real stage flow and profile approval gate, `docs/runtime/data_management.md` now shows the active artifact layout under `generate_documents_v2`, and `docs/runtime/pipeline_overview.md` now reflects the LangGraph + review UI control flow instead of retired modules.

## 2026-04-07

- Unified logging configuration: added `src/shared/logging_config.py` with `configure_logging(log_file=None)` that loads `config/logging.json` via `dictConfig`; all entry points (`cli/main.py`, `scraper/main.py`, `translator/main.py`, `apply/main.py`) now call it instead of `basicConfig`/`force=True`; third-party loggers (LangChain, LangGraph, httpx) capped at `WARNING` in `config/logging.json`; `LOG_DIR` env var controls log file destination; raw bracket strings in `translator/` replaced with `LogTag`.

- Implemented profile feedback updater in `generate_documents_v2`: added `ProfileUpdateRecord` model to `contracts/hitl.py` (fields: `field_path`, `old_value`, `new_value`, `source_stage`, `approved`); added `approved_profile_updates: list[dict]` to `GenerateDocumentsV2State`; extended `apply_patches()` in `hitl_patch_engine.py` to create self-approving `ProfileUpdateRecord` items for every `persist_to_profile=True` modify patch and accumulate them in state; added `_apply_dot_path(obj, path, value)` helper in `hitl_patch_engine.py` that writes a value at a dot-separated path, creating intermediate dicts as needed; replaced the no-op `_make_profile_updater_node` in `graph.py` with a real implementation that loads the profile JSON, applies each approved update, writes back to disk, and persists an audit artifact under `profile_updater/current.json`; added 15 tests in `tests/unit/core/ai/generate_documents_v2/test_profile_updater.py`; closed `future_docs/issues/core/ai/generate_documents_v2/profile_feedback_updater.md`.
- Implemented regional document strategy layer in `generate_documents_v2`: added `src/core/ai/generate_documents_v2/strategies.py` with `DocumentStrategy` dataclass and three named constants (`STRATEGY_GENERIC`, `STRATEGY_GERMAN_PROFESSIONAL`, `STRATEGY_ACADEMIC`); added `select_strategy(strategy_type, target_language)` which maps explicit names, defaults `"de"` to `STRATEGY_GERMAN_PROFESSIONAL`, and falls back to `STRATEGY_GENERIC`; added `filter_sections_by_strategy` to `profile_loader.py` which filters `SectionMappingItem` lists by `country_context` and reorders them per `strategy.section_order`; wired both into `stage3_macroplanning.py` and `pipeline.py`; added `chosen_strategy` field to `GlobalBlueprint` so the resolved strategy name is persisted in the blueprint stage artifact; added 19 tests in `tests/unit/core/ai/generate_documents_v2/test_strategies.py`; closed `future_docs/issues/core/ai/generate_documents_v2/regional_document_strategies.md`.
- Implemented HITL patch flow in `generate_documents_v2`: added `MatchReviewPayload`, `BlueprintReviewPayload`, `BundleReviewPayload`, and `PatchBundle` models to `contracts/hitl.py`; added `pending_patches: list[dict]` as a caller-settable field to `GenerateDocumentsV2State`; created `hitl_patch_engine.py` with `apply_patches()` as the standalone deterministic patch engine supporting `approve`, `reject`, `modify`, and `request_regeneration` actions for both dict and list artifacts; wired the engine into all three HITL nodes (`hitl_1_match_evidence`, `hitl_2_blueprint_logic`, `hitl_3_content_style`) so that resumed executions read and apply patches instead of returning `{"status": "interrupted"}`; patches are persisted per-stage under `<stage>/applied_patches/current.json`; `pending_patches` is cleared on every HITL node exit; added 9 unit tests in `test_hitl_patch_engine.py`; closed `future_docs/issues/core/ai/generate_documents_v2/hitl_patch_flow.md`.
- Formalized extension seams in `generate_documents_v2`: documented stable caller-configurable fields in `GenerateDocumentsV2State` (with full docstring covering `target_language`, `auto_approve_review`, `profile_path`, `mapping_path`, `profile_evidence`, `strategy_type`); wired `strategy_type` from graph state into the blueprint subgraph instead of hardcoding `"professional"`; annotated `SectionMappingItem.country_context` as the reserved regional-strategies seam; clarified `build_profile_kg` as the stable dict-based injection entry point; updated the README with a complete `## 🛠️ How to Add / Extend` section distinguishing stable extension points from internal-only surfaces; closed `future_docs/issues/core/ai/generate_documents_v2/extension_seams.md`.
- Removed module-level `DataManager` singleton from `profile_loader.py`; replaced `_DATA_MANAGER.read_json_path(p)` calls with `json.loads(p.read_text(encoding="utf-8"))` so the path is never frozen at import time.
- Extracted duplicated `_google_api_key()` helper from five node files into `src/core/ai/generate_documents_v2/nodes/_utils.py`.
- Fixed HITL bypass: changed `auto_approve_review` default from `True` to `False` in `graph.py` and added `LogTag.WARN` log lines to all three HITL nodes (match, blueprint, bundle) so auto-approve is always visible in logs.
- Added `salary_range: str | None` to `JobKG` and updated ingestion prompts to surface salary/pay-grade as a first-class contract field (extraction semantics gap audit).

## 2026-04-03

- Added repo map documents under `docs/repo_maps/` covering the current repo and the `feat-apply-module` worktree, focused on scraping, Crawl4AI, BrowserOS, applying docs, and Ariadne-related files.
- Added pre-migration automation reference docs under `plan_docs/automation/` defining the target directory glossary and asset-placement rules before any runtime move.
- Added `plan_docs/automation/superpowers_audit.md` to classify the remaining `docs/superpowers/` files as implemented, partial, stale, or broken-reference material before deleting that folder.
- Removed the old `docs/superpowers/` tree after preserving current behavior in `src/core/ai/generate_documents_v2/README.md`, moving deferred work into `future_docs/issues/`, and fixing broken apply-doc references.
- Removed stale render/test compatibility references by dropping the old `src.graph` test/script artifacts and retiring the `generate_documents` render dual-write fallback.
- Removed the old `plan_docs/applying/` bucket by deleting stale apply implementation checklists, deleting the legacy `manual_usuario`, moving apply traces into `data/ariadne/reference_data/applying_traces/`, moving BrowserOS/Crawl4AI external-library references into `docs/reference/external_libs/`, and rehoming future/issue material into `future_docs/` and `plan_docs/automation/`.
- Moved the Crawl4AI schema cache into `data/ariadne/assets/crawl4ai_schemas/` and removed root clutter files and folders (`uuid`, `session.txt`, `testsprite_tests/`, `logs/`, `output/`, and LaTeX aux files).
- Removed outdated global `future_docs/issues/` entries, rehomed live deferred items into mirrored paths, and then moved apply/scraper issue docs into `plan_docs/issues/{apply,scraper}/` with updated code references.
- Replaced the obsolete dev-branch `extract_understand` future doc with a narrower `generate_documents_v2` semantic-gap audit under `future_docs/issues/core/ai/generate_documents_v2/`.

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
- Added `future_docs/new_feature/logging_layer_conflicts.md` to track the mixed logging setup and the need for a shared application logging bootstrap.

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
