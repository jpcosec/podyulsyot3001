# BrowserOS Chat Runtime Support Statement

This document states the current runtime support level for BrowserOS `/chat`
within this repository.

## Scope

This statement applies only to workflows that intentionally depend on
BrowserOS `/chat`, mainly Level 2 trace capture and related exploratory agent
flows.

It does **not** apply to scrape rescue, which is MCP-first.

## Current Support Classification

| Workflow | Current support level | Evidence |
| --- | --- | --- |
| Level 2 `/chat` SSE trace capture | `best-effort` | validated historically in `docs/reference/external_libs/browseros/live_agent_validation.md`; current direct probe in this session returned `503 Service Unavailable` |
| Exploratory direct `/chat` agent sessions | `best-effort` | prior live evidence shows successful SSE/tool events, but current availability is not guaranteed |
| MCP-first scrape rescue | `not applicable` | does not depend on `/chat` |

## Evidence Summary

- historical live evidence exists in
  `docs/reference/external_libs/browseros/live_agent_validation.md`
  - direct `/chat` accepted requests
  - SSE event streams were captured
  - tool-call events were observed in `mode=agent`
  - heavier use also showed `429 Too Many Requests`
- current session probe against `http://127.0.0.1:9000/chat`
  - returned `503 Service Unavailable`

## Practical Meaning

- `/chat` should be treated as available enough for exploratory/trace workflows
  when it responds, but not guaranteed as a stable production runtime surface
  for this repo.
- repo-critical runtime paths should continue to prefer MCP.
- any workflow that still depends on `/chat` should document that dependency as
  `best-effort` unless newer validation upgrades the support level.
