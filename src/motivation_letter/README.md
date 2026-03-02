# Motivation Letter Module

Generates job-tailored motivation letters from:

- Full job posting text (`job.md` — complete translated posting)
- Candidate profile (`data/reference_data/profile/base_profile/profile_base_data.json`)
- Reviewed matching proposal (`planning/match_proposal.md` — human-approved)
- Prompt specification (`src/prompts/motivation_letter.txt`)

## Pipeline CLI

```bash
python src/cli/pipeline.py motivation-build <job_id> [--source tu_berlin]
```

Optional flags: `--skip-pdf`, `--skip-email`

## Output Files

- `data/pipelined_data/<source>/<job_id>/planning/motivation_letter.md`
- `data/pipelined_data/<source>/<job_id>/planning/motivation_letter.analysis.json`

## Status

Service module (`service.py`) pending rebuild as part of the incremental pipeline fix plan. See `docs/plans/2026-03-02-incremental-pipeline-fix/03-fix-motivation.md`.
