# Match Review Regeneration Loop

This document explains how iterative review of `planning/match_proposal.md` works in the graph-coordinated run flow.

## Why this loop exists

Matcher output is human-reviewed. You can approve, edit, or reject requirement mappings and add inline feedback with HTML comments (`<!-- ... -->`).

When matching regenerates, the system should:

- keep approved items stable,
- remove rejected items,
- regenerate edited items with reviewer guidance,
- avoid stale Evidence IDs,
- preserve prior proposal rounds for traceability.

## End-to-end flow

1. Start pipeline run:

   ```bash
   python src/cli/pipeline.py job <job_id> run
   ```

2. Pipeline pauses at review gate when `planning/reviewed_mapping.json` is missing.

3. Review `planning/match_proposal.md`:
   - mark one decision per requirement (`approve`, `edit`, or `reject`),
   - add guidance under `Notes:` (or inline comments),
   - optionally provide final text in `Edited Claim:`.

4. Resume run:

   ```bash
   python src/cli/pipeline.py job <job_id> run --resume
   ```

   Resume auto-runs the review-lock step, writing `planning/reviewed_mapping.json`, then continues downstream.

5. If additional edits are needed, regenerate matching and repeat review:

   ```bash
   python src/cli/pipeline.py job <job_id> match --force
   python src/cli/pipeline.py job <job_id> run --resume
   ```

## What regeneration does

On regeneration, matcher receives both base context and review context from the previous round:

- prior proposal content,
- parsed reviewed claims,
- extracted reviewer comments.

Regeneration directives are interpreted per requirement:

- `approved` -> keep requirement claim stable,
- `rejected` -> remove requirement from proposal,
- `edited` -> regenerate evidence/claim with reviewer notes and edited claim context.

## Claim priority

Claim text is resolved with strict priority:

1. user-edited claim (`Edited Claim:`),
2. LLM-generated claim,
3. deterministic template fallback.

This ensures explicit reviewer wording is never overwritten by a later generation pass.

## Round file versioning

Before writing a new `planning/match_proposal.md`, the existing file is archived.

- first regeneration: `match_proposal.md` -> `match_proposal.round1.md`
- second regeneration: active `match_proposal.md` -> `match_proposal.round2.md`
- new output is always written as `match_proposal.md`

This keeps the original reviewed artifact fixed while newer rounds increment.

## Approval lock behavior

`planning/reviewed_mapping.json` is a lock tied to a specific proposal revision.

- during normal `run`, missing lock triggers review interrupt,
- `run --resume` recreates lock from reviewed proposal,
- regenerating `match` invalidates stale lock by deleting `planning/reviewed_mapping.json`.

Downstream nodes never proceed with stale approvals.

## Evidence ID hygiene

Evidence IDs can drift between rounds as extraction changes. During regeneration:

- IDs from current matcher output are preferred,
- fallback to prior reviewed IDs happens only if still valid,
- missing IDs are dropped,
- `Evidence IDs` and `Evidence` lines are rewritten using valid references only.

## Comment logging

Comments are logged per job in:

- `data/pipelined_data/<source>/<job_id>/.metadata/comments.jsonl`

Entries are appended from both `match` and review-lock passes with timestamp, file, line, text, and context.
