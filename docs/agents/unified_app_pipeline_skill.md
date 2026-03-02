# Unified Application Pipeline Skill

Purpose: reusable operating playbook for agentic runs in this repository.

## Scope

Use this skill when handling job applications end-to-end with the staged lifecycle:

1. `app-prepare`
2. `app-review`
3. `app-renderize`

Or one-shot:

- `app-run`

Applies to both targets:

- `motivation`
- `cv`
- `all`

## Environment

- Required conda env: `phd-cv`
- Preferred execution style:
  - `conda run -n phd-cv python src/cli/pipeline.py <command> ...`

## Canonical Commands

- Prepare:
  - `python src/cli/pipeline.py app-prepare <job_id> --source <source> --target all`
- Review (HTML comments gate):
  - `python src/cli/pipeline.py app-review <job_id> --source <source> --target all`
- Renderize:
  - `python src/cli/pipeline.py app-renderize <job_id> --source <source> --target all`
- One-shot orchestration:
  - `python src/cli/pipeline.py app-run <job_id> --source <source> --target all`
- Status:
  - `python src/cli/pipeline.py app-status <job_id> --source <source> --target all`
- Job index by source:
  - `python src/cli/pipeline.py jobs-index --source all`

## Pipeline Contract

All stage outputs for a job live under:

- `data/pipelined_data/<source>/<job_id>/output/`

Subfolders:

- `prep/`: editable artifacts for correction cycle
- `review/`: unresolved-comment report
- `final/`: renderized final deliverables
- `reports/`: ATS pre/final reports
- `state.md`: timeline + stage statuses

## Review Gate Rule

Corrections are expressed as HTML comments in prep markdown:

- `<!-- correction note -->`

`app-review` scans prep files and blocks renderization if unresolved comments exist.

Expected behavior:

- comments found -> status `needs_corrections`
- no comments -> status `ready_to_renderize`

## ATS Rule (Two Stage)

Run ATS twice:

1. Prepare stage on pre artifacts (`*_ats_pre.json`)
2. Renderize stage on final artifacts (`*_ats_final.json`)

Files:

- `output/reports/cv_ats_pre.json`
- `output/reports/cv_ats_final.json`
- `output/reports/motivation_ats_pre.json`
- `output/reports/motivation_ats_final.json`

## Motivation Deliverables

Final motivation outputs:

- `output/final/motivation/motivation_letter.md`
- `output/final/motivation/motivation_letter.pdf`
- `output/final/motivation/application_email.md`

Supporting prep assets include synthetic pre-letter and evidence-backed planning.

## CV Deliverables

Final CV outputs:

- `output/final/cv/cv.to_render.md`
- `output/final/cv/cv.docx`
- `output/final/cv/cv.pdf`

## Archiving Rule

Expired positions (deadline earlier than current date) should be moved to:

- `data/pipelined_data/<source>/archive/<job_id>/`

After archival, regenerate active index:

- `python src/cli/pipeline.py jobs-index --source all`

## Operational Defaults

- Keep source default as `tu_berlin` unless requested otherwise.
- Prefer `--target all` for complete runs.
- Use `--target cv` when Gemini quota blocks motivation generation.
- Keep `ats_mode=fallback` unless strict mode is explicitly requested.

## Failure Playbook

If `app-run` fails at review:

1. open `output/review/comments.md`
2. resolve comments in `output/prep/**/*.md`
3. rerun `app-review`
4. rerun `app-renderize`

If motivation generation fails with Gemini quota (`429 RESOURCE_EXHAUSTED`):

1. continue CV with `--target cv`
2. retry motivation later with `--target motivation`

## Current State Snapshot (Codified)

- Unified staged lifecycle is implemented and active.
- `app-status` and `jobs-index` are implemented.
- Central index files are generated under `data/pipelined_data/job_ids_index.{json,md}`.
- Motivation PDF renderer uses structured letter layout (improved formatting).
