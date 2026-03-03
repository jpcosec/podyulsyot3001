# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

Conda environment: `phd-cv` (Python 3.11). Activate with `conda activate phd-cv`.

System dependencies: `libreoffice` (DOCX→PDF), `pdflatex` / `texlive` (LaTeX builds), `ghostscript` (`gs`) for PDF compression.

## Common Commands

```bash
# Graph-based workflow (default run path)
python src/cli/pipeline.py job 201084 ingest                    # fetch job posting
python src/cli/pipeline.py job 201084 match                     # generate match proposal
python src/cli/pipeline.py job 201084 tailor-cv --language english  # tailor CV content
python src/cli/pipeline.py job 201084 motivate                  # generate motivation letter
python src/cli/pipeline.py job 201084 draft-email               # compose email
python src/cli/pipeline.py job 201084 render --via docx --docx-template modern  # render PDFs
python src/cli/pipeline.py job 201084 package                   # merge into Final_Application.pdf

# Shortcuts
python src/cli/pipeline.py job 201084 run                       # run graph coordinator until done/review gate
python src/cli/pipeline.py job 201084 run --resume              # resume after editing match proposal
python src/cli/pipeline.py job 201084 status                    # show step completion table

# Job queries
python src/cli/pipeline.py jobs                                 # list all open jobs
python src/cli/pipeline.py jobs --expiring 7                    # jobs expiring within 7 days
python src/cli/pipeline.py jobs --keyword "bioprocess"          # filter by keyword

# Admin
python src/cli/pipeline.py archive 201084                       # archive a job
python src/cli/pipeline.py ingest-url https://job.posting.url   # ingest from URL
python src/cli/pipeline.py ingest-listing https://listing.url   # scrape all from listing
```

## Running Tests

```bash
pytest                                    # all tests
pytest tests/render/test_docx.py         # single file
pytest tests/render/test_docx.py::test_function  # single test
```

`conftest.py` adds the repo root to `sys.path` automatically.

## Architecture

### Graph Coordinator (Current)
Primary orchestration now lives in `src/graph/pipeline.py`:
- graph-style run flow with review interrupt/resume (`run` / `run --resume`)
- review gate pauses when `planning/reviewed_mapping.json` is missing
- individual step verbs remain available for targeted/manual execution

### Legacy Step Modules
Step implementations remain in `src/steps/`:
1. **ingestion** — scrape jobs, parse HTML → raw artifacts
2. **matching** — extract requirements, generate proposals, approve matches
3. **motivation** — generate motivation letter content
4. **cv_tailoring** — tailor CV to job requirements
5. **email_draft** — compose application email
6. **rendering** — convert content (.md) → PDFs (DOCX/LaTeX)
7. **packaging** — merge PDFs into final submission

Each step is registered in `src/steps/__init__.py` and callable via CLI: `pipeline job <id> <step-name>`.

### Entry Points
- **`src/cli/pipeline.py`** — thin CLI dispatcher that routes commands to step functions (now ~300 lines, was 2149)
- **`src/steps/`** — all 7 step modules implementing the pipeline workflow

### Path & State Management
- **`src/utils/state.py`** — `JobState` class (single authority for job paths and artifact tracking)
  - `state.artifact_path(rel)` — resolve absolute paths
  - `state.step_complete(step)` — check step completion
  - `state.pending_steps()` — list incomplete steps
  - `state.read_artifact()` / `state.write_artifact()` — unified I/O
- **`src/utils/config.py`** — `CVConfig` (project root, profile root, pipeline root)
- Profile canonical path: `data/reference_data/profile/base_profile/profile_base_data.json`
- Pipeline output root: `data/pipelined_data/tu_berlin/<job_id>/`
- Always use `Path(__file__).resolve().parents[n]` — never hardcode `/home/jp/phd`.

### Comment System
- **`src/utils/comments.py`** — extract, collect, and log inline HTML comments (`<!-- comment -->`)
- Comments flow from step outputs → prompt injection for LLM refinement
- Logged in `planning/comments_log.json` per step

### CV Rendering (src/render/)
- **`src/render/docx.py`** — `DocumentRenderer`: ATS-safe single-column DOCX (primary path)
- **`src/render/styles.py`** — style constants: `CVStyles` (classic), `CVStylesModern`, `CVStylesHarvard`, `CVStylesExecutive`
- **`src/render/latex.py`** — jinja2 → `.tex` rendering; templates in `src/render/templates/`
- **`src/render/pdf.py`** — text extraction via `pdftotext` subprocess (preferred over pypdf)

### ATS Engine
- **`src/utils/ats.py`** — dual-engine orchestration: code (0.6 weight) + Gemini LLM (0.4 weight)
- **`src/ats_tester/deterministic_evaluator.py`** — `DeterministicContentEvaluator` (code path)
- Gemini client: `src/utils/gemini.py` — uses `google-genai` SDK (NOT `google-generativeai`), model from `GEMINI_MODEL` env var

### Data Layout per Job
```
data/pipelined_data/tu_berlin/<job_id>/
  job.md            # tracker (hand-edited, at root)
  raw/              # scraped artifacts (auto-generated — never hand-edit)
  planning/         # cv_tailoring.md, cv_content_preview.md, motivation_letter.md
  cv/
    to_render.md    # canonical render source (ATS parity reference)
    rendered/       # DOCX, PDF, LaTeX outputs
    ats/            # report.json, template_test.json
  output/           # final submission PDFs (gitignored)
  build/            # LaTeX scratch (gitignored)
```

## Critical Rules

**ATS-safe rendering:**
- Use single-column paragraph layout only — never table-based headers.
- Photo rendered as floating anchored image (`wp:anchor`, top-right) — preserves ATS safety.
- Section order is non-negotiable: Header → Summary → Education → Experience → Publications → Skills → Languages.

**LaTeX ATS markers:**
- `\atswhite{text}` injects hidden text (same font size, white color) for ATS extraction parity.
- Section/date/item markers follow the pattern documented in `docs/cv/ats-guidelines.md`.

**DOCX templates** (`--docx-template classic|modern|harvard|executive`): all produce identical ATS scores; differ only in font, color, and margins.

## Legacy Files (Phase 10 & 11 — Deleted)

### Phase 10
- `src/cv_generator/renderer.py` (superseded by `src/render/docx.py`)
- `src/cv_generator/styles.py` (superseded by `src/render/styles.py`)
- `src/cv_generator/compile` (superseded by CLI)
- `src/cv_generator/Code/`, `DHIK_filled/`, `Txt/`, `src/` (legacy data directories)
- `src/build_word_cv.py` (legacy hardcoded DOCX builder)
- `src/ats_tester/backend/`, `frontend/` (orphaned web app scaffolding)
- `src/scraper/fetch_jobs.sh` (legacy shell wrapper)

### Phase 11 (cv_generator Complete Cleanup)
- **Entire `src/cv_generator/` directory deleted**
  - Migrated modules: `config.py`, `loaders/`, `model.py`, `ats.py`, `pipeline.py`, `__main__.py` → `src/utils/`
  - `__main__.py` renamed to `cv_rendering.py` for clarity

## Documentation Policy
- Top-level docs: `README.md`, `docs/`.
- Module docs live next to their module.
- Major changes go in `changelog.md`.
- ATS rules: `docs/cv/ats-guidelines.md`.
- Pipeline deep dive: `docs/pipeline/end_to_end_pipeline_deep_dive.md`.
