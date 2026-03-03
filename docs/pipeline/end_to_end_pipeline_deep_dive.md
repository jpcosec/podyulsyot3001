# End-to-End Pipeline Deep Dive

This document describes the full operational pipeline used in this repository, from job ingestion to ATS validation and final PDF packaging.

It is the canonical technical walkthrough for maintainers and automation agents.

> Update (2026-03-03): runtime orchestration is graph-coordinated via `pipeline job <id> run` and `pipeline job <id> run --resume`. Historical command references in this file are retained for migration context.

## 1) System Overview

The workflow has three major lanes:

1. **Job ingestion lane**: fetch, parse, normalize, and track TU Berlin postings.
2. **CV lane**: generate CV artifacts (DOCX/LaTeX/PDF), then run ATS analysis.
3. **Submission lane**: package and compress final PDFs for application upload.

### 1.1 Current graph coordinator

Primary orchestration now runs through `src/graph/pipeline.py`.

Graph flow:

```text
ingest -> match -> review_gate(interrupt) -> motivate -> tailor_cv -> draft_email -> render -> package
```

Review behavior:

- `python src/cli/pipeline.py job <id> run` executes until review lock is needed.
- If `planning/reviewed_mapping.json` is missing, run interrupts at review gate.
- After editing `planning/match_proposal.md`, use `python src/cli/pipeline.py job <id> run --resume`.
- Resume auto-locks reviewed mapping, then continues through downstream nodes.

Primary entrypoint (CLI-first policy):

```bash
python src/cli/pipeline.py <command>
```

## 2) Data Contracts and Layout

### 2.1 Canonical roots

- Runtime/generated: `data/pipelined_data/`
- Static/reference: `data/reference_data/`

### 2.2 Job-scoped contract

Each TU Berlin job is modeled as:

`data/pipelined_data/tu_berlin/<job_id>/`

Sub-zone layout:

```
<job_id>/
  job.md              # application tracker (root, hand-edited)
  raw/                # scraped artifacts — auto-generated, never hand-edited
    raw.html
    proposal_text.md
    summary.json
  planning/           # agent + human authored
    cv_tailoring.md
    cv_content_preview.md
    motivation_letter.md
  cv/
    to_render.md      # canonical render source for parity checks
    rendered/         # generated DOCX / TeX / PDF
    ats/              # report.json, template_test.json
  output/             # final submission PDFs (gitignored)
  build/              # LaTeX scratch (gitignored)
```

Core artifacts validated by `pipeline.py validate`:

- `raw/raw.html`
- `raw/summary.json`
- `job.md`

## 3) Unified CLI Orchestration

Implementation: `src/cli/pipeline.py`

### 3.1 Pipeline commands (jobs/data)

- `run`: multi-stage orchestration (`fetch -> regenerate? -> translate -> backup -> validate`)
- `fetch`: run a single fetch strategy (`filtered` or `fixed`)
- `fetch-url`: deterministic URL-targeted ingestion (`html -> source_text.md -> extracted.json -> job.md`)
- `translate`: run translation only (`rules`, `deep`, `both`)
- `regenerate`: rebuild job tracker markdowns from existing `raw.html`
- `backup`: rebuild backup compendium
- `status`: print pipeline health and missing artifacts
- `validate`: fail when required artifacts are missing

### 3.2 CV and motivation commands

- `cv-render`: render CV via `src.cv_generator` to final PDF (`--via docx|latex`)
- `cv-build`: render/build CV via `src.cv_generator` to final PDF (`--via docx|latex`)
- `cv-validate-ats`: run ATS validation against `docx` or `pdf`
- `cv-pdf`: one-command build + ATS validation (`cv-build` then `cv-validate-ats`), defaulting to `--via docx`
- `cv-template-test`: build CV and compute deterministic parity score (0-100%) against `docx` or `pdf`
- `cv-tailor`: generate job-specific tailoring brief + TeX assets in `<job_id>/latex/`
- `app-prepare`: stage prep artifacts under `<job_id>/output/prep/` and run ATS pre-analysis
- `app-review`: collect unresolved HTML comments (`<!-- ... -->`) from prep artifacts into `<job_id>/output/review/comments.md`
- `app-renderize`: render final CV/motivation artifacts only when review has zero unresolved comments; writes final assets under `<job_id>/output/final/`
- `app-run`: one-command orchestrator for prepare -> review -> renderize (stops at review when unresolved comments exist)
- `app-status`: show current staged workflow status for one job from `<job_id>/output/state.md`
- `jobs-index`: generate central index of job ids by source folder at `data/pipelined_data/job_ids_index.{json,md}`
- `motivation-build`: generate motivation letter content + evidence analysis in `<job_id>/planning/`
- `motivation-build`: generate final motivation letter using prompt bridge insights, then produce `output/motivation_letter.pdf` and `planning/application_email.md` draft

Motivation subsystem full internals (context contracts, prompt boundaries, hardcoded vs agent-driven areas, and target architecture):

- `docs/pipeline/motivation_letter_system_deep_dive.md`

## 4) Job Ingestion Lane

### 4.1 Fetch strategies

1. **Filtered pagination scraper**: `src/scraper/fetch_all_filtered_jobs.py`
   - Crawls filtered TU Berlin listing pages.
   - Discovers job URLs dynamically.
2. **Fixed URL scraper**: `src/scraper/fetch_and_parse_all.py`
   - Uses a hardcoded list of job URLs.

Both strategies produce the same job artifact schema.

### 4.2 Parsing and extraction model

Shared behavior (duplicated across scraper scripts):

- Parse HTML via `BeautifulSoup`.
- Extract facts table values (`reference_number`, `deadline`, `category`, `salary`, `duration`).
- Extract contact email from `mailto:`.
- Detect and split posting sections into:
  - `Requirements` (profile)
  - `Responsibilities` (tasks)
- Convert extracted lines into checklist markdown (`- [ ] ...`).
- Compute heuristic "How I Match" bullets from regex rule hits.

### 4.3 Generated outputs per job

Under `raw/`:
- `raw.html`: fetched posting source
- `proposal_text.md`: verbatim requirement/responsibility extract
- `summary.json`: lightweight structured summary

At job root:
- `job.md`: full tracker page with frontmatter + checklist sections

Plus root-level indexes:

- `data/pipelined_data/tu_berlin/summary.csv`
- `data/pipelined_data/tu_berlin/summary_detailed.csv`

### 4.4 Regeneration mode

`src/scraper/generate_populated_tracker.py` recreates `job.md` and `summary.json` from already downloaded `raw.html`.

Use when scraping is unavailable but local HTML snapshots exist.

## 5) Translation Lane

### 5.1 Rules-first translation

`src/scraper/translate_markdowns.py`:

- Applies dictionary-based German-to-English replacements.
- Targets `job.md` and `motivation_letter.md` only.
- Idempotent-ish textual replacements, low external dependencies.

### 5.2 Deep translation

`src/scraper/deep_translate_jobs.py`:

- Uses `deep-translator` (`GoogleTranslator`).
- Applies line-level translation heuristics on selected line types.
- Executes concurrently with `ThreadPoolExecutor`.

## 6) CV Lane (Render, Build, ATS)

### 6.1 CV source model

Primary runtime source:

- `data/reference_data/profile/base_profile/profile_base_data.json`

Path config:

- `src/cv_generator/config.py` (`CVConfig`)

### 6.2 CV generator entrypoint

Module: `src/cv_generator/__main__.py`

Supported commands:

- `status`
- `render`
- `build`
- `validate-ats`
- `test-template`

Output path contract:

`data/pipelined_data/<source>/<job_id>/cv/rendered/`

Artifacts:

- `cv.docx`
- `cv.tex`
- `cv.pdf`

ATS report path:

- `data/pipelined_data/<source>/<job_id>/cv/ats/report.json`

### 6.3 DOCX renderer

Renderer module: `src/render/docx.py`

Design choices for ATS compatibility:

- Single-column paragraph-based header (no table-based header dependency).
- Standard section names (`SUMMARY`, `EXPERIENCE`, `EDUCATION`, `SKILLS`, etc.).
- Bullet-style sections for parsability.
- Limited decorative styling (colors, spacing, paragraph borders) without structural complexity.
- Supports built-in style variants (`classic`, `modern`) and optional external `.docx` base templates.
- DOCX engine requires LibreOffice (`soffice`) for DOCX -> PDF conversion.

### 6.4 PDF text extraction

Module: `src/render/pdf.py`

- `extract_docx_text(...)` for DOCX text inspection.
- `extract_pdf_text(...)` for PDF ATS target text extraction (`pypdf` with `PyPDF2` fallback).

## 7) ATS Lane

### 7.1 Core ATS analysis

Module: `src/cv_generator/ats.py`

Dual-engine model:

1. **Code engine**: deterministic evaluator (`src/ats_tester/deterministic_evaluator.py`) backed by `TextAnalyzer`.
2. **LLM engine**: Gemini-based semantic evaluation (`src/utils/gemini.py` client path).

Scoring:

- Weighted merge (`code=0.6`, `llm=0.4` by default).
- `fallback` mode: tolerate missing engines.
- `strict` mode: require all engines.

### 7.2 Deterministic parity checks

During `validate-ats`, report includes `content_parity`:

- Compares `to_render.md` (if present) against rendered text.
- Measures:
  - line overlap percentage
  - order match percentage
  - missing and out-of-order lines

Targets:

- `--ats-target docx`
- `--ats-target pdf` (default for validation in current CV CLI)

### 7.3 ATS report contract (high-level)

`report.json` includes:

- `score`: final combined score
- `engines.code`: deterministic/fallback engine status and score
- `engines.llm`: Gemini engine status and score/reason
- `ats_target`: source artifact used for ATS extraction (`pdf` or `docx`)
- `content_parity`: deterministic parity diagnostics (when `to_render.md` is available)

Detailed ATS checker internals, thresholds, schema, and troubleshooting:

- `docs/cv/ats_checker_deep_dive.md`

## 8) Submission Packaging Lane

### 8.1 Backup manifest

Module: `src/utils/build_backup_compendium.py`

- Walks `data/pipelined_data` and `data/reference_data`.
- Emits checksum manifest to `data/reference_data/backup/backup_compendium.json`.

### 8.2 PDF merge/compress

Module: `src/utils/pdf_merger.py`

- Merges ordered input PDFs.
- Compresses with Ghostscript (`gs`) until below target size threshold.

## 9) Recommended Operational Flows

### 9.1 Refresh jobs + artifacts

```bash
python src/cli/pipeline.py run --fetch filtered --translate rules --regenerate
```

### 9.2 Build final CV PDF and run ATS on PDF

```bash
python src/cli/pipeline.py cv-pdf 201084 english --source tu_berlin --via docx --docx-template modern
```

### 9.3 Explicit ATS validation against PDF

```bash
python src/cli/pipeline.py cv-validate-ats 201084 --source tu_berlin --file-stem cv --ats-target pdf
```

### 9.4 DOCX template quality gate (100% parity)

```bash
python src/cli/pipeline.py cv-template-test 201084 english --source tu_berlin --via docx --docx-template modern --target docx --require-perfect
```

## 10) Current Gaps and Improvement Targets

1. **Legacy/manual jobs may miss `to_render.md`**, which makes parity unavailable until a fresh render/build is run.
2. **Scraper logic duplication** exists across `fetch_all_filtered_jobs.py`, `fetch_and_parse_all.py`, and `generate_populated_tracker.py`.
3. **Mixed robustness around ATS dependencies** (e.g., missing `spacy` or Gemini client creds) can force fallback paths.
4. **Submission lane is partly separate** (`pdf_merger.py` not yet integrated into unified CLI command set).
5. **Some docs lag code** (command lists in module READMEs should be synchronized with latest CLI additions).

## 11) Governance Rules for Changes

- Prefer CLI-first invocation (`src/cli/pipeline.py`) over direct module execution.
- Keep generated artifacts in `data/pipelined_data/...`, not in source directories.
- Preserve stable per-job file contracts (`raw.html`, `proposal_text.md`, `summary.json`, `job.md`).
- Record major pipeline behavior changes in `changelog.md`.
