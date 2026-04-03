# Automation Directory Glossary

Status: pre-migration reference for the unified automation refactor.

This document defines what each target directory means before any runtime move.

## Root

### automation package

- future runtime home for low-level automation concerns currently split across `src/scraper/` and `src/apply/`
- should unify scrape, apply, Ariadne replay, and backend selection
- should not absorb the whole operator control plane from `src/cli/main.py`

### automation main entrypoint

- unified runtime CLI for automation work
- expected responsibilities:
  - `scrape`
  - `apply`
  - `ariadne inspect`
  - `ariadne replay`
  - `ariadne record`
- should orchestrate motors and portals, not embed source-specific logic directly

## Source definitions

### portals

- source-specific knowledge that should be reusable across all motors
- each portal folder should hold the source truth for:
  - scrape intent and scrape-specific hints
  - apply intent and source-specific form/routing rules
  - application routing logic
  - Ariadne path naming conventions
  - source capability declarations

Example shape:

```text
<automation-package>/portals/xing/
  scrape.py
  apply.py
  routing.py
  ariadne/
```

### portal `scrape.py`

- portal-level scrape definitions
- does not own Crawl4AI mechanics; it feeds the Crawl4AI motor

### portal `apply.py`

- portal-level apply definitions
- does not own BrowserOS or Crawl4AI engine mechanics; it feeds those motors

### portal `routing.py`

- application-routing logic for the source
- should answer whether the job is email apply, inline apply, external ATS, or unsupported

### portal `ariadne/`

- source-local Ariadne references and path registration metadata
- useful for naming, grouping, and source-level organization
- the canonical Ariadne schema/storage still belongs to the top-level Ariadne package

## Ariadne

### Ariadne package

- backend-neutral source of truth for path knowledge
- owns canonical replay/recording concepts
- must not be owned by BrowserOS, Crawl4AI, or any one source

### Ariadne `models.py`

- canonical path/playbook schema
- should absorb the generalized parts of the current BrowserOS playbook models

### Ariadne `storage.py`

- disk layout for normalized Ariadne artifacts
- versioning, naming, and source/job/path resolution helpers

### Ariadne `recorder.py`

- normalization layer from raw backend recordings to canonical Ariadne paths
- should accept BrowserOS CLI recordings, BrowserOS agent recordings, and future OS-native traces

### Ariadne `replayer.py`

- backend-neutral replay planning layer
- prepares replayable steps for execution motors

### Ariadne `promotion.py`

- rules for path promotion from exploratory/draft to known-good/canonical

### Ariadne `traces/`

- packaged runtime Ariadne paths and normalized replay assets that ship with code
- not for large exploratory screenshots or note dumps

## Motors

### motors

- execution mechanisms/backends
- motors consume portal definitions and Ariadne contracts
- a motor may record, replay, scrape, apply, or escalate, but it should not become the source of truth for path knowledge

### `motors/crawl4ai`

- Crawl4AI-specific runtime logic
- owns:
  - browser configs
  - scrape engine
  - apply engine for deterministic browser automation
  - Crawl4AI-specific schema cache logic
  - Crawl4AI-specific contracts
- does not own Ariadne schema

### Crawl4AI `scrape_engine.py`

- backend implementation for discovery/detail ingestion
- likely destination for the shared mechanics currently in `src/scraper/smart_adapter.py`

### Crawl4AI `apply_engine.py`

- backend implementation for deterministic apply flows
- likely destination for the shared mechanics currently in `src/apply/smart_adapter.py`

### Crawl4AI `schema_cache.py`

- management of Crawl4AI extraction schemas now stored in `data/ariadne/assets/crawl4ai_schemas/`

### Crawl4AI `contracts.py`

- motor-specific contracts only
- examples: extraction schema wrapper, browser session options, Crawl4AI result adapters

### `motors/browseros/cli`

- deterministic BrowserOS MCP execution path
- owns:
  - direct MCP client
  - deterministic executor
  - BrowserOS CLI-specific contracts
- should consume Ariadne replay assets, not define the canonical path schema

### `motors/browseros/agent`

- BrowserOS/OpenBrowser agent-driven path
- owns:
  - agent prompting
  - recording/discovery flow
  - agent-specific contracts
- should produce Ariadne-compatible recordings

### `motors/os_native_tools`

- physical/native interaction motor
- intended for escalation when browser-level actions are insufficient or detectable
- examples:
  - native click
  - native typing
  - coordinate-based interactions
  - ultra-stealth primitives
- should remain explicit and opt-in

### motor-local `contracts.py`

- contracts that are specific to that motor only
- this avoids a misleading giant shared `contracts/` folder at the package root

## Documentation homes

### `plan_docs/automation/`

- planning and reference docs for the automation refactor
- should hold migration docs, glossary docs, asset-placement rules, and conceptual design docs

### `plan_docs/automation/ariadne/`

- documentation for Ariadne concepts, storage rules, replay semantics, and promotion workflow

### `plan_docs/automation/browseros/`

- documentation for BrowserOS MCP interfaces, BrowserOS agent path, and operational notes

### `plan_docs/automation/crawl4ai/`

- documentation for Crawl4AI usage, schema strategy, and backend-specific behavior

## Non-goals for the target tree

- the future automation package should not swallow unrelated LangGraph pipeline code
- Ariadne should not be nested under BrowserOS
- `data/ariadne/assets/crawl4ai_schemas/` is a temporary practical home and should be revisited during the automation refactor
- exploratory screenshots and note-heavy traces should not live inside runtime code folders
