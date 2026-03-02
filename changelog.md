# Changelog

## 2026-03-02 — De-hardcode Pipeline & Agent Architecture

### Added
- `src/models/` — Pydantic models for job postings, pipeline contract, motivation letters, and application plans
- `src/prompts/` — Centralized prompt files with loader utility (moved from data/reference_data/prompts/)
- `src/agent/tools.py` — Tool functions wrapping scraper, renderer, ATS, and motivation services
- `src/agent/orchestrator.py` — `ApplicationAgent` for batch application processing
- `apply-to <urls>` CLI command — guided application workflow with human-in-the-loop checkpoints
- `src/prompts/email_draft.txt` — Agent prompt for email generation
- `src/prompts/motivation_pre_letter.txt` — Agent prompt for motivation letter planning

### Changed
- `src/cv_generator/pipeline.py` — Rewritten as `CVTailoringPipeline` using full prompts from files + Pydantic models
- `src/motivation_letter/service.py` — Rebuilt as agent-driven (pre-letter plan + generation + email all via LLM)
- `src/cv_generator/ats.py` — Uses `src/prompts/` loader instead of hardcoded path

### Removed
- `CV_RULES` constant from `src/cli/pipeline.py` — replaced by MATCHER agent
- `render_job_cv_body()`, `render_job_cv_main()`, `ensure_job_cv_sources()` — hardcoded LaTeX content
- `build_cv_tailoring()` hardcoded logic — now delegates to `CVTailoringPipeline`
- `_build_section_plan()`, `_render_pre_letter()` and helper methods from `MotivationLetterService` — replaced by pre-letter agent
- Hardcoded email draft template from `generate_email_draft()` — replaced by email agent
- `data/reference_data/prompts/AST.md` — duplicate of ATS prompt

## 2026-03-02

- Added full motivation subsystem documentation at `docs/pipeline/motivation_letter_system_deep_dive.md`, covering runtime entrypoints, data contracts, method inventory, hardcoded vs prompt-driven boundaries, and a target multi-agent architecture.
- Linked the new motivation deep dive from `docs/pipeline/end_to_end_pipeline_deep_dive.md` for hierarchical navigation from pipeline overview to subsystem internals.

## 2026-03-01 (continued)

- Expanded motivation-letter generation with a two-step flow: synthetic pre-letter scaffold (`motivation_letter.pre.md`) plus final expansion; inserted explicit format-insights bridge (strengths to preserve + improvements to apply) between pre-render and final prompt, now dynamically analyzed from `planning/motivation_letter copy.md` when present; added requirement-to-evidence analysis and reusable cross-job evidence bank at `data/reference_data/profile/evidence/evidence_bank.json`, implemented in `src/motivation_letter/service.py` with tests in `tests/motivation_letter/test_service.py`.
- Added pipeline CLI commands `motivation-pre` and `motivation-build` in `src/cli/pipeline.py` and parser tests in `tests/cli/test_pipeline.py`.
- Added `.env` auto-loading fallback for Gemini credentials in `src/utils/gemini.py` and a conda environment reminder warning (`phd-cv`) for motivation commands in `src/cli/pipeline.py`.
- Updated `motivation-build` to produce formal PDF output (`output/motivation_letter.pdf`) and an application email draft (`planning/application_email.md`); added PDF/email service methods and tests.
- Added unified two-stage application lifecycle in `src/cli/pipeline.py`: `app-prepare`, `app-review`, `app-renderize` with state tracking at `output/state.md`, prep-comment review (`<!-- ... -->`), and ATS analysis in both prep and renderize stages for CV and motivation targets.
- Added `app-status` (state summary per job) and `jobs-index` (central job-id index by source folder) commands to the unified pipeline workflow.
- Added `app-run` orchestrator command to execute prepare -> review -> renderize in one step (with correction gate at review stage).
- Improved motivation-letter PDF rendering layout in `src/motivation_letter/service.py` (structured letter blocks, better spacing/typography, subject emphasis) and rebuilt the 201084 final motivation PDF.
- Added deterministic URL-targeted scraping flow (`src/scraper/scrape_single_url.py`) and CLI command `fetch-url` in `src/cli/pipeline.py`, implementing: download HTML -> extract full source text markdown -> English check -> parse markdown to structured JSON -> render minimal `job.md`.
- Migrated job 201084 to new sub-zone layout (`raw/`, `planning/`, `cv/`, `output/`, `build/`); deleted superseded experimental DOCX variants.
- Switched Gemini SDK from deprecated `google-generativeai` to `google-genai`; updated model to `gemini-2.5-flash` in `.env` and `environment.yml`.
- Fixed all hardcoded `/home/jp` paths and `gemini-1.5-flash` model references in `src/`.
- Added `docs/cv/ats-guidelines.md` documenting ATS formatting constraints, safe elements, photo policy, and section order.
- Removed `src/build_word_cv.py`'s hardcoded photo path; output now writes to `cv/rendered/`.
- Consolidated `docs/plan/` into `docs/pipeline/end_to_end_pipeline_deep_dive.md`; deleted stale `docs/plan/` directory.
- Updated README.md structure diagram to reflect current job sub-zone layout, actual `src/` modules, and current gap list.
- Updated `docs/pipeline/end_to_end_pipeline_deep_dive.md` job-scoped contract section to match actual `raw/` and `planning/` layout.

## 2026-03-01

- Added deterministic template testing commands: `python -m src.cv_generator test-template ...` and `python src/cli/pipeline.py cv-template-test ...` with optional `--require-perfect` 100% gate.
- Added automatic `to_render.md` generation during CV render/build so parity checks have a canonical source input.
- Improved deterministic parity normalization for punctuation/dash variations to better reflect ATS text extraction equivalence.
- Simplified CV command surface: rendering/build now defaults to final PDF output with explicit engine selection via `--via latex|docx`; ATS remains a separate validation step unless `--with-ats` is explicitly set.
- Cleaned `validate-ats` command interface to expose only ATS-relevant options (removed unrelated render flags from help/usage).
- Updated `cv-pdf` command to support engine selection (`--via latex|docx`, default `docx`) and DOCX template options.
- Added DOCX template flexibility: built-in style variants (`classic`, `modern`) plus optional external `.docx` base templates via `--docx-template-path`.
- Added in-depth ATS checker documentation at `docs/cv/ats_checker_deep_dive.md` and aligned ATS guidelines with current CLI/report behavior.
- Refreshed repository/module documentation (`README.md`, `data/README.md`, `src/cli/README.md`, `src/cv_generator/README.md`, `docs/pipeline/end_to_end_pipeline_deep_dive.md`) to match current command surface and artifacts.
- Updated root/module documentation (`README.md`, `src/cli/README.md`, `src/cv_generator/README.md`) to reflect current CLI commands and PDF-first workflow.
- Updated documentation recommendations to ATS-first CV flow (`--via docx` + `cv-validate-ats --ats-target pdf`) while keeping LaTeX as fallback.
- Added deep-dive pipeline architecture and operations documentation at `docs/pipeline/end_to_end_pipeline_deep_dive.md`, covering CLI stages, data contracts, CV/ATS flow, and known gaps.
- Extended unified CLI `src/cli/pipeline.py` with CV lifecycle commands: `cv-render`, `cv-build`, `cv-validate-ats`, and `cv-pdf` (PDF-first build + ATS validation).
- Updated CV ATS validation CLI to support target artifact selection via `--ats-target docx|pdf` (default `pdf`) so final ATS can run against PDF output.
- Hardened LaTeX build handling to accept non-zero `pdflatex` exits when a valid PDF is still produced.
- Extracted a lightweight deterministic ATS evaluator into `src/ats_tester/deterministic_evaluator.py` and exposed it via `src/ats_tester/__init__.py`.
- Switched CV ATS code-engine integration to the deterministic evaluator in `src/cv_generator/ats.py`.
- Added parity validation in `validate-ats` to compare `data/pipelined_data/<source>/<job_id>/cv/to_render.md` against rendered DOCX text and PDF text (when available), persisted under `content_parity` in the ATS report.
- Refactored DOCX header rendering in `src/render/docx.py` to ATS-safe single-column paragraphs (removed table-based header), preserved canonical section labels (`SUMMARY`, `EXPERIENCE`, `EDUCATION`, `SKILLS`, `PUBLICATIONS`, `LANGUAGES`), and improved styling for readability.
- Removed legacy ATS tester backend code under `src/ats_tester/backend/` that was not part of the current CV pipeline flow.

## 2026-02-28

- Refactored `src/cv_generator/compile` to use canonical profile input from `data/reference_data/profile/base_profile/profile_base_data.json`.
- Redirected CV generator outputs to job-scoped pipeline paths: `data/pipelined_data/<source>/<job_id>/cv/rendered/`.
- Added `src/cv_generator/config.py` to centralize project, profile, and pipeline path resolution.
- Added `src/cv_generator/loaders/profile_loader.py` to isolate canonical profile loading.
- Updated CV CLI to support renderer selection via `--format` (`docx` default, `latex` optional) and pipeline scoping via `--job-id` and `--source`.
- Extended `src/cv_generator/renderer.py` to support broader DOCX section rendering (education, publications, languages, skills) and removed absolute default photo path usage.
- Added `src/cv_generator/ats.py` and integrated ATS reporting into DOCX flow (`render`/`build`) with explicit `validate-ats` command.
- ATS reports now persist to `data/pipelined_data/<source>/<job_id>/cv/ats/report.json`, with optional job-description matching from pipeline job files.
- Upgraded ATS reporting to a dual-engine model: code-based parser/readability scoring plus LLM-based semantic scoring, combined into one weighted final score.
- Wired LLM ATS prompts to canonical prompt file `data/reference_data/prompts/Academic_ATS_Prompt_Architecture.txt` with optional CLI override.
- Added CLI ATS controls: `--ats-mode fallback|strict` and `--ats-prompt`.
- Updated `src/cv_generator/pipeline.py` sample bootstrapping to use `CVConfig` paths instead of hardcoded absolute paths.
- Updated `src/cv_generator/README.md` to document canonical source paths, pipelined outputs, and ATS-prioritized DOCX workflow.
- Added architecture and migration planning documentation at `docs/plan/cv_generator_architecture_and_remaining_work.md` with current module logic, data contracts, remaining work, and open risks.

## 2026-02-27

- Added `.gitignore` covering Python caches, LaTeX build artifacts, OS files, and Obsidian config.
- Removed `__pycache__/` directories from `src/cli/`, `src/scraper/`, and `src/utils/`.
- Removed LaTeX build artifacts (`main.aux`, `.log`, `.out`) from `src/cv_generator/DHIK_filled/`.
- Deleted stale `data/pipelined_data/tu_berlin/_source_listing/` (duplicated listing HTML).
- Deduplicated PROFILE files: removed copies from `data/reference_data/profile/`, keeping `docs/PROFILE.md` and `docs/PROFILE.json` as the single source of truth.
- Consolidated 7 CV JSON variants into a single canonical `src/cv_generator/src/data/profile.json` (v2.0) with multilingual content (EN/DE/ES) and explicit `technologies` arrays on every experience, education, and project entry.
- Archived superseded JSON files to `src/cv_generator/src/data/archive/`.
- Updated `docs/PROFILE.md` source-of-truth references to point to `profile.json`.
- Updated `README.md` structure diagram and profile metadata docs.

## 2026-02-26

- Added root `README.md` with architecture overview, workflow documentation, script map, dependency notes, and an in-depth repository review.
- Added `docs/AGENT_ENTRYPOINT.md` defining execution rules, constraints, defaults, and playbooks for automation agents.
- Added `docs/PROFILE.md` as a machine-friendly, human-readable canonical identity/profile record with open questions and default preferences.
- Expanded `docs/PROFILE.md` with data from `/home/jp/buscapega`, including richer experience/skills, Chancenkarte visa status, relocation preferences, and a structured job-summary snapshot with identified parser data gaps.
- Added `data/base_profile/` with imported base profile snapshots and explicit job-summary gap records (no inferred salary/duration values).
- Added `docs/PROFILE.json` as strict JSON export for machine consumption.
- Updated scraper field mapping (`fetch_all_filtered_jobs.py`, `fetch_and_parse_all.py`, `generate_populated_tracker.py`) to parse German labels like `Dauer`, `Vergütung`, and `Kennziffer` instead of leaving avoidable `Unknown` values.
- Validated and fixed `docs/PROFILE.md` YAML machine-parseability after manual edits by removing inline HTML comments and converting ambiguous notes into structured fields/open questions.
- Added referee-ready recommendation proposal drafts for academic and professional references, plus email request templates in `Applications_Tracker/Templates/`.
- Differentiated recommendation proposal tone/style by audience: academic draft now research-rigor oriented; professional draft now outcome/execution oriented.
- Enhanced scraper outputs to preserve proposal text integrity: generated per-job `proposal_text.md`, added verbatim posting sections to tracker markdowns, and introduced `summary_detailed.csv` with full requirements/responsibilities text.
- Improved matching quality in scraper-generated tracker pages by adding rule-based auto-detected match reasons (including Airflow/workflow orchestration), inspired by `postulator3000` skill-matching patterns.
- Added a tailored motivation letter draft for TU Berlin Job Posting III-51/26 in `Applications_Tracker/Jobs/TU_Berlin_201084_motivation_letter.md`.
- Added `src/utils/build_backup_compendium.py` to mirror critical assets into normalized backup paths (`data/general_data`, `data/website`) and generate `data/backup_compendium.json` with file checksums.
- Added `docs/data/backup_compendium.md` and `src/utils/README.md` documenting the backup layout, canonical CV location, and refresh commands.
- Updated root `README.md` to include the normalized backup structure and compendium refresh command.
- Migrated repository layout away from `Applications_Tracker/` into canonical domains: `data/pipelined_data` (job pipeline artifacts) and `data/reference_data` (templates, profile snapshots, archives, and supporting assets).
- Moved operational docs to `docs/applications/` (`TODO.md` and `Documentation_Checklist.md`) and updated agent guidance/docs references accordingly.
- Refactored scraper and translation scripts to use `data/pipelined_data/tu_berlin/<job_id>/...` outputs (`raw.html`, `proposal_text.md`, `summary.json`, `job.md`, optional `motivation_letter.md`).
- Reworked `src/utils/build_backup_compendium.py` to generate checksum manifests for the new data layout at `data/reference_data/backup/backup_compendium.json`.
- Updated `README.md` to document the canonical two-category data model and job-centric pipeline path convention.
- Updated `docs/applications/Documentation_Checklist.md` to reference canonical local document paths under `data/reference_data/application_assets` and current job artifact locations.
- Updated `docs/PROFILE.md` supporting file paths to local canonical reference-data copies.
- Added a unified CLI at `src/cli/pipeline.py` with explicit stages (`run`, `fetch`, `translate`, `regenerate`, `backup`, `status`, `validate`) for a clear, repeatable pipeline.
- Added `src/cli/README.md` and updated `README.md`, `data/README.md`, and `docs/AGENT_ENTRYPOINT.md` to document CLI-first pipeline usage.
- Extended CLI with `cv-tailor <job_id>` to generate per-job CV tailoring guidance at `data/pipelined_data/tu_berlin/<job_id>/cv_tailoring.md`.
- Added a dedicated TU Berlin III-51/26 CV variant (`src/cv_generator/main_tu_berlin_201084.tex`, `src/cv_generator/Txt/1-CV-body_tu_berlin_201084.tex`) and linked usage notes under `data/pipelined_data/tu_berlin/201084/cv_tailoring.md`.
- Built and stored tailored CV output for III-51/26 at `data/pipelined_data/tu_berlin/201084/CV_TU_Berlin_201084.pdf`, and marked the job checklist CV item complete.
- Added a pre-PDF markdown CV draft aligned with the updated motivation letter at `data/pipelined_data/tu_berlin/201084/cv_content_preview.md`.
- Migrated tailored CV source files into the job pipeline folder (`data/pipelined_data/tu_berlin/201084/CV_TU_Berlin_201084*.tex`) and updated `src/cli/pipeline.py` so `cv-tailor` writes TeX assets directly under each job directory.
- Copied the CV generator framework from `/home/jp/buscapega/Pega` into `src/cv_generator/`, including the standalone `compile` workflow, JSON/template engine, and LaTeX assets.
- Updated `src/cli/pipeline.py` so `cv-tailor` writes/refreshes TeX sources in `data/pipelined_data/tu_berlin/<job_id>/latex/` (instead of scattering files), and made generation idempotent by rewriting sources each run.
