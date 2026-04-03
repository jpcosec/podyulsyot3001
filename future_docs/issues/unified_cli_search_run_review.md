# Unified CLI Search Run Review

## Goal

Create a coherent operator workflow from the CLI that supports:

1. searching for jobs by query + city across one or more sources
2. starting LangGraph pipeline runs for selected or batched jobs
3. launching the review TUI against the same LangGraph API environment

The end state should feel like one control plane, not several disconnected commands.

## Current State

The repository already has most of the building blocks, but they do not compose into the desired workflow yet.

### What exists

- `postulator scrape` accepts `--job-query` and `--city`, but only for a single `--source` at a time in `src/cli/main.py:67`
- `postulator pipeline` starts one run for one `source + job_id` in `src/cli/main.py:46`
- `LangGraphAPIClient.invoke_pipeline()` starts one remote pipeline run per job in `src/core/api_client.py:185`
- `postulator review` launches the TUI in `src/cli/main.py:338`
- `scripts/postulator.sh` already starts or reuses `langgraph dev` and then launches the TUI in `scripts/postulator.sh:20`
- the explorer screen can browse threads from the API in `src/review_ui/screens/explorer_screen.py:101`

### What is broken or missing

- no CLI command accepts multiple sources for search
- no CLI command chains discovery results into batch LangGraph runs
- no batch selection layer exists between scrape results and `invoke_pipeline()`
- `review` claims explorer mode is optional, but `_run_review()` still constructs `thread_id = f"{args.source}_{args.job_id}"` unconditionally in `src/cli/main.py:353`
- the search, API, batch run, and TUI pieces are documented separately rather than as one operator workflow

## Desired Workflow

### Operator flow

1. search once with:
   - job query
   - city
   - one or more sources
2. inspect results
3. choose which jobs to process
4. ensure LangGraph API is available
5. start pipeline runs for each selected job
6. open the TUI explorer or a direct review screen to continue the HITL loop

### Example target UX

```bash
postulator search --job-query "data scientist" --city berlin --sources xing stepstone tuberlin
postulator run-batch --sources xing stepstone --limit 10 --profile-evidence profile.json
postulator review
```

Or, if search and run are combined:

```bash
postulator search-run --job-query "data scientist" --city berlin --sources xing stepstone --limit 10
postulator review
```

## Architectural Decisions

### 1. Keep search and run as distinct concepts

Search/discovery and pipeline execution are different concerns.

- search produces candidate ingested jobs
- run-batch turns selected ingested jobs into LangGraph threads

We may later add a convenience command that combines them, but the underlying architecture should keep them separate.

### 2. Treat LangGraph API as the default control plane for batch work

For single-job local fallback, the current local execution path can remain.

For operator workflows involving many jobs and later TUI review, the CLI should prefer:

- ensure API is running
- create or reuse threads
- invoke runs remotely

This keeps the TUI explorer and the batch runner pointed at the same persistence layer.

### 3. Make review explorer mode real

`postulator review` without `--source/--job-id` should open the explorer cleanly.

Direct review of a single job should remain supported, but must be a separate branch from explorer mode instead of assuming both modes use the same setup path.

## Planned Commands

### Command A: `search`

Purpose:

- run discovery ingestion for one or more sources with shared filters

Minimum inputs:

- `--job-query`
- `--city`
- `--sources` (one or more)

Optional inputs:

- `--limit`
- `--overwrite`
- source-specific filters like `--categories`

Output:

- canonical ingested jobs in `data/jobs/...`
- a concise CLI summary of new/updated jobs per source

### Command B: `run-batch`

Purpose:

- launch LangGraph pipeline runs for existing ingested jobs

Minimum inputs:

- one or more sources and a selection policy

Selection policy options could include:

- explicit `--job-ids`
- `--limit N` newest jobs per source
- `--status` filter from data root metadata if needed later

Runtime behavior:

- ensure LangGraph API is reachable
- create/reuse thread ids using `source_jobid`
- invoke the remote pipeline for each selected job
- print a run summary

### Command C: `review`

Purpose:

- launch TUI in explorer mode or direct job mode

Modes:

- no `--source/--job-id` => explorer mode
- with both `--source` and `--job-id` => direct review mode

Behavior:

- prefer active LangGraph API
- if launched from helper script, use the same API URL

### Optional Command D: `api`

Purpose:

- explicitly start or validate the LangGraph dev server instead of relying only on shell scripts

This is optional but may reduce operational ambiguity and make the workflow more self-contained.

## Implementation Stages

### Stage 1: Fix review mode split

Refactor `postulator review` so explorer mode and direct review mode are distinct and both actually work.

Acceptance criteria:

- `postulator review` opens explorer mode without requiring thread_id construction
- `postulator review --source ... --job-id ...` opens direct review mode

### Stage 2: Add multi-source search command

Extend CLI search/scrape behavior to accept one or more sources with shared search filters.

Acceptance criteria:

- one command can run discovery across multiple sources
- results are summarized per source

### Stage 3: Add batch pipeline invocation

Build a CLI command that selects ingested jobs and invokes LangGraph API runs for each.

Acceptance criteria:

- operator can start multiple pipeline runs without manually invoking one job at a time
- batch runner uses the same thread id convention as the TUI explorer

### Stage 4: Unify API startup story

Decide whether API startup remains shell-script owned or becomes a first-class CLI capability.

Recommended direction:

- keep `scripts/postulator.sh` for convenience
- add a CLI-visible API check/start path or at least document the official flow clearly

Acceptance criteria:

- there is one documented primary path to get API + batch runs + review working together

### Stage 5: Documentation rewrite for operator workflow

Update docs so the official workflow is explicit.

Must update:

- `README.md`
- `src/review_ui/README.md`
- CLI docs where appropriate

Acceptance criteria:

- a user can understand the intended search -> run -> review flow from the docs alone

## Open Questions

1. Should `search` only ingest jobs, or should it also print a selectable shortlist that `run-batch` can reuse?
2. Should batch selection be by newest jobs, explicit ids, or both from the start?
3. Do we want CLI-based API startup inside `postulator`, or do we keep scripts as the only startup mechanism?
4. Should `run-batch` support `--profile-evidence` and other pipeline input refs globally, or require those to be pre-materialized on disk?

## Risks

- source-specific filters do not map cleanly across all providers
- mixing local fallback and remote API semantics in batch mode may create confusing partial behavior
- explorer mode assumptions in `review_ui` may still depend on API-only metadata patterns

## Recommended Order

1. fix `review` explorer/direct split
2. add multi-source search
3. add batch pipeline invocation
4. tighten API startup story
5. update docs

## Validation Plan

Verify at least these workflows:

1. `postulator review` opens explorer mode with API available
2. `postulator review --source xing --job-id 12345` opens direct review mode
3. multi-source search runs across at least two providers with shared `job_query` and `city`
4. batch run creates threads visible in the explorer
5. jobs launched through batch mode can be resumed via the TUI review flow
