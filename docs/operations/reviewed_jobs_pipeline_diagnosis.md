# Diagnosis: Resume Failures for Reviewed Jobs

Date: 2026-03-11

## Scope

This diagnosis covers reviewed `prep_match` jobs under:

- `data/jobs/tu_berlin/201578`
- `data/jobs/tu_berlin/201588`
- `data/jobs/tu_berlin/201601`
- `data/jobs/tu_berlin/201606`
- `data/jobs/tu_berlin/201661`
- `data/jobs/tu_berlin/201695`

## Reported issue

Running the pipeline for already reviewed jobs fails when attempting to continue from the review gate.

## Reproduction evidence

### 1) CLI resume currently fails in current shell context

Command:

```bash
python -m src.cli.run_prep_match --source tu_berlin --job-id 201588 --resume
```

Observed error:

```text
ModuleNotFoundError: No module named 'langgraph'
```

Important context from `docs/operations/agent_entrypoint.md`:

- expected env is `conda activate phd-cv`
- expected preflight is `set -a; source .env; set +a`

So this symptom is treated as an environment preflight miss in the tested shell, not as a repository code defect by itself.

### 2) Review node fails closed on reviewed files

Running `src/nodes/review_match/logic.py` directly against current reviewed artifacts fails for all scoped jobs with:

```text
ValueError: decision.md is missing source_state_hash; regenerate review markdown from current nodes/match/approved/state.json and re-apply decisions
```

### 3) Data-plane and control-plane state snapshot

For all scoped reviewed jobs:

- `nodes/match/review/decision.md` exists
- decision checkboxes are already marked (`[x]` variants)
- `source_state_hash` front matter is missing
- `nodes/match/review/decision.json` does not exist
- `nodes/match/review/rounds/round_*/feedback.json` does not exist
- `graph/checkpoint.sqlite` exists but `checkpoints` and `writes` table row counts are `0`

## Root cause analysis

## 1) Review artifact contract mismatch (primary)

Current review gate logic in `src/nodes/review_match/logic.py` requires `source_state_hash` locking for edited decisions.

Existing reviewed files were generated in an earlier format (no front matter hash), then manually edited. This triggers intentional fail-closed behavior:

- missing hash + checked decisions => hard error

This prevents applying human decisions to potentially stale match payloads.

## 2) Missing checkpoint history for resume (secondary)

`run_prep_match --resume` depends on persisted LangGraph checkpoint state (`thread_id = f"{source}_{job_id}"`) to wake from interrupt before `review_match`.

Current per-job sqlite files have schema but no checkpoint rows, so there is no recorded interrupt state to resume from.

## 3) Runtime dependency preflight not satisfied in tested shell (secondary)

The tested shell did not satisfy the runtime preconditions documented in `docs/operations/agent_entrypoint.md` (notably `phd-cv` + `.env` export), so resume exited before graph execution started.

## Why this affects reviewed jobs specifically

The guard is asymmetric by design:

- Legacy file with no hash and no marked decisions -> allowed to regenerate safely.
- Legacy file with no hash and marked decisions -> blocked, requiring regeneration plus manual re-application.

Your reviewed jobs are in the second category.

## Recommended recovery plan

Implemented helper for safe migration:

- `python -m src.cli.migrate_review_hash_lock --source <source> --job-id <id> [--job-id <id> ...]`
- use `--dry-run` first to preview actions.

Implemented checkpoint-independent continuation runner:

- `python -m src.cli.run_available_jobs --source <source> --dry-run`
- `python -m src.cli.run_available_jobs --source <source> --profile-evidence <path_to_profile_json>`

## Phase A - unblock execution environment

1. Install runtime dependencies (at minimum `langgraph`) in the active environment.
2. Verify import path with a dry check before rerunning CLI.

## Phase B - migrate reviewed jobs to hash-locked review artifacts

For each affected job:

1. Back up current reviewed file:
   - `nodes/match/review/decision.md` -> `nodes/match/review/decision.legacy_reviewed.md`
2. Regenerate a fresh hash-bearing `decision.md` from current `nodes/match/approved/state.json`.
3. Re-apply reviewer decisions/comments onto the regenerated file.
4. Resume and verify `decision.json` and `feedback.json` are produced.

Note: because checkpoint tables are empty, safest operational path is to rerun prep stages for each job (non-resume) to recreate valid checkpoint history and fresh review artifacts, then re-apply decisions.

## Verification checklist after recovery

For each job, confirm:

1. `nodes/match/review/decision.md` contains front matter with `source_state_hash`.
2. Review resume no longer raises hash-related `ValueError`.
3. `nodes/match/review/decision.json` exists.
4. `nodes/match/review/rounds/round_<NNN>/feedback.json` exists.
5. `graph/checkpoint.sqlite` has non-zero rows in `checkpoints` after a successful graph run.

## Preventive actions

1. Add a one-off migration utility for legacy `decision.md` files (pre-hash format) before running resume in mixed-version data folders.
2. Add an operator preflight command that checks:
   - dependency imports,
   - checkpoint row presence,
   - review hash-lock readiness.
3. Keep compatibility notes explicit when review markdown schema changes.

## Applied recovery (2026-03-11)

The hash-lock migration was applied to reviewed TU Berlin jobs:

- `201578`
- `201588`
- `201601`
- `201606`
- `201661`
- `201695`

For each job:

- `nodes/match/review/decision.md` now includes front matter with `source_state_hash`.
- backup of the original reviewed file exists as `nodes/match/review/decision.legacy_reviewed.md`.
- deterministic parsing produced `nodes/match/review/decision.json` and `nodes/match/review/rounds/round_001/feedback.json`.

Batch continuation was then executed with:

- `python -m src.cli.run_available_jobs --source tu_berlin --profile-evidence data/reference_data/profile/base_profile/profile_base_data.json`

Observed outcomes:

- `201661` reached terminal complete route (`approve`).
- `201578`, `201588`, `201601`, `201606`, and `201695` advanced through regeneration and reopened review as new `round_002` pending review.
- `201637` completed first match generation and is now pending first review (`round_001`).
