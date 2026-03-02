# Agent Entrypoint

This document is the operational entrypoint for coding/automation agents working in this repository.

## Mission

Support the PhD application workflow safely and reproducibly by improving automation, documentation, and execution quality without breaking the existing file-based process.

## Read-First Context

Before making changes, review:
- `README.md`
- `data/README.md`
- `docs/applications/Documentation_Checklist.md`
- `docs/applications/TODO.md`
- `src/scraper/`
- `src/utils/pdf_merger.py`

## Primary Work Domains

- `src/scraper/`: scrape postings, parse data, generate tracker markdown.
- `data/pipelined_data/`: generated pipeline artifacts (per website/job/document).
- `data/reference_data/`: reference/profile/template assets and archives.
- `src/cv_generator/`: CV source and rendered outputs.
- `src/utils/`: utility scripts for document packaging.

## Current State Constraints

- Most scripts are absolute-path based (`/home/jp/phd/...`).
- Generated markdown in `data/pipelined_data/tu_berlin/<job_id>/job.md` is a core operational artifact.
- Existing tracker files may contain manual edits and should not be overwritten blindly.
- This repository contains personal documents and identifiable information; minimize exposure in logs and outputs.

## Safe Execution Rules

- Prefer non-destructive updates.
- Back up or preserve user-authored markdown content when regenerating tracker files.
- Keep script behavior deterministic and idempotent where possible.
- Avoid introducing new required services or paid APIs.
- Maintain plain, explicit file outputs (markdown/csv/pdf) over opaque binary state.

## Decision Defaults

- CLI-first policy: prefer `python src/cli/pipeline.py ...` before any direct module command.
- Prefer `python src/cli/pipeline.py run` for standard end-to-end refreshes.
- If both fixed-list and filtered-list scrapers are viable, prefer `fetch_all_filtered_jobs.py`.
- If translation quality is uncertain, run rule-based translation first (`translate_markdowns.py`) before machine translation.
- If a change impacts all scraper scripts, centralize shared logic rather than copying patches into each script.

## Task Playbooks

### Add/Improve Scraping

1. Validate expected fields from one known job HTML page.
2. Refactor parser logic into reusable functions.
3. Keep output schema stable for frontmatter in `data/pipelined_data/tu_berlin/<job_id>/job.md`.
4. Add a small regression test or fixture-based validation.

### Improve Tracker Generation

1. Preserve existing frontmatter keys (`status`, `deadline`, `reference_number`, `url`, etc.).
2. Keep checklist sections stable unless explicitly requested.
3. If adding fields, update README and note migration impact.

### Improve PDF Packaging

1. Keep merge order user-driven via CLI args.
2. Retain Ghostscript fallback compression path.
3. Surface clear errors when `gs` is unavailable.

## Done Criteria for Agent Changes

- Code is readable and avoids unnecessary complexity.
- Documentation updated where behavior changes.
- `changelog.md` updated for major changes.
- Any risky assumption is made explicit.

## Open Improvement Backlog

- Introduce a repository-level config for paths and defaults.
- Add a unified CLI (`python -m ...`) for all workflows.
- Add parser tests against saved HTML fixtures.
- Separate generated files from curated files more cleanly.
