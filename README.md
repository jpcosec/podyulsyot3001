# PhD Application Workspace

This repository is a personal operations workspace for PhD and research-job applications, centered on TU Berlin postings.

It combines:
- job scraping and parsing scripts,
- markdown-based application tracking,
- CV generation to final PDF (via LaTeX or DOCX),
- PDF assembly/compression utilities,
- and supporting academic documents.

## Scope and Intent

The repository is optimized for a single-user workflow where generated artifacts are directly usable in Obsidian and email submissions.

The current implementation is script-first (not package-first): most automation lives in standalone Python and shell scripts under `src/`.

## Repository Structure

```text
.
├── data/
│   ├── README.md                    # canonical data model and naming conventions
│   ├── pipelined_data/
│   │   └── tu_berlin/
│   │       ├── summary.csv
│   │       └── <job_id>/
│   │           ├── job.md                    # application tracker (root, hand-edited)
│   │           ├── raw/                      # scraped artifacts (auto-generated)
│   │           │   ├── raw.html
│   │           │   ├── proposal_text.md
│   │           │   └── summary.json
│   │           ├── planning/                 # agent + human authored
│   │           │   ├── cv_tailoring.md
│   │           │   ├── cv_content_preview.md
│   │           │   └── motivation_letter.md
│   │           ├── cv/
│   │           │   ├── to_render.md          # canonical render source for parity checks
│   │           │   ├── rendered/             # generated DOCX / TeX / PDF
│   │           │   └── ats/                  # ATS reports
│   │           ├── output/                   # final submission PDFs (gitignored)
│   │           └── build/                    # LaTeX scratch (gitignored)
│   └── reference_data/
│       ├── application_assets/     # CV, docs, publication proofs, photos
│       ├── agent_feedback/         # templates and recommender drafts
│       ├── profile/                # canonical runtime profile
│       │   └── base_profile/
│       │       └── profile_base_data.json
│       ├── prompts/                # agent prompt specifications
│       ├── archive/                # archived tracker markdowns
│       └── backup/
│           └── backup_compendium.json
├── src/
│   ├── cli/
│   │   ├── pipeline.py             # unified pipeline CLI (primary entrypoint)
│   │   └── README.md
│   ├── cv_generator/               # CV domain logic
│   │   ├── __main__.py             # direct module CLI
│   │   ├── config.py               # CVConfig — path authority
│   │   ├── model.py                # CVModel dataclass
│   │   ├── ats.py                  # ATS orchestration (dual engine)
│   │   ├── pipeline.py             # multi-agent tailoring
│   │   └── loaders/
│   │       └── profile_loader.py
│   ├── render/                     # shared rendering infrastructure
│   │   ├── docx.py                 # DocumentRenderer (ATS-safe single-column)
│   │   ├── latex.py                # jinja2 → .tex
│   │   ├── pdf.py                  # text extraction (DOCX + PDF)
│   │   ├── styles.py               # CVStyles constants
│   │   ├── templates/latex/        # english/german/spanish .tex.jinja2
│   │   └── assets/                 # LaTeX assets (Einstellungen/, Abbildungen/)
│   ├── utils/                      # shared low-level infrastructure
│   │   ├── loader.py               # JSON/file loading
│   │   ├── gemini.py               # GeminiClient (google-genai SDK)
│   │   ├── nlp/
│   │   │   └── text_analyzer.py    # TextAnalyzer (spaCy, language-registry ready)
│   │   ├── pdf_merger.py           # merge/compress final application PDFs
│   │   └── build_backup_compendium.py
│   └── ats_tester/
│       ├── deterministic_evaluator.py  # DeterministicContentEvaluator + parity checker
│       └── backend/                # web UI (separate Flask app, independent)
├── tests/
│   ├── cv_generator/
│   ├── render/
│   └── utils/
├── docs/
│   ├── AGENT_ENTRYPOINT.md         # agent onboarding and execution guide
│   ├── PROFILE.md                  # canonical profile record (human + YAML)
│   ├── PROFILE.json                # canonical profile record (strict JSON)
│   ├── applications/
│   │   ├── TODO.md
│   │   └── Documentation_Checklist.md
│   ├── cv/
│   │   ├── ats-guidelines.md       # ATS formatting rules and constraints
│   │   └── ats_checker_deep_dive.md
│   ├── pipeline/
│   │   └── end_to_end_pipeline_deep_dive.md
│   └── data/
│       └── backup_compendium.md
├── environment.yml                 # conda env spec (phd-cv, Python 3.11)
├── conftest.py                     # pytest sys.path setup
├── .env                            # GOOGLE_API_KEY, GEMINI_MODEL
└── README.md
```

Additional profile metadata:
- `docs/PROFILE.md` — machine-friendly and human-readable personal profile for agents.
- `docs/PROFILE.json` — strict JSON export of canonical profile data.
- `data/reference_data/profile/base_profile/profile_base_data.json` — canonical runtime profile input used by CV generation.

## Data Model

- Two broad categories under `data/`: `pipelined_data/` and `reference_data/`.
- Canonical pipeline root: `data/pipelined_data/{website_source}/{job_id}/`.
- Each job folder has four sub-zones: `raw/` (scraped, auto-generated), `planning/` (human+agent authored), `cv/` (rendered artifacts + ATS reports), `output/` (final PDFs, gitignored), `build/` (LaTeX scratch, gitignored). `job.md` lives at the job root.
- Current website source: `tu_berlin`.
- Reference details and naming live in `data/README.md`.

## Workflow Overview

1. Fetch TU Berlin jobs into per-job pipeline folders.
2. Generate or refresh `job.md` and extracted proposal text.
3. Translate remaining German text in `job.md`/`motivation_letter.md` when needed.
4. Regenerate backup compendium manifest.
5. Tailor motivation letter and CV for a specific posting.
6. Build final CV PDF via `--via docx|latex`.
7. Validate ATS against final PDF (`cv-validate-ats --ats-target pdf`).
8. Merge and compress supporting PDFs for final submission.

## Key Scripts

- `src/cli/pipeline.py`
  - Primary unified CLI. Job/data stages: `run`, `fetch`, `translate`, `regenerate`, `backup`, `status`, `validate`. CV/ATS stages: `cv-render`, `cv-build`, `cv-validate-ats`, `cv-pdf`, `cv-template-test`, `cv-tailor`.
  - `cv-tailor` writes CV guidance into `data/pipelined_data/tu_berlin/<job_id>/planning/`.
- `src/scraper/fetch_all_filtered_jobs.py`
  - Primary crawler for filtered TU Berlin listings.
  - Generates `data/pipelined_data/tu_berlin/<job_id>/{raw.html,proposal_text.md,job.md}`, plus `summary.csv` and `summary_detailed.csv`.
- `src/scraper/fetch_and_parse_all.py`
  - Similar pipeline with a fixed URL list.
- `src/scraper/generate_populated_tracker.py`
  - Builds tracker markdown from already-fetched HTML files.
- `src/scraper/translate_markdowns.py`
  - Rule-based German-to-English text replacement in job markdown files.
- `src/scraper/deep_translate_jobs.py`
  - Optional machine translation pass using `deep-translator`.
- `src/cv_generator/__main__.py`
  - CV module CLI for `status`, `render`, `build`, `validate-ats`, `test-template`.
  - Supports PDF production via `--via latex|docx`, DOCX template variants, and ATS target selection (`--ats-target pdf|docx`).
- `src/utils/pdf_merger.py`
  - Merges PDFs and compresses with Ghostscript (`gs`) to target size constraints.
- `src/utils/build_backup_compendium.py`
  - Rebuilds checksum/index manifest at `data/reference_data/backup/backup_compendium.json`.

## Dependencies

Python libraries used by scripts:
- `beautifulsoup4`
- `python-docx`
- `jinja2`
- `python-dotenv`
- `pypdf` or `PyPDF2`
- `spacy` (optional but recommended for full deterministic ATS engine)
- `deep-translator` (optional translation path)

System dependency:
- `libreoffice` (`soffice`) for DOCX -> PDF conversion when using `--via docx`
- `texlive` / `pdflatex` for LaTeX CV builds when using `--via latex`
- `ghostscript` (`gs`) for PDF compression.

## In-Depth Review Findings

### Strengths

- End-to-end flow exists from job discovery to submission package.
- Output format is practical for job-centric processing (`data/pipelined_data/tu_berlin/<job_id>/job.md`).
- CV and publication assets are centralized and reusable.
- PDF merging/compression addresses common German application portal limits.

### Gaps and Risks

- Scraper scripts still write `raw.html`, `proposal_text.md`, `summary.json` directly to the job root, not to `raw/`. New jobs require a manual migration step to match the sub-zone layout.
- Parsing/markdown generation logic is duplicated across several scraper scripts.
- No tests or validation for scraper regressions after site layout changes.
- `src/cv_generator/` still contains superseded legacy files (`renderer.py`, `styles.py`, `compile`, `DHIK_filled/`, `src/`) that were not removed during the 2026-03-01 redesign.
- `src/build_word_cv.py` contains hardcoded CV content and is not integrated into the profile/pipeline; it is a manual one-off script.
- PDF merge/compress (`pdf_merger.py`) is not yet integrated into the unified CLI command set.

### Recommended Refactor Priorities

1. Remove legacy files from `src/cv_generator/` that have been superseded by `src/render/`.
2. Extract shared scraping/parsing functions into reusable modules.
3. Integrate `pdf_merger.py` into `src/cli/pipeline.py` as a `cv-package` command.
4. Add smoke tests for at least one known job HTML sample.

## Typical Usage

```bash
python src/cli/pipeline.py run
python src/cli/pipeline.py cv-tailor 201084
python src/cli/pipeline.py cv-build 201084 english --via docx --docx-template modern
python src/cli/pipeline.py cv-validate-ats 201084 --ats-target pdf
python src/cli/pipeline.py cv-template-test 201084 english --via docx --target docx --require-perfect
python src/cli/pipeline.py status
python src/utils/pdf_merger.py -o Final_Application.pdf <file1.pdf> <file2.pdf> <file3.pdf>
```

Advanced examples:

```bash
python src/cli/pipeline.py run --fetch fixed --translate both --regenerate
python src/cli/pipeline.py validate
python src/cli/pipeline.py cv-render 201084 english --via docx --docx-template-path data/reference_data/application_assets/templates/cv_base_template.docx
```

## Deep Dive

- End-to-end technical walkthrough: `docs/pipeline/end_to_end_pipeline_deep_dive.md`
- ATS checker architecture and troubleshooting: `docs/cv/ats_checker_deep_dive.md`

## CV Engine Recommendation

- ATS-first default: use `--via docx` and validate against final PDF via `cv-validate-ats --ats-target pdf`.
- LaTeX remains available as a layout-stable fallback, but ATS quality must always be confirmed on the generated PDF.

## Documentation Policy

- Top-level abstract documentation lives in `README.md`.
- General supporting docs live under `docs/`.
- Module-specific docs should live next to their module and be referenced from this README.
- Major changes should be recorded in `changelog.md`.
