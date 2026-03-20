# Current Architecture Analysis

Date: 2026-03-02

This document is a ground-truth analysis of the current codebase architecture: what exists, how it's connected, what's dead, and where the pain points are. It's written to inform a redesign, not to prescribe one.

## 1) Source Tree Map

```
src/
  cli/
    pipeline.py          # 2149 lines — THE monolith. All commands live here.
  cv_generator/
    __main__.py           # 837 lines — CV sub-CLI (render/build/ats/template-test)
    config.py             # CVConfig dataclass — path resolution authority
    model.py              # CV data model
    ats.py                # Dual ATS engine (code 0.6 + LLM 0.4)
    pipeline.py           # 567 lines — CVTailoringPipeline + MatchProposalPipeline classes
    loaders/              # profile_loader.py
    renderer.py           # LEGACY — table-based 2-column header, NOT ATS-safe
    styles.py             # LEGACY — duplicate of src/render/styles.py
    compile               # LEGACY — old CLI wrapper
    Code/, DHIK_filled/, Txt/, src/  # LEGACY data directories inside code tree
  motivation_letter/
    service.py            # 453 lines — MotivationLetterService (context/generate/pdf/email)
  agent/
    orchestrator.py       # 184 lines — ApplicationAgent (Gemini-based batch orchestrator)
    tools.py              # 463 lines — tool functions for agent (scrape/fit/tailor/render/ats/motivation)
  scraper/
    scrape_single_url.py  # 481 lines — deterministic single-URL fetch+parse
    fetch_listing.py      # 124 lines — paginated listing crawler
    generate_populated_tracker.py  # 304 lines — rebuild job.md from raw HTML
    fetch_jobs.sh         # Shell script wrapper (legacy?)
  render/
    docx.py               # DocumentRenderer — ATS-safe DOCX (primary path)
    latex.py               # Jinja2 → .tex rendering
    pdf.py                 # PDF text extraction
    styles.py              # CVStyles, CVStylesModern, CVStylesHarvard, CVStylesExecutive
    templates/             # LaTeX templates
    assets/                # Rendering assets
  models/
    job.py                 # JobRequirement, JobPosting
    application.py         # FitAnalysis, ApplicationPlan, ApplicationBatch
    motivation.py          # FitSignal, MotivationLetterOutput, EmailDraftOutput
    pipeline_contract.py   # EvidenceItem, RequirementMapping, PipelineState, etc.
  prompts/
    cv_renderer.txt
    cv_multi_agent.txt
    motivation_letter.txt
    email_draft.txt
    ats_evaluation.txt
  utils/
    gemini.py              # GeminiClient — shared LLM transport
    loader.py              # Generic data loading helpers
    pdf_merger.py          # PDF merge + Ghostscript compression
    build_backup_compendium.py  # Backup manifest builder
    nlp/                   # Text analysis (used by ATS)
  ats_tester/
    deterministic_evaluator.py  # DeterministicContentEvaluator
    backend/, frontend/    # Leftover web app scaffolding (has own .git!)
  build_word_cv.py         # LEGACY — hardcoded DOCX builder at src root
```

## 2) The Monolith: `src/cli/pipeline.py`

**2149 lines. 27 subcommands. Zero separation of concerns.**

This file is simultaneously:
- An argparse CLI definition (540 lines of parser setup)
- A command router (`main()` — 230 lines of if/elif chain)
- A job ingestion orchestrator (`run_fetch`, `run_fetch_url`, `run_fetch_listing`)
- A CV lifecycle manager (`run_cv_render`, `run_cv_build`, `run_cv_pdf_pipeline`, etc.)
- A motivation letter orchestrator (`run_motivation_build`)
- An application staging system (`run_app_prepare`, `run_app_review`, `run_app_renderize`, `run_app_run`)
- A match pipeline driver (`run_match_propose`, `run_match_approve`)
- A batch operations hub (`run_apply_to`, `run_archive_passed`)
- A global index builder (`run_jobs_index`)
- A status/validation reporter (`print_pipeline_status`, `collect_pipeline_stats`)
- A utility library (path helpers, state management, comment collection)

### 2.1 Command Surface (27 commands, grouped by actual domain)

**Job Ingestion (batch/global)**
| Command | What it does |
|---------|-------------|
| `run` | Multi-stage orchestrator: fetch → regenerate → backup → validate |
| `fetch` | Run fetch strategy (listing/filtered/fixed) |
| `fetch-url` | Deterministic URL-targeted ingestion |
| `fetch-listing` | Crawl filtered listing, paginate, scrape new jobs |
| `regenerate` | Rebuild job.md from existing raw HTML |
| `translate` | **DEAD** — deprecated no-op, prints warning |

**CV Lifecycle (single-job)**
| Command | What it does |
|---------|-------------|
| `cv-tailor` | Generate tailoring brief via CVTailoringPipeline |
| `cv-render` | Render CV via cv_generator sub-CLI |
| `cv-build` | Build CV via cv_generator sub-CLI |
| `cv-validate-ats` | Run ATS validation on rendered CV |
| `cv-pdf` | cv-build + cv-validate-ats combined |
| `cv-template-test` | Build + deterministic parity score |

**Matching (single-job)**
| Command | What it does |
|---------|-------------|
| `match-propose` | Generate requirement-to-evidence proposal |
| `match-approve` | Parse reviewed proposal, lock reviewed_mapping.json |

**Motivation Letter (single-job)**
| Command | What it does |
|---------|-------------|
| `motivation-build` | Generate final motivation letter + PDF + email |
| legacy motivation command | **BROKEN** — referenced in main() routing but function doesn't exist, parser not defined |

**Application Lifecycle (single-job)**
| Command | What it does |
|---------|-------------|
| `app-prepare` | Stage prep artifacts + ATS pre-analysis |
| `app-review` | Collect unresolved HTML comments |
| `app-status` | Show staged workflow status (read-only) |
| `app-renderize` | Render final artifacts (requires zero comments) |
| `app-run` | prepare → review → renderize combined |

**Batch/Agent Orchestration**
| Command | What it does |
|---------|-------------|
| `apply-to` | Agent-driven: scrape URLs → fit analysis → generate everything |

**Global/Admin**
| Command | What it does |
|---------|-------------|
| `backup` | Rebuild backup compendium |
| `jobs-index` | Generate central job_id index |
| `archive-passed` | Move expired jobs to archive |
| `status` | Pipeline health summary (read-only) |
| `validate` | Same as status but with exit code |

## 3) The Second Entrypoint: `src/cv_generator/__main__.py`

This is a parallel CLI that `pipeline.py` delegates to via `run_cv_command()` (subprocess call). It has its own command set:
- `status`, `render`, `build`, `validate-ats`, `test-template`

It owns the actual CV rendering logic: loading profile, building markdown, calling renderers, running ATS. But `pipeline.py` wraps every one of its commands with thin delegation functions.

**Problem:** Two CLIs for the same domain. pipeline.py adds no logic — it just reformats args and calls subprocess.

## 4) The Third Entrypoint: `src/agent/orchestrator.py`

`ApplicationAgent` is a Gemini function-calling agent that uses tools from `src/agent/tools.py`. These tools directly call into:
- `scrape_single_url.run_for_url()` — scraping
- `CVTailoringPipeline.execute()` — CV tailoring
- `MotivationLetterService` methods — motivation
- `run_cv_command()` — CV rendering (subprocess)
- `pdf_merger` — packaging

This is a parallel orchestration path that bypasses the CLI entirely.

## 5) Cross-Cutting Concerns Found Inside pipeline.py

These utility functions are defined inside `pipeline.py` but are not CLI-specific:

- `get_pipeline_root_for_source()`, `get_job_dir()`, `get_app_dirs()`, `ensure_app_dirs()` — path resolution
- `copy_into()`, `append_state_entry()`, `parse_state_entries()` — state management
- `write_prep_instructions()`, `collect_prep_comments()`, `write_review_comments()` — comment workflow
- `write_json_report()` — report writing
- `_list_numeric_job_dirs()`, `build_jobs_inventory()` — directory scanning
- `parse_deadline_date()`, `read_job_deadline()` — date parsing

These should be library functions, not embedded in a CLI file.

## 6) Dependency Graph (who calls whom)

```
pipeline.py (CLI)
  ├── src/scraper/scrape_single_url.py     (direct import: run_for_url)
  ├── src/scraper/fetch_listing.py         (direct import: crawl_listing)
  ├── src/scraper/generate_populated_tracker.py  (subprocess)
  ├── src/cv_generator/__main__.py         (subprocess via run_cv_command)
  ├── src/cv_generator/pipeline.py         (direct import: CVTailoringPipeline, MatchProposalPipeline)
  ├── src/motivation_letter/service.py     (direct import: MotivationLetterService)
  ├── src/agent/orchestrator.py            (direct import: ApplicationAgent)
  ├── src/utils/build_backup_compendium.py (subprocess)
  └── src/utils/pdf_merger.py              (direct import)

src/agent/tools.py
  ├── src/scraper/scrape_single_url.py
  ├── src/cv_generator/pipeline.py
  ├── src/cv_generator/__main__.py         (subprocess)
  ├── src/motivation_letter/service.py
  └── src/utils/pdf_merger.py

src/cv_generator/__main__.py
  ├── src/cv_generator/config.py
  ├── src/cv_generator/model.py
  ├── src/cv_generator/ats.py
  ├── src/render/docx.py
  ├── src/render/latex.py
  └── src/render/pdf.py
```

## 7) Dead Code and Ghosts

| Item | Status | Evidence |
|------|--------|---------|
| legacy motivation command | **Broken** | Referenced in `main()` routing but missing function and parser wiring |
| `translate` command | **Dead no-op** | Prints deprecation warning, does nothing |
| `src/cv_generator/renderer.py` | **Legacy** | Table-based header, not ATS-safe. Superseded by `src/render/docx.py` |
| `src/cv_generator/styles.py` | **Legacy** | Duplicate of `src/render/styles.py` |
| `src/cv_generator/compile` | **Legacy** | Old CLI wrapper, not wired to pipeline |
| `src/cv_generator/Code/`, `DHIK_filled/`, `Txt/`, `src/` | **Legacy data** | Data directories inside code tree |
| `src/build_word_cv.py` | **Legacy** | Hardcoded DOCX builder at src root |
| `src/ats_tester/backend/`, `frontend/`, `.git` | **Orphaned** | Web app scaffolding with its own git repo inside the project |
| `src/scraper/fetch_jobs.sh` | **Unclear** | Shell wrapper, may be legacy |

## 8) Identified Pain Points

### 8.1 The monolith naming problem
The main entrypoint is `src/cli/pipeline.py` but the root package is `src/cv_generator/`. Someone looking at this repo sees "cv_generator" as the primary module — it's misleading. The tool manages **applications** (scraping, matching, CV, motivation, packaging), not just CVs.

### 8.2 No domain boundaries
All 27 commands share one file, one namespace, one set of imports. A change to motivation letter logic can break CV rendering through shared state or import errors. There's no way to test or reason about one domain without loading everything.

### 8.3 Three parallel orchestration paths
1. `pipeline.py` CLI — the intended path
2. `cv_generator/__main__.py` — parallel CV CLI (called by pipeline.py via subprocess)
3. `agent/orchestrator.py` — Gemini-driven agent path

These overlap significantly and can diverge silently.

### 8.4 Mixed abstraction levels in pipeline.py
The same file contains:
- High-level orchestration (`run` → fetch → regenerate → backup → validate)
- Mid-level domain logic (application staging, comment collection)
- Low-level utilities (path resolution, date parsing, state serialization)

### 8.5 CV lifecycle is scattered
To understand CV rendering you need to read:
- `pipeline.py` (CLI wrappers) → calls subprocess →
- `cv_generator/__main__.py` (routing + logic) → calls →
- `cv_generator/config.py` + `model.py` (data) + `render/docx.py` or `render/latex.py` (output)
- `cv_generator/pipeline.py` (tailoring, which is a separate concern from rendering)
- `cv_generator/ats.py` (validation, also separate)

"CV generator" conflates four distinct concerns: tailoring, rendering, building (render+convert), and ATS validation.

### 8.6 Motivation letter is self-contained but under-connected
`MotivationLetterService` is well-structured internally (453 lines, clean API). But it's connected to the pipeline through:
- `pipeline.py` → `run_motivation_build()` (thin wrapper)
- `agent/tools.py` → `write_motivation_letter()` (another thin wrapper)
- `pipeline.py` → `run_app_prepare/renderize()` (third integration point)

Three integration surfaces for one service.

### 8.7 Matching lives in the wrong package
`CVTailoringPipeline` and `MatchProposalPipeline` are in `src/cv_generator/pipeline.py`. But matching requirements to evidence is not a CV concern — it's an application-level concern that feeds into both CV tailoring and motivation letter writing.

### 8.8 The agent system is disconnected
`src/agent/` (orchestrator + tools) duplicates logic that exists in the CLI pipeline. Both paths can scrape, tailor, render, and build — with slightly different behavior. The tools in `agent/tools.py` are essentially a parallel API to pipeline.py commands.

## 9) What Actually Works Well

- **`src/render/`** — Clean, focused module. Renderers (docx, latex) are well-separated from routing.
- **`src/models/`** — Pydantic/dataclass contracts are clean and useful.
- **`src/utils/gemini.py`** — Single LLM transport, shared correctly.
- **`src/motivation_letter/service.py`** — Self-contained service with clear API.
- **`src/scraper/scrape_single_url.py`** — Deterministic, well-structured single-job scraper.
- **Data layout** — The per-job directory contract (`raw/`, `planning/`, `cv/`, `output/`) is good.
- **ATS dual-engine** — Code + LLM evaluation with weighted merge is a solid design.

## 10) Size Summary

| File | Lines | Role |
|------|-------|------|
| `src/cli/pipeline.py` | 2149 | CLI monolith |
| `src/cv_generator/__main__.py` | 837 | CV sub-CLI + logic |
| `src/cv_generator/pipeline.py` | 567 | Tailoring + matching pipelines |
| `src/scraper/scrape_single_url.py` | 481 | Single-URL scraper |
| `src/agent/tools.py` | 463 | Agent tool functions |
| `src/motivation_letter/service.py` | 453 | Motivation letter service |
| `src/scraper/generate_populated_tracker.py` | 304 | Tracker regeneration |
| `src/agent/orchestrator.py` | 184 | Agent orchestrator |
| `src/scraper/fetch_listing.py` | 124 | Listing crawler |
| **Total key files** | **~5,562** | |

## 11) Conceptual Domain Map

Reading the code, there are really **five distinct operational domains**:

1. **Ingestion** — Scrape job postings, parse, create job directory structure
2. **Matching** — Map job requirements to candidate evidence (currently in cv_generator/pipeline.py)
3. **CV** — Tailor profile → render DOCX/LaTeX → convert to PDF → ATS validate
4. **Motivation** — Build context → generate letter → render PDF → draft email
5. **Packaging** — Stage, review, finalize, merge PDFs for submission

Plus two cross-cutting concerns:
- **Admin/Batch** — Index, archive, backup, batch operations
- **Agent** — LLM-driven orchestration across all domains

These domains are currently **not reflected in the code structure**. Instead, everything funnels through `pipeline.py` and `cv_generator/`.
