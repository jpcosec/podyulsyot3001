# Motivation Letter System Deep Dive

This document is the full technical description of the motivation-letter subsystem in this repository.

It covers:

- every runtime entrypoint used by the unified CLI,
- every major data contract and artifact path,
- where generation is prompt-driven vs hardcoded,
- and the target direction for a fully agent-interaction-based flow.

## 1) Scope and Current Status

The motivation subsystem currently combines deterministic orchestration and LLM generation:

- deterministic context assembly and planning scaffolding,
- one prompt-driven final letter expansion call,
- deterministic PDF rendering and deterministic email draft generation.

So today it is a hybrid system, not a fully agentic one.

## 2) Runtime Entrypoints

Primary CLI: `src/cli/pipeline.py`

Motivation-related commands:

- `motivation-build <job_id>`
- `motivation-build <job_id>`
- `app-prepare <job_id> --target motivation|all`
- `app-renderize <job_id> --target motivation|all`
- `app-run <job_id> --target motivation|all`

Service implementation:

- `src/motivation_letter/service.py`

Public service methods:

- `build_context(...)`
- `build_prompt(...)`
- `create_planning(...)`
- `generate_for_job(...)`
- `build_pdf_for_job(...)`
- `generate_email_draft(...)`

## 3) End-to-End Execution Flows

### 3.1 `motivation-build`

1. Builds context from job + profile + evidence + format insights.
2. Generates synthetic planning scaffold (`motivation_letter.pre.md`).
3. Updates evidence bank (`evidence_bank.json`).
4. Writes pre-analysis JSON (`motivation_letter.pre.analysis.json`).

No LLM call happens in this command.

### 3.2 `motivation-build`

1. Rebuilds context and planning artifacts.
2. Builds final prompt from template + context JSON.
3. Calls generator (default: Gemini client).
4. Parses strict JSON response (`subject`, `salutation`, `letter_markdown`).
5. Writes final letter markdown + analysis JSON.
6. Optionally builds PDF.
7. Optionally builds email draft.

### 3.3 Unified app lifecycle integration

- `app-prepare --target motivation` uses `create_planning(...)` and writes staged prep artifacts under `output/prep/motivation/`.
- `app-review` checks unresolved HTML comments only in `output/prep/**/*.md`.
- `app-renderize --target motivation` uses `generate_for_job(...)`, builds PDF, writes email draft, and copies final files into `output/final/motivation/`.

## 4) Inputs, Prompts, and Outputs

### 4.1 Inputs

- Job tracker: `data/pipelined_data/<source>/<job_id>/job.md`
- Canonical profile: `data/reference_data/profile/base_profile/profile_base_data.json`
- Optional inspiration letter: `data/pipelined_data/<source>/<job_id>/planning/motivation_letter copy.md`

### 4.2 Prompt source

- Prompt template file: `data/reference_data/prompts/Academic_Motivation_Letter_Prompt.txt`
- Required placeholder token: `{{CONTEXT_JSON}}`

If the prompt file is missing or the token is absent, generation fails fast.

### 4.3 Generator backend

Default generator path:

- `MotivationLetterService._default_generator(...)`
- `src/utils/gemini.py` -> `GeminiClient`

Env requirements:

- `GOOGLE_API_KEY`
- optional `GEMINI_MODEL` (default `gemini-2.5-flash`)

### 4.4 Core outputs

Planning outputs:

- `planning/motivation_letter.pre.md`
- `planning/motivation_letter.pre.analysis.json`
- `planning/motivation_letter.md`
- `planning/motivation_letter.analysis.json`
- `planning/application_email.md`

Build/output artifacts:

- `build/motivation_letter/*.tex`
- `output/motivation_letter.pdf`

Pipeline-staged outputs:

- `output/prep/motivation/...`
- `output/final/motivation/motivation_letter.md`
- `output/final/motivation/motivation_letter.pdf`
- `output/final/motivation/application_email.md`

Cross-job evidence memory:

- `data/reference_data/profile/evidence/evidence_bank.json`

## 5) Data Model Contracts

### 5.1 Context contract assembled by `build_context(...)`

Top-level keys:

- `meta`
- `job`
- `candidate`
- `analysis`
- `artifacts`
- `constraints`

Notable sections:

- `job.requirements`: extracted from `## Their Requirements` checklist lines (`- [ ] ...`).
- `job.responsibilities`: extracted from `## Area of Responsibility` checklist lines.
- `job.fit_signals_from_job_tracker`: extracted non-checklist bullets from `## How I Match`.
- `candidate.evidence_catalog`: generated evidence cards from profile/model data.
- `analysis.requirement_coverage`: heuristic requirement-to-evidence coverage scoring.
- `analysis.format_insights`: structure/quality signals from optional inspiration letter.

### 5.2 Model output contract (LLM response)

The final generation parser requires JSON object fields:

- `subject` (non-empty string)
- `salutation` (non-empty string)
- `letter_markdown` (non-empty string)

Optional fields currently persisted when available:

- `fit_signals`
- `risk_notes`

### 5.3 Evidence bank contract

`evidence_bank.json` includes:

- `items[]` with `bank_id`, `fingerprint`, `category`, `text`, `tags`, source metadata,
- `job_runs[]` with per-job linked requirement coverage,
- `updated_at_utc` and version metadata.

## 6) What Is Hardcoded vs Agent-Driven Today

### 6.1 Prompt/LLM-driven parts

- Final prose generation in `generate_for_job(...)` is prompt-driven.
- Prompt path is configurable at service construction (`prompt_path`).
- Output is parsed and validated strictly after generation.

### 6.2 Deterministic/hardcoded parts

The following are currently deterministic and embedded in code:

- Pre-letter scaffold structure and fixed section labels in `_render_planning(...)`.
- Section planning keyword logic in `_build_section_plan(...)`.
- Format-insight fallback strengths/improvements in `_build_inspiration_insights(...)`.
- Email draft content and phrasing in `generate_email_draft(...)`.
- Requirement summary heuristics in `_summarize_requirement_for_email(...)`.
- Requirement coverage scoring thresholds in `_analyze_requirement_coverage(...)`.
- PDF LaTeX assembly in `_render_letter_tex(...)` and `_render_letter_body_from_blocks(...)`.

Conclusion: only the final letter expansion step is currently agentic.

## 7) Full Method Inventory (`MotivationLetterService`)

### 7.1 Public API

- `__init__`
- `build_context`
- `build_prompt`
- `create_planning`
- `generate_for_job`
- `build_pdf_for_job`
- `generate_email_draft`

### 7.2 Orchestration internals

- `_write_planning_artifacts`
- `_default_generator`

### 7.3 Planning and scaffold generation

- `_build_section_plan`
- `_render_planning`
- `_render_format_insights_lines`
- `_render_evidence_lines`
- `_render_evidence_cards`

### 7.4 Evidence bank and evidence mapping

- `_update_evidence_bank`
- `_load_evidence_bank`
- `_find_bank_item`
- `_next_evidence_bank_index`
- `_collect_coverage_evidence_ids`
- `_select_evidence_ids_by_keywords`
- `_format_evidence_refs`
- `_build_evidence_catalog`
- `_analyze_requirement_coverage`
- `_requirement_evidence_score`
- `_build_search_tags`
- `_merge_unique`
- `_fingerprint`

### 7.5 Job/candidate parsing and extraction

- `_parse_frontmatter`
- `_extract_posting_title`
- `_extract_section_block`
- `_extract_checklist_items`
- `_extract_bullet_items`
- `_build_candidate_payload`

### 7.6 Inspiration-analysis helpers

- `_build_inspiration_insights`
- `_analyze_inspiration_letter`
- `_split_paragraphs`

### 7.7 PDF/LaTeX rendering helpers

- `_render_letter_tex`
- `_extract_letter_blocks`
- `_render_letter_body_from_blocks`
- `_escape_latex`

### 7.8 Email helpers and model-output parsing

- `_clean_posting_title`
- `_summarize_requirement_for_email`
- `_parse_generation_output`
- `_parse_json_loose`
- `_extract_json_object`

## 8) Validation and Tests

Current tests: `tests/motivation_letter/test_service.py`

Covered behavior:

- context extraction,
- planning/evidence-bank write path,
- final generation output parsing and persistence,
- deterministic email draft generation,
- PDF build path with mocked `pdflatex`.

## 9) Gaps Relative to a Fully Agentic Architecture

If the target is "pre-stage should not be hardcoded" and "whole system based on agent interaction", current gaps are:

1. Pre-letter scaffold content is static Python strings.
2. Section plan selection is keyword/threshold logic, not LLM planning.
3. Email drafting is hardcoded and detached from prompt framework.
4. Only one prompt file exists for final letter, not for planning/review stages.
5. No explicit multi-agent stage contracts (planner/writer/reviewer/verifier).

## 10) Recommended Agent-Interaction Target Design

### 10.1 Agent stages

1. **Planner agent**: turn context into a structured section plan (JSON schema).
2. **Evidence-mapper agent**: map requirements to evidence IDs with confidence and gaps.
3. **Writer agent**: draft planning from structured plan (no hardcoded scaffold text).
4. **Rewriter agent**: produce final letter from planning + format insights + constraints.
5. **Critic/verifier agent**: check factual grounding and contract compliance before persistence.

### 10.2 Prompt files to externalize

Recommended prompt set under `data/reference_data/prompts/`:

- `motivation_planner_prompt.txt`
- `motivation_evidence_mapper_prompt.txt`
- `motivation_preletter_writer_prompt.txt`
- `motivation_final_writer_prompt.txt`
- `motivation_critic_prompt.txt`
- `motivation_email_prompt.txt`

### 10.3 Keep deterministic guardrails

Even with full agent interaction, keep deterministic checks for:

- required JSON fields,
- evidence IDs referenced by claims,
- min/max word constraints,
- subject/reference consistency,
- no unsupported claims.

## 11) Operational Notes for Maintainers

- `app-review` only reads comments in `output/prep/**/*.md`; comments in source files (for example `cv/to_render.md`) are not part of review gate.
- `motivation-build` currently rebuilds planning artifacts before final generation.
- Prompt quality is bounded by context quality; stale or incomplete profile evidence propagates to outputs.

## 12) Related Docs

- `docs/pipeline/end_to_end_pipeline_deep_dive.md`
- `docs/agents/unified_app_pipeline_skill.md`
- `docs/cv/ats_checker_deep_dive.md`
