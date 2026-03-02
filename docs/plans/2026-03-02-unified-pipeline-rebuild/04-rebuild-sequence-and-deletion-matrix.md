# Rebuild Sequence and Deletion Matrix

Date: 2026-03-02
Execution mode: destructive cleanup followed by unified rebuild

## 1) Deletion Matrix

Delete these implementation layers (recreated in `src/unified_pipeline/`):

- `src/agent/` (all wrappers/orchestrators/tools)
- Legacy orchestration internals in `src/cli/pipeline.py`
- `src/cv_generator/pipeline.py`
- `src/cv_generator/ats.py`
- Legacy CV CLI wrapper pathways in `src/cv_generator/__main__.py` that encode old flow assumptions
- Legacy motivation orchestration service layer

Keep and integrate only:

- `src/utils/gemini.py`
- `src/prompts/`
- `src/models/`
- `src/render/`
- deterministic scraper/translation primitives

## 2) Rebuild Sequence

Step 1: Create new backbone

- Create `src/unified_pipeline/` package.
- Add state, contracts, checkpoints, and runner modules.

Step 2: Implement LLM template first

- Build one parser+validator+retry layer.
- Ensure all downstream nodes import only this layer for LLM calls.

Step 3: Add deterministic nodes

- Ingest/context/report/render nodes using existing deterministic engines.

Step 4: Add LLM nodes

- Match/gap/proposal/motivation/email nodes.
- Validate outputs against Pydantic contracts.

Step 5: Add graph wiring

- Build LangGraph transitions and review gate.
- Add resume support from checkpoints.

Step 6: Replace CLI surface

- Introduce unified CLI commands.
- Remove or alias old commands with deprecation notice.

Step 7: Tests and migration docs

- Unit + integration + resume tests.
- Update README and docs with only new architecture.

## 3) Hard Constraints During Rewrite

1. No direct `GeminiClient.generate(...)` in node modules.
2. No local JSON extraction helpers in feature modules.
3. No duplicate state definitions across modules.
4. No writes into archived job directories during generation flow.

## 4) Exit Criteria for Cleanup Stage

- Old wrappers are absent.
- Unified package compiles and exposes graph entrypoint.
- All tests referencing removed wrappers are either migrated or deleted.
