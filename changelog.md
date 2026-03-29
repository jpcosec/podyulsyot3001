# Changelog

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
