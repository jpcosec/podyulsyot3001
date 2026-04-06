# Automation Architecture

Navigation guide to the automation system's design concepts and their implementation homes.

## Core design principle

Portal knowledge (what fields exist, what steps a flow has) is separated from execution mechanics (how to interact with those fields in a browser). The boundary between them is the **Ariadne portal schema** defined in `src/automation/ariadne/portal_models.py`.

This separation means adding a second execution backend for an existing portal requires no changes to the portal intent files — only a new motor translator.

## Where to read more

| Topic | Where |
|---|---|
| Package layout, boundary rules, data flows, how to extend | `src/automation/README.md` |
| Ariadne portal schema (the boundary models) | `src/automation/ariadne/portal_models.py` |
| C4AI motor base classes | `src/automation/motors/crawl4ai/scrape_engine.py`, `apply_engine.py` |
| Open design issues for Ariadne Phase 2 | `plan_docs/automation/2026-04-04-ariadne-common-language-issues.md` |
| Motor concepts and future motors | `plan_docs/motors/`, `plan_docs/ariadne/` |
| Crawl4AI usage rules | `docs/standards/code/crawl4ai_usage.md` |
| Ingestion boundary rules | `docs/standards/code/ingestion_layer.md` |

## What is deferred

Phase 1 (complete) established the Ariadne portal schema and moved all runtime code under `src/automation/`. The following are Phase 2:

- Ariadne storage, recorder, replayer, and promotion (only `portal_models.py` exists today)
- BrowserOS playbook generation from `ApplyPortalDefinition` (today it replays a pre-recorded trace)
- `portals/*/routing.py` — application routing (email vs. inline vs. ATS)
- BrowserOS agent motor, OS-native tools motor, vision motor — conceptual only
