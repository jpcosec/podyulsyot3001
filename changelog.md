# Changelog

## 2026-03-03 — LangGraph Migration Hard-Cut Steps (No `run` Fallback)

- Updated migration plans in `docs/plans/2026-03-03-langgraph-pipeline/` to enforce hard cutover semantics:
  - `pipeline job <id> run` as graph-first path
  - explicit removal of `run --legacy` fallback after tagged cutover
  - mandatory refactors: keyword-domain split and pipeline-domain decomposition
- Split keyword extraction out of `src/steps/matching.py` into dedicated module `src/steps/keywords.py`.
- Split mixed domains from `src/utils/pipeline.py` into focused `src/graph/` modules:
  - parsers: `src/graph/parsers/{proposal_parser.py,claim_builder.py}`
  - agent runtime: `src/graph/agents/base.py`
  - pipelines: `src/graph/pipelines/{tailoring.py,matching.py}`
  - `src/utils/pipeline.py` now serves as compatibility shim re-exporting legacy symbols.
- Added real LangGraph `StateGraph` coordinator in `src/graph/pipeline.py` and routed `pipeline job <id> run` through it:
  - interrupt behavior at review gate when `planning/reviewed_mapping.json` is missing
  - resume path via `pipeline job <id> run --resume`
  - automatic review lock on resume (invokes matching approval step)
  - `pipeline job <id> graph-status` for checkpoint inspection
- Added LangGraph runtime dependencies to `environment.yml` (`langgraph`, `langgraph-checkpoint-sqlite`) and ignored runtime checkpoint files via `**/.graph/`.
- Updated CLI and maintainer docs to reflect graph run/resume flow:
  - `src/cli/README.md`
  - `CLAUDE.md`

## 2026-03-03 — Match Proposal Review Regeneration Loop

- Added iterative match-proposal regeneration behavior in `src/utils/pipeline.py`:
  - Previous proposal is now passed back as revision context with parsed reviewed claims and inline user comments.
  - Regeneration directives enforce: keep approved claims stable, remove rejected claims, and regenerate edited evidence.
  - Existing `planning/match_proposal.md` is archived automatically as `planning/match_proposal.roundN.md` before writing the new round.
  - Evidence IDs are revalidated against current evidence items to avoid stale references in regenerated proposals.
- Relaxed decision parsing in `src/utils/pipeline.py` to accept non-strict checkbox formatting (for example `[ x]`, `[x ]`, `x[ ]`).
- Updated matching step behavior in `src/steps/matching.py`:
  - Comments are logged before matcher execution so feedback is not lost on failures.
  - `match-approve` now logs extracted proposal comments as part of the review loop.
  - Regenerating `match` invalidates stale `planning/reviewed_mapping.json`, forcing explicit re-approval.
- Expanded tests in `tests/steps/test_matching.py`:
  - Flexible checkbox parsing coverage.
  - Proposal comment logging coverage in `match-approve`.
  - Stale reviewed-mapping invalidation on regeneration.
  - Round-archive naming behavior (`match_proposal.roundN.md`).
- Added loop documentation at `docs/pipeline/match_review_regeneration_loop.md` and linked it from `src/cli/README.md`.

## 2026-03-03 — Remove English-Only Ingestion Filter

- Removed strict-English filtering from ingestion runtime; job scraping now always ingests and records language metadata only.
- Updated scraper interfaces to drop `strict_english` parameters:
  - `src/scraper/scrape_single_url.py` (`run_for_url`, CLI parser)
  - `src/scraper/fetch_listing.py` (`crawl_listing`)
  - `src/steps/ingestion.py` (`run`, `run_from_url`, `run_from_listing`)
- Removed `--strict-english` option from unified CLI ingestion commands in `src/cli/pipeline.py`.
- Updated `src/agent/tools.py` to use the new ingestion signature.
- Fixed `ingest-url` handler in `src/cli/pipeline.py` to call `run_for_url` per URL.
- Unified translation behavior between fresh ingest and regenerate flows by introducing shared source-text normalization in `src/scraper/scrape_single_url.py` (`normalize_source_text_to_english`).
- Added explicit language verification for `/en/job-postings/<id>` fetches before accepting them; fallback remains line-level translation when `/en` content is still non-English.
- Reused the same normalization logic in `src/scraper/generate_populated_tracker.py` to keep regeneration consistent with normal ingestion.
- Updated `pipeline jobs --category` in `src/cli/pipeline.py` to filter by posting metadata category (job header/frontmatter) instead of matching-derived `planning/keywords.json` categories.
- Added explicit job-query aliases in `src/cli/pipeline.py`: `--filter-by-keyword` / `--filterbykeyword` and `--filter-by-property` / `--filterbyproperty` (`KEY=VALUE`) for Obsidian-property-driven filtering.
- Added marker-driven archiving in `src/cli/pipeline.py`: `pipeline archive --marked` now archives open jobs tagged in `job.md` frontmatter (e.g., `archive: true`, `status: archived`, or `tags: [archive]`).
- Implemented `pipeline index` to rebuild `summary.csv` and `summary_detailed.csv` with pipeline status (`open`/`archived`), and wired archive operations to refresh the index after archiving.
- Enhanced property filtering to read Obsidian frontmatter values (including list tags), so `pipeline jobs --filter-by-property "tags=..."` works directly on `job.md` markers.
- Extended rebuilt index output to include tag markers (`Tags` column in `summary_detailed.csv`, tags appended in `summary.csv` facts).
- Added marker-driven execution command `pipeline run-marked` to gather jobs by frontmatter tags (default `continue,yes`) and run either the next step or all remaining steps.
- Enforced canonical progression with approval gate for automated runs (`ingest -> match -> match-approve -> motivate -> tailor-cv -> draft-email -> render -> package`).
- Updated related tests and CLI docs:
  - `tests/cli/test_pipeline.py`
  - `tests/steps/test_ingestion.py`
  - `tests/scraper/test_fetch_listing.py`
  - `src/cli/README.md`

## 2026-03-02 — Pipeline Redesign Phase 6: Motivation and Email-Draft Steps

- Added `src/steps/motivation.py` with `run()` function that wraps `MotivationLetterService.generate_for_job()`
  - Reads: job.md, planning/reviewed_mapping.json, profile data, comments from previous outputs
  - Produces: planning/motivation_letter.md (rendered letter), planning/motivation_letter.json (structured output)
  - Implements StepResult protocol with comment extraction and logging via `append_to_comment_log()`
  - Returns error if reviewed_mapping.json missing (requires 'match-approve' to run first)
  - Force re-run support for iterative refinement
- Added `src/steps/email_draft.py` with `run()` function that wraps `MotivationLetterService.generate_email_draft()`
  - Reads: planning/motivation_letter.json, job.md, comments from previous outputs
  - Produces: planning/application_email.md (email draft with To, Subject, body, closing, sender info)
  - Implements StepResult protocol with comment extraction and logging
  - Returns error if motivation_letter.json missing (requires 'motivate' to run first)
  - Force re-run support for iteration
- Both steps extract comments from previous outputs and input files for iterative refinement via `extract_comments()`
- Both steps log extracted comments to `.metadata/comments.jsonl` via `append_to_comment_log()`
- MotivationLetterService in `src/motivation_letter/service.py` remains unchanged — steps are thin wrappers
- Added comprehensive test suites:
  - `tests/steps/test_motivation.py`: 5 tests covering artifact production, completion skip, force re-run, missing input errors, comment reading
  - `tests/steps/test_email_draft.py`: 5 tests covering email generation, completion skip, missing input errors, force re-run, content verification
- All tests passing; motivation and email-draft steps ready for integration into CLI dispatch
- Phase 6 complete; next: Phase 7 (CV tailoring step)

## 2026-03-02 — Pipeline Redesign Phase 4: Ingestion Step

- Added `src/steps/ingestion.py` with three entry points for job scraping and ingestion:
  - `run(state, *, force=False, url=None, strict_english=True)` — Main step function following the StepResult protocol
  - `run_from_url(url, source="tu_berlin", *, strict_english=True)` — Ingest a single job from URL
  - `run_from_listing(listing_url, source="tu_berlin", *, strict_english=True, delay=0.5)` — Crawl and ingest all jobs from a listing page
- Wraps existing scraper modules (`src/scraper/scrape_single_url.py`, `src/scraper/fetch_listing.py`, `src/scraper/generate_populated_tracker.py`) without duplicating logic
- Uses `JobState` for path resolution and artifact management (via `state.artifact_path()` and `state.write_artifact()`)
- Produces exactly the STEP_OUTPUTS["ingestion"] contract: `raw/raw.html`, `raw/source_text.md`, `raw/extracted.json`, `job.md`
- Implements three ingestion patterns: fresh scrape (if URL provided), regeneration from cached raw HTML, or error if neither available
- Added comprehensive test suite (`tests/steps/test_ingestion.py`) with 18 tests covering all three functions, error handling, force re-runs, parameter passing, and URL parsing
- All tests passing; ingestion step ready for integration into CLI dispatch
- Created `src/steps/__init__.py` with `StepResult` dataclass and STEPS registry (if not already present from Phase 3)

## 2026-03-02 — Pipeline Redesign Phase 2: Comment System

- Added `src/utils/comments.py` with comment extraction and logging system for iterative feedback
- Implemented `InlineComment` and `CommentLogEntry` dataclasses for structured comment tracking
- `extract_comments()` extracts all `<!-- ... -->` HTML comments from markdown files with line numbers and context
- `extract_comments_from_files()` provides batch extraction with relative path support via job_dir parameter
- `load_comment_log()` and `append_to_comment_log()` handle JSON persistence with graceful error handling
- `format_comments_for_prompt()` converts comments to human-readable text blocks suitable for LLM injection
- Regex uses `re.DOTALL` to properly handle multiline comments
- Added comprehensive test suite (`tests/utils/test_comments.py`) with 22 tests covering extraction, logging, formatting, and edge cases
- All tests passing; ready for Phase 3 (steps package protocol)

## 2026-03-02 — Incremental Pipeline Fix: Code Review Fixes

- **Motivation guard:** `motivation-build` now requires approved mapping (`match-approve`) before generating letters; raises ValueError if mapping exists but isn't approved
- **Scraper full-text output:** `render_tracker_markdown()` now uses full posting body as primary output, with raw markdown fallback; filtered checklists only as last resort
- **Cleaned up `_format_insights`:** Removed hardcoded reference to dev artifact file "motivation_letter copy.md"
- **ATS default mode:** Changed default `ats_mode` from "fallback" to "combined"
- **`match-approve` regex parser:** Now accepts both `req_N` and `RN` heading formats for flexibility
- **Command/mutation audit doc:** Added `docs/pipeline/command_surface_and_mutation_audit.md` with full command inventory, mutation boundaries, runfile audit, and architecture constraints for single-job-first + explicit batch orchestration.

## 2026-03-02 — Incremental Pipeline Plan Implementation (Phase 1)

- Updated CV rendering inputs to honor reviewer intent for equivalency and Walmart scope: `data/reference_data/profile/base_profile/profile_base_data.json` now includes Walmart achievements, `src/cv_generator/__main__.py` now emits education equivalency notes into `cv/to_render.md`, and `src/render/docx.py` now renders education equivalency notes in DOCX output.
- Implemented full-posting tracker output in `src/scraper/scrape_single_url.py`: `job.md` now keeps YAML frontmatter but uses the full extracted posting body (with structured-checklist fallback only when full body is unavailable).
- Replaced legacy fetch/translation script wiring in `src/cli/pipeline.py` with the unified deterministic flow (`fetch_listing.py` + `scrape_single_url.py`), keeping translation command as explicit no-op compatibility.
- Removed legacy scraper scripts: `src/scraper/fetch_all_filtered_jobs.py`, `src/scraper/fetch_and_parse_all.py`, `src/scraper/generate_tracker.py`, `src/scraper/deterministic_extraction.py`, `src/scraper/translate_markdowns.py`, and `src/scraper/deep_translate_jobs.py`.
- Added reviewed-mapping contracts in `src/models/pipeline_contract.py` (`ReviewedClaim`, `ReviewedMapping`) and a new proposal workflow in `src/cv_generator/pipeline.py` (`MatchProposalPipeline`, `parse_reviewed_proposal`).
- Extended CLI with `match-propose` and `match-approve` in `src/cli/pipeline.py` to support human-in-the-loop claim review and locking.
- Rebuilt the motivation service module (`src/motivation_letter/service.py`) and restored package exports via `src/motivation_letter/__init__.py`, including letter generation, PDF build, email draft generation, and compatibility helpers.

## 2026-03-02 — Unified Pipeline Rebuild Planning Pack

- Replaced all previous planning documents under `docs/plans/` with a single hard-break rebuild plan pack at `docs/plans/2026-03-02-unified-pipeline-rebuild/`.
- Added plan files covering: master rebuild plan, in-depth analysis of kept codepieces (Gemini caller, prompts, Pydantic contracts, deterministic rendering, deterministic translation/extraction), target LangGraph architecture, unified phase graph, and deletion matrix.
- Removed legacy plan documents that described superseded partial migrations and wrapper-based incremental approaches.

## 2026-03-02 — De-hardcode Pipeline & Agent Architecture

### Added
- `src/models/` — Pydantic models for job postings, pipeline contract, motivation letters, and application plans
- `src/prompts/` — Centralized prompt files with loader utility (moved from data/reference_data/prompts/)
- `src/agent/tools.py` — Tool functions wrapping scraper, renderer, ATS, and motivation services
- `src/agent/orchestrator.py` — `ApplicationAgent` for batch application processing
- `apply-to <urls>` CLI command — guided application workflow with human-in-the-loop checkpoints
- `src/prompts/email_draft.txt` — Agent prompt for email generation

### Changed
- `src/cv_generator/pipeline.py` — Rewritten as `CVTailoringPipeline` using full prompts from files + Pydantic models
- `src/motivation_letter/service.py` — Rebuilt as agent-driven (letter generation + email via LLM)
- `src/cv_generator/ats.py` — Uses `src/prompts/` loader instead of hardcoded path

### Removed
- `CV_RULES` constant from `src/cli/pipeline.py` — replaced by MATCHER agent
- `render_job_cv_body()`, `render_job_cv_main()`, `ensure_job_cv_sources()` — hardcoded LaTeX content
- `build_cv_tailoring()` hardcoded logic — now delegates to `CVTailoringPipeline`
- Hardcoded email draft template from `generate_email_draft()` — replaced by email agent
- `data/reference_data/prompts/AST.md` — duplicate of ATS prompt

## 2026-03-02 — Deterministic Listing Crawler

- Added `src/scraper/fetch_listing.py` with deterministic pagination over filtered TU Berlin listing URLs, helper utilities for listing-page parsing, and deduplication against both active and archived job folders before delegating scraping to `scrape_single_url.run_for_url()`.
- Added `tests/scraper/test_fetch_listing.py` covering listing extraction, known-id collection, page URL building, and `crawl_listing()` behavior with monkeypatched network/scrape calls.
- Extended `src/cli/pipeline.py` with `fetch-listing` command (`url`, `--source`, `--strict-english`, `--delay`) and dispatch wiring, plus parser coverage in `tests/cli/test_pipeline.py`.
- Expanded `jobs-index` inventory reporting to track active vs archived counts, overlap IDs (same job ID present in both), and unique known totals; updated `tests/cli/test_pipeline_review.py` with inventory coverage.
- Enforced English-first scraping defaults for `fetch-url` and `fetch-listing` (strict English enabled by default, optional `--allow-non-english` override).
- Added `archive-passed` CLI command with dry-run by default and `--apply` mode to move expired active jobs into `archive/`, including JSON report output at `data/pipelined_data/archive_passed_report_<source>.json`.
- Hardened motivation generation parsing in `src/motivation_letter/service.py` to tolerate JSON wrapped in extra text/fences for final-letter and email-draft outputs.
- Updated CV pipeline schema and orchestration: `language` is now accepted as an evidence item type in `src/models/pipeline_contract.py`, and seller/checker steps in `src/cv_generator/pipeline.py` can recover missing top-level state fields from prior validated step output.

## 2026-03-02

- Added full motivation subsystem documentation at `docs/pipeline/motivation_letter_system_deep_dive.md`, covering runtime entrypoints, data contracts, method inventory, hardcoded vs prompt-driven boundaries, and a target multi-agent architecture.
- Linked the new motivation deep dive from `docs/pipeline/end_to_end_pipeline_deep_dive.md` for hierarchical navigation from pipeline overview to subsystem internals.

## 2026-03-01 (continued)

- Expanded motivation-letter generation with format-insights integration (strengths to preserve + improvements to apply), dynamically analyzed from `planning/motivation_letter copy.md` when present; added requirement-to-evidence analysis and reusable cross-job evidence bank at `data/reference_data/profile/evidence/evidence_bank.json`, implemented in `src/motivation_letter/service.py` with tests in `tests/motivation_letter/test_service.py`.
- Added motivation pipeline CLI command `motivation-build` in `src/cli/pipeline.py` and parser tests in `tests/cli/test_pipeline.py`.
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
