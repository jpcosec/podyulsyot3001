# Unified Automation Refactor Plan

Date: 2026-04-03

## Goal

Replace the current split between `src/scraper/` and `src/apply/` with one unified automation package and one common entrypoint, organized around execution interfaces instead of historical module boundaries.

The target concept is:

```text
<automation-package>/
  main.py                  # common CLI entrypoint
  motors/                  # execution mechanisms/backends
    crawl4ai/              # scraping + browser-driven apply helpers using Crawl4AI
    browseros/
      cli/                 # BrowserOS MCP/direct-tool execution path
      agent/               # BrowserOS/OpenBrowser agent path
    os_native_tools/       # physical click/input + ultra-stealth primitives
  ariadne/                 # path map, recording, storage, replay contracts
  portals/                 # xing/stepstone/linkedin/tuberlin-specific logic
```

## Directory meanings and what moves where

This section exists specifically to remove ambiguity before any code move begins.

### automation main entrypoint

- the unified runtime CLI for low-level automation concerns
- owns subcommands such as scrape/apply/ariadne
- does not own LangGraph operator workflow; that can stay in `src/cli/main.py`

### portals

- source-specific knowledge, independent of execution mechanism
- examples:
  - URL/routing conventions
  - source capability declarations
  - source-specific scraping hints
  - source-specific apply intent
  - source-specific Ariadne path naming
- this is where XING, StepStone, LinkedIn, and TUBerlin stop being tied to one motor

### Ariadne package

- the canonical source of truth for path knowledge
- owns:
  - playbook/path schema
  - recording normalization
  - replay contracts
  - branch/dead-end metadata
  - storage/promotion rules
- this is not BrowserOS-specific; BrowserOS is one producer/consumer of Ariadne artifacts

### `motors/crawl4ai`

- execution and extraction logic implemented with Crawl4AI
- owns browser configs, crawl/apply engines, and any motor-specific contracts needed for Crawl4AI execution
- it should consume source definitions from `portals/` and path definitions from `ariadne/`

### `motors/browseros/cli`

- deterministic BrowserOS MCP tool-calling path
- owns direct client/executor/backend code
- consumes Ariadne replay artifacts

### `motors/browseros/agent`

- higher-level BrowserOS/OpenBrowser agent path
- owns recording/discovery workflows and agent-specific prompting/contracts
- produces Ariadne-compatible recordings and possibly consumes Ariadne for assisted replay

### `motors/os_native_tools`

- physical/native interaction primitives and stealth-oriented mechanisms
- examples:
  - native mouse click
  - native typing
  - coordinate-based interaction
  - ultra-stealth mode primitives
- this is an escalation motor, not the default path

## Where current non-code assets should go

These decisions should be documented before moving anything.

### Current `plan_docs/applying/traces/`

- these are design/reference traces, not runtime code assets
- recommended destination:
  - keep design/reference material under planning docs, for example `plan_docs/automation/ariadne/traces/`
- rule:
  - if a trace is only documentation or exploratory evidence, keep it in docs
  - if a trace becomes a normalized runtime replay asset, move or copy the normalized form into the Ariadne runtime asset area

### Current packaged runtime playbooks

- example: `src/apply/playbooks/linkedin_easy_apply_v1.json`
- recommended destination:
  - the Ariadne runtime trace area or a nearby runtime asset folder under Ariadne
- reason:
  - packaged replay paths belong to Ariadne, not to BrowserOS specifically

### Current `scrapping_schemas/`

- these are Crawl4AI-specific extraction schema caches
- recommended destination:
  - keep them outside docs and outside Ariadne
  - move them under a Crawl4AI-owned location, such as a motor-local `schemas/` folder if they are shipped with code, or a runtime/data-owned schema cache path if they are environment-generated
- principle:
  - extraction schemas are motor-specific, not Ariadne artifacts

### Current planning docs under `plan_docs/applying/`

- these should remain documentation, not runtime code
- recommended destination over time:
  - `plan_docs/automation/` with subfolders for `ariadne/`, `browseros/`, `crawl4ai/`, and `migration/`
- this documentation move should happen before or alongside the code move so the code migration has a stable written reference

The user explicitly chose a **hard move now** strategy, not a compatibility-first shim phase.

## What exists today

- Scraping lives in `src/scraper/` and is Crawl4AI-based.
- Applying lives in `src/apply/`.
- BrowserOS runtime code already exists only in the apply path:
  - `src/apply/browseros_client.py`
  - `src/apply/browseros_models.py`
  - `src/apply/browseros_executor.py`
  - `src/apply/browseros_backend.py`
- Ariadne exists today only as a partial concept:
  - typed playbook fields such as `ariadne_tag`
  - one packaged LinkedIn playbook
  - design docs in `plan_docs/applying/`
- Operator CLI already exists in `src/cli/main.py`, but scraping and applying also still have their own module CLIs.

## Architectural direction

### 1. Make interface the primary axis

The new package should be organized by execution interface, not by old stage names.

- `motors/crawl4ai/` = deterministic browser automation and page extraction
- `ariadne/` = canonical map of paths, recordings, playbooks, replay metadata, branch history
- `motors/browseros/cli/` = direct MCP tool-calling path, no LLM
- `motors/browseros/agent/` = higher-level agent-driven path
- `motors/os_native_tools/` = lowest-level physical/device-native interaction and stealth tooling
- `portals/` = source-specific knowledge that each backend consumes

This keeps Ariadne as the source of truth above interfaces rather than burying it inside BrowserOS only.

### 2. Separate portal knowledge from execution backend

Portal-specific logic should move out of backend-specific folders where possible.

Target idea:

```text
<automation-package>/portals/
  xing/
    scrape.py
    apply.py
    ariadne/...
  stepstone/
  linkedin/
  tuberlin/
```

Then each runtime backend consumes the same portal-level intent/contracts.

### 3. Ariadne becomes the shared source of truth

Ariadne should own:

- playbook schema
- path naming and versioning
- known paths and dead ends
- recordings captured from BrowserOS agent/CLI sessions
- replay-ready normalized steps
- branch metadata and promotion workflow

Backend roles after refactor:

- Crawl4AI = execution/extraction backend
- BrowserOS CLI = execution backend
- BrowserOS agent = recording/discovery backend and optionally execution backend
- OS native tools = escalation backend when synthetic/browser-level actions are insufficient
- Ariadne = canonical contract and knowledge store used by all of them

## Proposed target layout

```text
<automation-package>/
  __init__.py
  main.py
  portals/
    xing/
      scrape.py
      apply.py
      routing.py
      ariadne/...
    stepstone/
      scrape.py
      apply.py
      routing.py
      ariadne/...
    linkedin/
      apply.py
      routing.py
      ariadne/...
    tuberlin/
      scrape.py
      routing.py
  ariadne/
    models.py
    storage.py
    recorder.py
    replayer.py
    promotion.py
    traces/
  motors/
    crawl4ai/
      scrape_engine.py
      apply_engine.py
      schema_cache.py
      contracts.py
    browseros/
      cli/
        client.py
        executor.py
        backend.py
        contracts.py
      agent/
        client.py
        prompting.py
        recorder.py
        backend.py
        contracts.py
    os_native_tools/
      clicks.py
      keyboard.py
      stealth.py
      backend.py
      contracts.py
```

Note on `registry.py`:

- the earlier draft used `registry.py` as a placeholder for backend/provider lookup.
- based on feedback, that does not need to be a dedicated top-level file yet.
- backend and portal selection can initially live in the automation main entrypoint until a clearer shape emerges from the documentation phase.

## CLI target

Move toward one automation main entrypoint with subcommands such as:

```text
automation scrape ...
automation apply ...
automation route ...
automation ariadne record ...
automation ariadne replay ...
automation ariadne inspect ...
```

Recommended command model:

- `automation scrape --source stepstone ... --backend crawl4ai`
- `automation apply --source linkedin ... --backend browseros-cli`
- `automation apply --source xing ... --backend crawl4ai`
- `automation ariadne replay --source linkedin --path linkedin.easy_apply.standard`

Backend names should become explicit and stable:

- `crawl4ai`
- `browseros-cli`
- `browseros-agent`
- `os-native`

## Migration plan

### Phase 0 - Document what exists now first

Before moving code, create and consolidate documentation for the current state.

This phase should produce:

- current code map for scraping/applying/BrowserOS/Ariadne
- current CLI map
- current test map
- current docs map
- current artifact/data-plane map
- gap list: implemented vs planned vs missing
- target directory glossary explaining what each future folder means
- asset-placement document explaining where traces, packaged playbooks, and Crawl4AI schemas belong

Reason:

- this reduces migration errors and makes the hard move easier because every existing responsibility is named before relocation

Mandatory rule for implementation start:

- no runtime move should begin until the directory glossary and asset-placement document are written and approved

### Phase 1 - Freeze target contracts in docs

Define before code moves:

- final package tree
- common CLI command surface
- Ariadne ownership boundaries
- portal adapter boundaries
- naming conventions for backends and paths

Deliverable:

- this approved plan becomes the implementation contract

### Phase 2 - Define contracts in Ariadne and each motor

Create shared contracts before moving implementations.

Must define:

- Ariadne path/playbook/storage contracts in the Ariadne package
- Crawl4AI engine contracts in the Crawl4AI motor
- BrowserOS CLI contracts in the BrowserOS CLI motor
- BrowserOS agent contracts in the BrowserOS agent motor
- OS-native contracts in the OS-native motor

Reason:

- without common contracts, the hard move will just relocate code without reducing coupling

### Phase 3 - Create the automation package and move the entrypoint

Actions:

- create the automation main entrypoint
- move provider/backend lookup logic from `src/scraper/main.py` and `src/apply/main.py` into the common entrypoint layer
- define one parser/subcommand tree for scrape/apply/ariadne
- decide whether `src/cli/main.py` delegates into the automation main entrypoint or remains a higher-level operator CLI only

Recommendation:

- keep `src/cli/main.py` as the operator control-plane CLI
- make the automation main entrypoint the runtime automation CLI
- let `src/cli/main.py` call into automation services rather than duplicating scraping/apply argument logic

### Phase 4 - Move shared models and persistence

Actions:

- move Ariadne-neutral models into the Ariadne package or the relevant motor folder
- keep motor-specific contracts within each motor folder, not in one root `contracts/` package
- centralize artifact-path conventions for scrape/apply/ariadne traces
- define where Ariadne runtime artifacts live on disk

Recommendation for data plane:

```text
data/jobs/<source>/<job_id>/nodes/
  ingest/
  apply/
  ariadne/
```

Where:

- `ingest/` remains job discovery/detail artifacts
- `apply/` remains apply execution artifacts
- `ariadne/` stores normalized traces, known paths, branch decisions, and replay metadata

### Phase 5 - Move Crawl4AI engines out of stage folders

Actions:

- move `src/scraper/smart_adapter.py` concepts into the planned Crawl4AI scrape engine
- move `src/apply/smart_adapter.py` concepts into the planned Crawl4AI apply engine
- move provider-specific scraping/applying logic into the planned portals area

Important split:

- engine files own backend mechanics
- portal files own selectors, routing logic, and source-specific quirks

### Phase 6 - Promote Ariadne into a real subsystem

Actions:

- move `src/apply/browseros_models.py` concepts into the planned Ariadne models module
- move packaged playbooks into the Ariadne runtime trace area or equivalent runtime asset folder
- define storage and promotion flow for known-good paths
- define how BrowserOS recordings normalize into Ariadne paths
- define how Crawl4AI and BrowserOS both consume Ariadne replay plans

Core principle:

- BrowserOS should not own the playbook schema; Ariadne should

### Phase 7 - Split BrowserOS into CLI and agent layers

Actions:

- move direct MCP code to the planned BrowserOS CLI motor
- reserve the planned BrowserOS agent motor for agent-driven workflows and recording
- make both produce/consume Ariadne contracts

Responsibilities:

- `motors/browseros/cli/` = deterministic tool-by-tool execution
- `motors/browseros/agent/` = path discovery/recording and possibly adaptive execution

### Phase 8 - Add OS-native escalation layer

Actions:

- create the planned OS-native tools motor
- define minimal backend contract for physical click/type/upload primitives
- make it an escalation backend, not the default path

Important guardrail:

- stealth/physical-input behavior must remain explicitly opt-in and isolated from normal deterministic paths

### Phase 9 - Move portal implementations

Actions:

- move XING/StepStone/LinkedIn/TUBerlin source logic into the planned portals area
- separate per-source capabilities:
  - discovery scraping
  - application routing
  - apply flow definitions
  - Ariadne path registry

### Phase 10 - Remove old packages and update imports

Because the user requested a hard move now:

- remove `src/scraper/` runtime ownership after migration
- remove `src/apply/` runtime ownership after migration
- update imports across tests, docs, and CLIs to point at the new automation package
- update README/module docs/changelog together in the same change window

## Recommended execution order inside the hard move

1. Finalize contracts and target tree
2. Create the automation main entrypoint and common command surface
3. Move Ariadne schema out of BrowserOS-specific files
4. Move BrowserOS CLI implementation under `motors/browseros/cli/`
5. Move Crawl4AI scraper/apply engines under `motors/crawl4ai/`
6. Move portal source logic under `portals/`
7. Wire disk layout for Ariadne artifacts
8. Update tests to new imports and command surface
9. Remove old `src/scraper` and `src/apply`
10. Update docs and changelog comprehensively

## Main tradeoffs

### Benefits

- one mental model for browser automation
- Ariadne becomes reusable across all interfaces
- avoids duplicating portal knowledge across backends
- creates a clean place for future OS-native escalation

### Costs

- hard move will break imports, docs, and tests until the migration is fully finished
- current Crawl4AI scraper and apply logic are not yet contract-aligned, so some code will need reshaping, not just moving
- BrowserOS agent and OS-native layers are still mostly conceptual, so the folder tree may get ahead of implementation unless phased carefully

## Risks to manage

### Risk 1 - Conflating discovery scraping and apply execution too early

Mitigation:

- unify them under one package, but keep separate contracts for discovery vs apply execution

### Risk 2 - Ariadne becomes BrowserOS-coupled again

Mitigation:

- place schema/storage/replay under Ariadne, never under `browseros/`

### Risk 3 - Portal logic gets duplicated across backend folders

Mitigation:

- centralize portal knowledge under the planned portals area

### Risk 4 - Hard move creates a long broken window

Mitigation:

- execute in a branch with short, internally coherent commits per phase
- require tests for each migrated slice before deleting the old location

### Risk 5 - OS-native layer expands scope too early

Mitigation:

- define backend contract now, implement only minimal stub/escalation path later

## Acceptance criteria for the refactor

- current-state documentation exists and is approved before code movement begins
- one runtime automation package exists under the new automation namespace
- one common runtime entrypoint exists under that automation package
- old `src/scraper/` and `src/apply/` are no longer the primary runtime homes
- Ariadne contracts/storage live in a backend-neutral location
- BrowserOS CLI runtime consumes Ariadne contracts from that neutral location
- Crawl4AI scraping and applying consume shared portal definitions from the planned portals area
- docs clearly explain the new package map and command surface

## Concrete next planning outputs to create after approval

1. package tree spec for the automation package
2. CLI command spec for `automation scrape/apply/ariadne`
3. Ariadne storage/schema spec
4. migration checklist mapping old files to new files
5. test migration matrix
