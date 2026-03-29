# Logging Layer Conflicts

**Why deferred:** Logging cleanup is important, but it is not the main blocker for the current API-backed pipeline execution.
**Last reviewed:** 2026-03-29

## Problem

The repository currently mixes multiple logging setup styles:

- ad-hoc `logging.basicConfig(...)` in CLI entry points
- `force=True` in some standalone module CLIs
- direct bracketed log strings in a few places instead of `LogTag`
- no single shared application logging configurator under `src/shared/`

This makes it harder to reason about how local CLI logs, module logs, and LangGraph dev logs interact.

## Why It Matters

- root logger configuration can be overridden unexpectedly
- module CLIs can stomp on each other's logging behavior
- observability output is inconsistent across the stack
- it is harder to separate our application logs from LangGraph / third-party logs

## Recommended Direction

Introduce a shared logging configuration layer under `src/shared/` and migrate entry points to it.

Likely steps:

1. add a shared logger/bootstrap utility
2. stop using `force=True` in module CLIs unless there is a strong reason
3. standardize on `LogTag` for application-level messages
4. keep third-party logs isolated from our application logger where possible
5. document the official logging model in the relevant READMEs
