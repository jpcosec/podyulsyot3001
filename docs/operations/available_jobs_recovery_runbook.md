# Available Jobs Recovery Runbook

Date: 2026-03-11

## Purpose

Run the current prep-match pipeline on all available jobs, including jobs with missing LangGraph checkpoints, while preserving existing human reviews.

## Preconditions

Use the runtime environment documented in `agent_entrypoint.md`:

```bash
conda activate phd-cv
set -a; source .env; set +a
```

Required runtime deps for LLM steps:

- `langgraph`
- `google-generativeai`

## One-time safety migration (already idempotent)

This preserves reviewed decisions and adds hash-lock front matter to legacy reviewed files.

```bash
python -m src.cli.migrate_review_hash_lock --source tu_berlin --all-jobs --dry-run
python -m src.cli.migrate_review_hash_lock --source tu_berlin --all-jobs
```

Backups are written as:

- `data/jobs/<source>/<job_id>/nodes/match/review/decision.legacy_reviewed*.md`

## Run all available jobs from artifacts

Preview plan only:

```bash
python -m src.cli.run_available_jobs --source tu_berlin --dry-run
```

Execute continuation:

```bash
python -m src.cli.run_available_jobs \
  --source tu_berlin \
  --profile-evidence data/reference_data/profile/base_profile/profile_base_data.json
```

## What the command does

Per job:

1. If `nodes/match/approved/state.json` is missing, runs `match -> review_match`.
2. If reviewed decision is `approve`, marks the prep flow as terminal complete.
3. If reviewed decision is `reject`, stops at terminal reject route.
4. If reviewed decision is `request_regeneration`, runs regeneration (`match` with round feedback) and reopens a fresh review round.
5. If no decision is marked, leaves job in `pending_review`.

This path is checkpoint-independent and uses current artifacts as the source of truth.

## Verification

After execution, verify per affected job:

- `nodes/match/review/decision.md` exists and is updated for current round.
- `nodes/match/review/decision.json` exists.
- `nodes/match/review/rounds/round_<NNN>/feedback.json` exists when reviewed decisions were parsed.
- New rounds are created for regeneration jobs.

## Notes

- This command does not delete or overwrite your legacy reviewed file backups.
- If LLM dependencies/credentials are missing, jobs that require `match` execution will fail closed with explicit per-job errors.
