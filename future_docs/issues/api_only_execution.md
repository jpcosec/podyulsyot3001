# API-Only Execution: Remove Local SQLite Fallbacks

**Why deferred:** Not blocking current development. The API path works correctly; the fallback is just dead/broken weight.
**Last reviewed:** 2026-03-29

## Problem

Both `pipeline` and `review` CLI commands implement a two-path execution model: try the LangGraph API first, fall back to local SQLite if unreachable. This fallback is broken and causes state divergence.

### Broken local fallback in `_run_review` (`src/cli/main.py`)

```python
app = build_match_skill_graph(checkpointer=None)  # compiled without checkpointer
app.checkpointer = checkpointer                    # silently ignored — too late
```

LangGraph bakes the checkpointer in at `compile()` time. Setting it afterward has no effect. The fallback runs without persistence — threads are lost on exit.

### Split state problem

The LangGraph API server manages its own thread database. The local fallback uses a separate `data/jobs/checkpoints.db`. These two stores never sync. A thread started via the API cannot be resumed by the local fallback and vice versa. This is what produced the stale `tuberlin_201665` checkpoint: a partial `review_payload` update was written to the local DB, but the full thread state only ever lived in the API.

### Explorer mode bug

`_run_review` always computes `thread_id = f"{args.source}_{args.job_id}"` even in explorer mode where both are `None`, producing `thread_id = "None_None"`.

## Intended Architecture

The LangGraph API server is the single source of truth for all graph state. The CLI is a thin HTTP client. There is no local execution path.

- If the API is unreachable → fail fast with a clear error message.
- `data/jobs/checkpoints.db` is no longer written or read by the CLI.
- `build_match_skill_graph` is only called by the API server (via `langgraph.json`), not by the CLI.

## Fix

1. Remove the local SQLite fallback block from `_run_pipeline`.
2. Remove the local SQLite fallback block from `_run_review` (including the broken `app.checkpointer` assignment and the `build_match_skill_graph` import).
3. In `_run_review`, skip `thread_id` construction when source/job_id are absent (explorer mode).
4. Replace all fallback `except` blocks with a single `LangGraphConnectionError` surfaced to the user.
5. Delete `data/jobs/checkpoints.db` from the repo (or add to `.gitignore`).

## `LangGraphAPIClient.ensure_server`

The `api_client.py` already has `ensure_server()` which can auto-start `langgraph dev` if not running. The CLI commands could call this instead of the current ping-then-fallback pattern, making the API server a transparent prerequisite rather than an optional dependency.
