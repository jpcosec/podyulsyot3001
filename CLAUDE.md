# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

Conda environment: `phd-cv` (Python 3.11). Activate with `conda activate phd-cv`.

System dependencies: `libreoffice` (DOCX→PDF), `pdflatex` / `texlive` (LaTeX builds), `ghostscript` (`gs`) for PDF compression.

## Common Commands

```bash
# Full pipeline run (fetch + translate)
python src/cli/pipeline.py run

# CV lifecycle for a specific job
python src/cli/pipeline.py cv-tailor 201084
python src/cli/pipeline.py cv-build 201084 english --via docx --docx-template modern
python src/cli/pipeline.py cv-validate-ats 201084 --ats-target pdf
python src/cli/pipeline.py cv-template-test 201084 english --via docx --target docx --require-perfect

# PDF assembly
python src/utils/pdf_merger.py -o Final_Application.pdf file1.pdf file2.pdf

# Status and validation
python src/cli/pipeline.py status
python src/cli/pipeline.py validate
```

## Running Tests

```bash
pytest                                    # all tests
pytest tests/render/test_docx.py         # single file
pytest tests/render/test_docx.py::test_function  # single test
```

`conftest.py` adds the repo root to `sys.path` automatically.

## Architecture

### Entry Points
- `src/cli/pipeline.py` — **primary unified CLI**. Commands: `run`, `fetch`, `translate`, `regenerate`, `backup`, `status`, `validate`, `cv-render`, `cv-build`, `cv-validate-ats`, `cv-pdf`, `cv-template-test`, `cv-tailor`.
- `src/cv_generator/__main__.py` — direct module CLI, invoked by pipeline.py for CV operations.

### Path Authority
- `src/cv_generator/config.py` — `CVConfig` dataclass. All path resolution flows through here.
- Profile canonical path: `data/reference_data/profile/base_profile/profile_base_data.json`
- Pipeline output root: `data/pipelined_data/tu_berlin/<job_id>/`
- Always use `Path(__file__).resolve().parents[n]` — never hardcode `/home/jp/phd`.

### CV Rendering (active)
- `src/render/docx.py` — `DocumentRenderer`: ATS-safe single-column DOCX (primary path).
- `src/render/styles.py` — style constants: `CVStyles` (classic), `CVStylesModern`, `CVStylesHarvard`, `CVStylesExecutive`.
- `src/render/latex.py` — jinja2 → `.tex` rendering; templates in `src/render/templates/latex/`.
- `src/render/pdf.py` — text extraction via `pdftotext` subprocess (preferred over pypdf).

### ATS Engine
- `src/cv_generator/ats.py` — dual-engine orchestration: code (0.6 weight) + Gemini LLM (0.4 weight).
- `src/ats_tester/deterministic_evaluator.py` — `DeterministicContentEvaluator` (code path).
- Gemini client: `src/utils/gemini.py` — uses `google-genai` SDK (NOT `google-generativeai`), model from `GEMINI_MODEL` env var.

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

## Files to Avoid (Legacy)
- `src/cv_generator/renderer.py` — superseded by `src/render/docx.py`
- `src/cv_generator/styles.py` — superseded by `src/render/styles.py`
- `src/cv_generator/compile` — superseded by `__main__.py`

## Documentation Policy
- Top-level docs: `README.md`, `docs/`.
- Module docs live next to their module.
- Major changes go in `changelog.md`.
- ATS rules: `docs/cv/ats-guidelines.md`.
- Pipeline deep dive: `docs/pipeline/end_to_end_pipeline_deep_dive.md`.
