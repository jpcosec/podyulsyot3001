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
│   ├── graph/                      # graph-style pipeline coordinator + domain modules
│   │   ├── pipeline.py             # run/resume coordinator with review interrupt
│   │   ├── agents/                 # shared agent runner infrastructure
│   │   ├── parsers/                # reviewed proposal + claim parsing helpers
│   │   └── pipelines/              # CV tailoring and match proposal pipelines
│   ├── steps/                      # pipeline step modules (targeted/manual execution)
│   │   ├── ingestion.py
│   │   ├── matching.py
│   │   ├── cv_tailoring.py
│   │   ├── motivation.py
│   │   ├── email_draft.py
│   │   ├── rendering.py
│   │   └── packaging.py
│   ├── render/                     # shared rendering infrastructure
│   │   ├── docx.py                 # DocumentRenderer (ATS-safe single-column)
│   │   ├── latex.py                # jinja2 → .tex
│   │   ├── pdf.py                  # text extraction (DOCX + PDF)
│   │   ├── styles.py               # CVStyles constants
│   │   ├── templates/              # english/german/spanish .tex.jinja2
│   │   └── assets/                 # LaTeX assets (Einstellungen/, Abbildungen/)
│   ├── utils/                      # shared low-level infrastructure
│   │   ├── state.py                # JobState (unified path authority + artifact tracking)
│   │   ├── config.py               # CVConfig (project/profile/pipeline roots)
│   │   ├── comments.py             # extract & log inline HTML comments
│   │   ├── loader.py               # JSON/file loading
│   │   ├── gemini.py               # GeminiClient (google-genai SDK)
│   │   ├── model.py                # CVModel, ContactInfo, EducationEntry, etc.
│   │   ├── pipeline.py             # compatibility shim re-exporting src/graph symbols
│   │   ├── ats.py                  # ATS dual-engine (code + Gemini LLM)
│   │   ├── cv_rendering.py         # rendering orchestration
│   │   ├── loaders/                # load_base_profile() (profile loading)
│   │   ├── pdf_merger.py           # merge/compress final application PDFs
│   │   └── build_backup_compendium.py
│   └── ats_tester/
│       └── deterministic_evaluator.py  # DeterministicContentEvaluator + parity checker
├── tests/
│   ├── cli/
│   ├── steps/
│   ├── scraper/
│   ├── motivation_letter/
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
│   │   ├── end_to_end_pipeline_deep_dive.md
│   │   ├── match_review_regeneration_loop.md
│   │   ├── motivation_letter_system_deep_dive.md
│   │   ├── command_surface_and_mutation_audit.md
│   │   └── current_architecture_analysis.md
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
- Each job folder has five sub-zones: `raw/` (scraped, auto-generated), `planning/` (human+agent authored), `cv/` (rendered artifacts + ATS reports), `output/` (final PDFs, gitignored), `build/` (LaTeX scratch, gitignored). `job.md` lives at the job root.
- Current website source: `tu_berlin`.
- Reference details and naming live in `data/README.md`.

## Workflow Overview

The default run path is graph-coordinated:

1. **ingest** -> fetch TU Berlin job posting -> raw artifacts
2. **match** -> generate requirement/evidence proposal + keywords
3. **review gate (interrupt)** -> user edits `planning/match_proposal.md`
4. **run --resume** -> auto-lock reviewed mapping and continue
5. **motivate** -> **tailor-cv** -> **draft-email** -> **render** -> **package**

Individual step commands remain available and support comment-based feedback loops.

**See `docs/pipeline/end_to_end_pipeline_deep_dive.md` for complete step DAG and CLI details.**

## Key Modules

### CLI & Orchestration
- **`src/cli/pipeline.py`**
  - Thin dispatcher routing `job <id> run` to graph coordinator
  - Command groups: `job <id> <step>`, `jobs` (listing), `ingest-*` (helpers), `archive`, `index`, `backup`
  - See `CLAUDE.md` for complete CLI command reference

### Graph Coordinator (`src/graph/`)
- **`pipeline.py`** — graph-style run/resume coordinator with explicit review interrupt
- **`parsers/`** — deterministic proposal parsing + claim-building helpers
- **`agents/base.py`** — shared `AgentRunner` for matcher/seller/checker execution
- **`pipelines/`** — extracted `CVTailoringPipeline` and `MatchProposalPipeline`

### Pipeline Steps (`src/steps/`)
Each step is an independent function with signature `run(state: JobState, **kwargs) -> StepResult`
- **`ingestion.py`** — scrape jobs, parse → raw artifacts
- **`matching.py`** — extract requirements, generate proposals, approve matches
- **`motivation.py`** — generate motivation letter content
- **`cv_tailoring.py`** — tailor CV to job → canonical render source
- **`email_draft.py`** — compose application email
- **`rendering.py`** — convert .md → PDFs (DOCX/LaTeX)
- **`packaging.py`** — merge PDFs → Final_Application.pdf

### Utilities & Configuration
- **`src/utils/state.py`** — `JobState` class (unified path authority + artifact tracking)
- **`src/utils/config.py`** — `CVConfig` (project/profile/pipeline roots)
- **`src/utils/comments.py`** — extract & log inline HTML comments for feedback loops
- **`src/utils/loader.py`** — JSON/file loading helpers
- **`src/utils/gemini.py`** — `GeminiClient` (google-genai SDK)
- **`src/utils/pdf_merger.py`** — merge & compress PDFs via Ghostscript
- **`src/utils/build_backup_compendium.py`** — rebuild backup manifest

### CV & ATS Modules
- **`src/utils/model.py`** — `CVModel`, `ContactInfo`, `EducationEntry`, etc.
- **`src/utils/loaders/`** — `load_base_profile()` (profile loading)
- **`src/utils/pipeline.py`** — compatibility shim for legacy imports
- **`src/utils/ats.py`** — ATS dual-engine (code 0.6 + Gemini LLM 0.4)
- **`src/utils/cv_rendering.py`** — rendering orchestration functions
- **`src/render/docx.py`** — `DocumentRenderer` (ATS-safe single-column DOCX)
- **`src/render/latex.py`** — jinja2 → `.tex` rendering
- **`src/render/pdf.py`** — PDF text extraction (pdftotext)
- **`src/render/styles.py`** — `CVStyles` constants (classic/modern/harvard/executive)

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

## Known Limitations

- Some tests require API keys (Gemini, spaCy) that may not be available offline.
- LaTeX PDF parity checker is best-effort (~86% order match) — sufficient for practical use.

## Typical Usage

**Single job workflow:**
```bash
# Run graph coordinator (pauses at review gate when needed)
python src/cli/pipeline.py job 201084 run

# Resume after reviewing/editing planning/match_proposal.md
python src/cli/pipeline.py job 201084 run --resume

# Or run steps individually
python src/cli/pipeline.py job 201084 ingest                    # fetch job
python src/cli/pipeline.py job 201084 match                     # generate match proposal
python src/cli/pipeline.py job 201084 tailor-cv                 # tailor CV
python src/cli/pipeline.py job 201084 render --via docx         # generate PDFs
python src/cli/pipeline.py job 201084 package                   # merge into Final_Application.pdf

# Check progress
python src/cli/pipeline.py job 201084 status
```

**Batch operations:**
```bash
# List all open jobs
python src/cli/pipeline.py jobs

# Filter by deadline
python src/cli/pipeline.py jobs --expiring 7

# Filter by keyword
python src/cli/pipeline.py jobs --keyword "bioprocess"

# Ingest from URL(s)
python src/cli/pipeline.py ingest-url https://job.url.de
python src/cli/pipeline.py ingest-listing https://listing.url.de

# Archive expired jobs
python src/cli/pipeline.py archive 201084
python src/cli/pipeline.py archive --expired  # all expired jobs
```

**Admin:**
```bash
# Rebuild job index
python src/cli/pipeline.py index

# Rebuild backup manifest
python src/cli/pipeline.py backup
```

## Deep Dive

- End-to-end pipeline walkthrough: `docs/pipeline/end_to_end_pipeline_deep_dive.md`
- Match review & regeneration loop: `docs/pipeline/match_review_regeneration_loop.md`
- Motivation letter subsystem: `docs/pipeline/motivation_letter_system_deep_dive.md`
- Command surface & mutation audit: `docs/pipeline/command_surface_and_mutation_audit.md`
- ATS checker architecture: `docs/cv/ats_checker_deep_dive.md`

## CV Engine Recommendation

- ATS-first default: use `--via docx` and validate against final PDF via `cv-validate-ats --ats-target pdf`.
- LaTeX remains available as a layout-stable fallback, but ATS quality must always be confirmed on the generated PDF.

## Documentation Policy

- Top-level abstract documentation lives in `README.md`.
- General supporting docs live under `docs/`.
- Module-specific docs should live next to their module and be referenced from this README.
- Major changes should be recorded in `changelog.md`.
