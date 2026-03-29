# Changelog

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
- Reworked `src/ai/generate_documents/graph.py` around `generate_documents_bundle()` so generation can run on in-memory inputs while persistence happens at the orchestration layer.
- Updated the generate-documents CLI and runtime docs to use the new schema-v0 data manager flow.
- Created `plan_docs/pipeline_unification.md` — implementation plan for orchestrating all modules under a single LangGraph pipeline with unified CLI and TUI wiring.
- Updated plan with critical corrections: (1) never call main.py from nodes — call adapters directly, (2) subgraph resume requires app.get_state() to obtain nested thread_id, (3) added fragility handling with dummy requirement on parse failure.
- Updated `plan_docs/2026-03-29-pipeline-unification-design.md` to be consistent with implementation plan: (1) keep existing module paths (src/ai/, src/tools/, src/review_ui/), (2) use summary payloads + refs for Studio compatibility, (3) call adapters directly in nodes, (4) resolved all open questions.
- **Implemented pipeline unification:**
  - Stage 1: extract_bridge node (src/graph/nodes/extract_bridge.py)
  - Stage 2: top-level pipeline graph (src/graph/__init__.py)
  - Stage 3: unified CLI (src/cli/main.py) with pipeline/scrape/translate/match/generate/render/review commands
  - Stage 4: TUI wiring (MatchBus.get_resume_config() for subgraph routing)
  - Stage 5: E2E tests (tests/e2e/test_pipeline.py)
- Fixed imports: src.ui.* → src.review_ui.*, src.translator.* → src.tools.translator.*
- Standardized CLI: translator and render main() accept argv parameter

## 2026-03-28

- Reorganized `src/render` into `documents/`, `engines/`, and `shared/` to separate document orchestration from rendering backends.
- Added a Pandoc-based rendering engine with initial Lua filter scaffolding for Markdown-first CV and letter generation.
- Preserved the legacy LaTeX CV compiler and DOCX post-processing helpers under engine-specific modules.
- Added `test_assets/` Markdown examples for CV and motivation letter rendering and verified PDF/DOCX generation end-to-end.
- Updated the Pandoc LaTeX path so sample metadata-driven images and CV semantic blocks render successfully to PDF.
- Rebased the `classic` CV template on the proven `Legacy_assets/general_cv` moderncv structure so the new Markdown pipeline uses the more familiar legacy layout.
- Added `src/ai/match_skill/` as a JSON-first LangGraph/LangChain-native reference implementation of the dev-branch match-review-regeneration loop.
- Replaced markdown review as the control surface in the new match skill with checkpointed HITL state updates plus structured review payloads.
- Added `src/ai/match_skill/main.py` so the new match skill can be run and resumed with JSON inputs plus SQLite-backed checkpoints.
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
