# Command Surface and Mutation Audit

Date: 2026-03-02

## Why this document exists

This is a ground-truth audit of:

- all user-facing commands in `src/cli/pipeline.py`
- the CV sub-CLI in `src/cv_generator/__main__.py`
- standalone runfiles that can write/move/delete files

The goal is to support a robust architecture where normal operations are single-job scoped and batch behavior is explicit through orchestrators.

## Sources analyzed

- `src/cli/pipeline.py`
- `src/cv_generator/__main__.py`
- `src/scraper/scrape_single_url.py`
- `src/scraper/fetch_listing.py`
- `src/scraper/generate_populated_tracker.py`
- `src/utils/build_backup_compendium.py`
- `src/utils/pdf_merger.py`
- `src/agent/orchestrator.py`
- `src/agent/tools.py`
- `src/cv_generator/compile` (legacy runfile)

## Scope labels used below

- `single-job`: command requires one job context and writes only that job tree
- `batch`: command can touch many jobs in one run
- `global`: command writes cross-job/global indexes/manifests/reports
- `read-only`: no file mutations expected

## Pipeline CLI command audit (`python src/cli/pipeline.py ...`)

| Command | Scope | Mutates filesystem | Primary write targets |
|---|---|---|---|
| `run` | batch/global | yes | Depends on enabled stages (`fetch`, `regenerate`, `backup`) |
| `fetch` | batch | yes | New/updated job folders under `data/pipelined_data/<source>/<job_id>/...` |
| `fetch-url` | batch (N URLs) | yes | Per job: `raw/raw.html`, `raw/source_text.md`, `raw/language_check.json`, `raw/extracted.json`, `job.md` |
| `fetch-listing` | batch | yes | Scrapes only newly discovered IDs; same per-job artifacts as `fetch-url` |
| `apply-to` | batch orchestrator | yes | Batch report + per-job CV/motivation/ATS outputs |
| `translate` | global | no (current) | Deprecated no-op (warning only) |
| `regenerate` | batch | yes | Rewrites `job.md`, `summary.json`, `proposal_text.md`, may rewrite `raw/source_text.md` |
| `backup` | global | yes | `data/reference_data/backup/backup_compendium.json` |
| `cv-tailor <job_id>` | single-job | yes | `planning/cv_tailoring.md`, `cv/pipeline_intermediates/*.json` |
| `match-propose <job_id>` | single-job | yes | `planning/match_proposal.md`, matcher intermediate JSON |
| `match-approve <job_id>` | single-job | yes | `planning/reviewed_mapping.json`, updates status in `planning/match_proposal.md` |
| `motivation-pre <job_id>` | single-job | yes | `planning/motivation_letter.pre.md`, `planning/motivation_letter.pre.analysis.json` |
| `motivation-build <job_id>` | single-job | yes | `planning/motivation_letter.md`, analysis JSON, PDF, email draft |
| `app-prepare <job_id>` | single-job | yes | `output/prep/**`, `output/reports/cv_ats_pre.json`, `output/state.md` |
| `app-review <job_id>` | single-job | yes | `output/review/comments.md`, `output/state.md` |
| `app-status <job_id>` | single-job | read-only | Reads `output/state.md` + prep comments |
| `app-renderize <job_id>` | single-job | yes | `output/final/**`, ATS final reports, `output/state.md` |
| `app-run <job_id>` | single-job | yes | Combined prepare+review+renderize outputs |
| `jobs-index` | global | yes | `data/pipelined_data/job_ids_index.json`, `data/pipelined_data/job_ids_index.md` |
| `archive-passed` | batch/global | yes | Moves active job dirs to `archive/`, writes `archive_passed_report_<source>.json` |
| `status` | global | read-only | Reads pipeline tree and manifest presence |
| `validate` | global | read-only | Same checks as `status` for exit code |
| `cv-render <job_id>` | single-job | yes | Delegates to CV CLI render outputs |
| `cv-build <job_id>` | single-job | yes | Delegates to CV CLI build outputs |
| `cv-validate-ats <job_id>` | single-job | yes | CV ATS report JSON |
| `cv-pdf <job_id>` | single-job | yes | CV build + ATS outputs |
| `cv-template-test <job_id>` | single-job | yes | CV artifacts + `cv/ats/template_test.json` |

## CV sub-CLI audit (`python -m src.cv_generator ...`)

Commands:

- `status`: read-only
- `render <language>`: writes `cv/to_render.md`, rendered artifacts (`docx`/`tex`/`pdf`), optional ATS report
- `build <language>`: currently same mutating behavior as render
- `validate-ats`: writes ATS report for existing rendered artifacts
- `test-template`: runs build + writes `cv/ats/template_test.json`

Per-job write roots:

- `data/pipelined_data/<source>/<job_id>/cv/to_render.md`
- `data/pipelined_data/<source>/<job_id>/cv/rendered/<via>/cv.{docx,tex,pdf}`
- `data/pipelined_data/<source>/<job_id>/cv/ats/report.json`
- `data/pipelined_data/<source>/<job_id>/cv/ats/template_test.json`

## Special mutating runfiles (standalone)

### `src/scraper/scrape_single_url.py`

- Scope: single-job per URL
- Writes raw and parsed artifacts under one job directory
- Enforces optional strict-English gate

### `src/scraper/generate_populated_tracker.py`

- Scope: batch by design (`--scope active|archive|all`)
- Rebuilds tracker artifacts from local raw/source content
- Can rewrite existing `job.md` and derived files at scale

### `src/utils/build_backup_compendium.py`

- Scope: global
- Recomputes and rewrites backup manifest for all files in `data/pipelined_data` and `data/reference_data`

### `src/utils/pdf_merger.py`

- Scope: user-selected output path
- Writes merged/compressed final PDF and removes temporary uncompressed intermediate

### `src/cli/pipeline.py`

- Scope: mixed (single-job + batch + global)
- Main orchestration entrypoint; can indirectly trigger most writes in repository data flow

### `src/cv_generator/__main__.py`

- Scope: single-job
- Canonical renderer and ATS CLI for CV artifacts

### `src/cv_generator/compile` (legacy runfile)

- Scope: single-job
- Mutating legacy CV runfile with overlapping behavior vs `src/cv_generator/__main__.py`
- Not wired to the primary pipeline CLI; high risk of divergence/confusion

## Hidden mutation path: batch orchestrator internals

The `apply-to` command calls `ApplicationAgent` (`src/agent/orchestrator.py`) which:

- writes `data/pipelined_data/batch_report.md`
- calls tool functions that scrape jobs, build CVs, generate motivation letters, create PDFs, and run ATS
- can touch multiple job directories in one run

This is currently the real batch orchestrator in code.

## Critical findings for architecture design

1. The command surface mixes single-job, batch, and global operations in one namespace.
2. Batch behavior exists in multiple places (`run`, `fetch`, `fetch-listing`, `regenerate`, `apply-to`, `archive-passed`).
3. `apply-to` is orchestrator-like, but job identity is not fully normalized (`reference_number` can leak into IDs).
4. A legacy mutating runfile still exists (`src/cv_generator/compile`) alongside canonical CV CLI.
5. `translate` remains as a compatibility command but intentionally does nothing.
6. Validation still depends on historic artifacts (`summary.csv`) and can drift from current deterministic flow contracts.

## Desired direction (architecture constraints)

If we enforce "normal ops are single-job" and "batch only through orchestrator", then:

1. Keep single-job primitives explicit and stable (`fetch-url`, `cv-*`, `motivation-*`, `app-*`, `match-*`).
2. Move all multi-job work behind explicit orchestrator commands (for example `batch <operation> ...`).
3. Mark batch/global commands as orchestration/admin only (`jobs-index`, `archive-passed`, `backup`, `regenerate`).
4. Remove or hard-deprecate legacy mutating runfiles not part of the canonical flow.
5. Define command contracts with mutation boundaries (allowed write roots per command).
6. Add dry-run where operations can move/overwrite many folders.

## Proposed next architecture step (for follow-up design doc)

- Introduce an explicit two-layer CLI model:
  - `pipeline job <job_id> <operation>` for all single-job mutating operations
  - `pipeline batch <operation>` for controlled multi-job orchestration
- Add a command registry with metadata:
  - scope (`single-job`/`batch`/`global`)
  - required identifiers (`job_id`, `source`)
  - allowed mutation roots
  - idempotency guarantees
  - dry-run support

This audit should be used as baseline before any command-surface refactor.
