# Unified Automation Refactor — Design Spec

Date: 2026-04-06

## Goal

Move all runtime automation code under `src/automation/` with clear motor ownership and
explicit data contracts at each boundary. Portal adapters move as-is into the Crawl4AI motor
as reference implementations. The top-level `portals/` layer (Ariadne common language) is
deferred until the common language schema is defined — portal files will be rewritten then.

---

## Current state

Runtime automation is split across two packages with no shared boundary:

- `src/scraper/` — Crawl4AI scraping, 3 portals (stepstone, xing, tuberlin)
- `src/apply/` — two execution backends (Crawl4AI and BrowserOS), 3 portals (linkedin, xing,
  stepstone), separate CLI

Portal adapters in both packages mix portal knowledge (URLs, entry points, field names) with
motor-specific translation code (CSS selectors, C4A-Script DSL, `crawl_result` API calls).

---

## Target layout

```text
src/automation/
  __init__.py
  main.py                          # unified CLI (scrape / apply subcommands)
  motors/
    crawl4ai/
      scrape_engine.py             # ← src/scraper/smart_adapter.py
      apply_engine.py              # ← src/apply/smart_adapter.py
      models.py                    # ← src/scraper/models.py + src/apply/models.py
      schemas/                     # ← data/ariadne/assets/crawl4ai_schemas/*.json
        stepstone_schema.json
        tuberlin_schema.json
        xing_schema.json
      portals/                     # C4AI reference adapters (pending Ariadne rewrite)
        stepstone/
          scrape.py                # ← src/scraper/providers/stepstone/adapter.py (as-is)
          apply.py                 # ← src/apply/providers/stepstone/adapter.py (as-is)
        tuberlin/
          scrape.py                # ← src/scraper/providers/tuberlin/adapter.py (as-is)
        xing/
          scrape.py                # ← src/scraper/providers/xing/adapter.py (as-is)
          apply.py                 # ← src/apply/providers/xing/adapter.py (as-is)
        linkedin/
          apply.py                 # ← src/apply/providers/linkedin/adapter.py (as-is)
    browseros/
      cli/
        client.py                  # ← src/apply/browseros_client.py
        executor.py                # ← src/apply/browseros_executor.py
        backend.py                 # ← src/apply/browseros_backend.py
        models.py                  # ← src/apply/browseros_models.py
        traces/
          linkedin_easy_apply_v1.json  # ← src/apply/playbooks/linkedin_easy_apply_v1.json
  portals/                         # DEFERRED — Ariadne common language (not part of this refactor)
```

---

## Motor ownership

### Crawl4AI motor (`motors/crawl4ai/`)

Owns all execution mechanics that depend on the Crawl4AI library: `AsyncWebCrawler`,
`BrowserConfig`, `CrawlerRunConfig`, `crawl_result` API, C4A-Script DSL, CSS selectors, and
extraction schema files.

**Models (`motors/crawl4ai/models.py`):**

- `JobPosting` — structured extraction output from a scrape run
- `FormSelectors` — CSS selectors used to validate and interact with an apply form
- `ApplicationRecord` — persisted record of one apply attempt
- `ApplyMeta` — status artifact from one apply run

Both the scrape and apply sides live in the same `models.py` because they are both C4AI
artifacts. They represent different operations but are produced and consumed exclusively within
the Crawl4AI motor.

**Extraction schemas (`motors/crawl4ai/schemas/`):**

Source-controlled JSON schemas passed to the Crawl4AI extraction pipeline. These are C4AI
motor assets, not Ariadne artifacts.

**Portal reference adapters (`motors/crawl4ai/portals/`):**

Current portal adapters moved as-is. Each file contains the full Crawl4AI-specific
implementation for one portal: CSS selectors, C4A-Script blocks, URL builders, and
`crawl_result` parsing logic. These are reference implementations — they will be rewritten
once the Ariadne common language schema is defined and the top-level `portals/` layer exists.

### BrowserOS CLI motor (`motors/browseros/cli/`)

Owns all execution mechanics that depend on the BrowserOS MCP interface: MCP client, playbook
executor, BrowserOS tool-call schema, and packaged runtime traces.

**Models (`motors/browseros/cli/models.py`):**

- `BrowserOSPlaybook`, `PlaybookStep`, `PlaybookAction`, etc. — BrowserOS MCP tool-call schema

These are BrowserOS-specific. The playbook schema is a known future split point: Ariadne will
eventually own a backend-neutral replay schema, at which point BrowserOS models become a
translation layer rather than the canonical schema.

**Traces (`motors/browseros/cli/traces/`):**

Packaged runtime BrowserOS traces that ship with code. Currently: `linkedin_easy_apply_v1.json`.

---

## Portals (`portals/`) — deferred

The top-level `portals/` layer is not part of this refactor. It will hold portal knowledge
expressed in Ariadne's motor-agnostic common language once that schema is defined.

When it exists, portal files will describe:

- base URLs and URL construction rules
- search parameter support declarations
- job ID extraction patterns
- application entry-point descriptions
- form field names and flow steps in Ariadne common language

Until then, all portal-specific code lives in `motors/crawl4ai/portals/` as reference
implementations. The top-level `portals/` directory is created as an empty placeholder only.

---

## Data contracts at each boundary

| Boundary | Input | Output |
|---|---|---|
| C4AI scrape engine ← C4AI portal adapter | URL, params, schema | `JobPosting` |
| C4AI apply engine ← C4AI portal adapter | selectors, scripts | `ApplyMeta`, `ApplicationRecord` |
| BrowserOS executor ← trace | `BrowserOSPlaybook` | `ApplyMeta`, `ApplicationRecord` |
| portals ← Ariadne common language | Ariadne step definitions | portal intent descriptions (deferred) |

---

## File disposition

### Moves (no logic change)

| Current | New |
|---|---|
| `src/scraper/smart_adapter.py` | `src/automation/motors/crawl4ai/scrape_engine.py` |
| `src/apply/smart_adapter.py` | `src/automation/motors/crawl4ai/apply_engine.py` |
| `src/scraper/models.py` + `src/apply/models.py` | `src/automation/motors/crawl4ai/models.py` (merged) |
| `src/apply/browseros_models.py` | `src/automation/motors/browseros/cli/models.py` |
| `src/apply/browseros_client.py` | `src/automation/motors/browseros/cli/client.py` |
| `src/apply/browseros_executor.py` | `src/automation/motors/browseros/cli/executor.py` |
| `src/apply/browseros_backend.py` | `src/automation/motors/browseros/cli/backend.py` |
| `src/apply/playbooks/linkedin_easy_apply_v1.json` | `src/automation/motors/browseros/cli/traces/linkedin_easy_apply_v1.json` |
| `data/ariadne/assets/crawl4ai_schemas/*.json` | `src/automation/motors/crawl4ai/schemas/*.json` |

### Portal adapters — moved as-is (no split)

Portal adapters are C4AI-specific reference implementations. They move without modification
into `motors/crawl4ai/portals/`. The split into common-language portal definitions is deferred.

| Current | New |
|---|---|
| `src/scraper/providers/stepstone/adapter.py` | `src/automation/motors/crawl4ai/portals/stepstone/scrape.py` |
| `src/scraper/providers/tuberlin/adapter.py` | `src/automation/motors/crawl4ai/portals/tuberlin/scrape.py` |
| `src/scraper/providers/xing/adapter.py` | `src/automation/motors/crawl4ai/portals/xing/scrape.py` |
| `src/apply/providers/linkedin/adapter.py` | `src/automation/motors/crawl4ai/portals/linkedin/apply.py` |
| `src/apply/providers/stepstone/adapter.py` | `src/automation/motors/crawl4ai/portals/stepstone/apply.py` |
| `src/apply/providers/xing/adapter.py` | `src/automation/motors/crawl4ai/portals/xing/apply.py` |

### New files (no current equivalent)

| File | Purpose |
|---|---|
| `src/automation/main.py` | Unified CLI merging scrape and apply subcommands |
| `src/automation/__init__.py` | Package root |
| All `__init__.py` under new tree | Package wiring |

### Not moved

| Asset | Reason |
|---|---|
| `data/ariadne/reference_data/applying_traces/` (all) | Exploratory reference data, not runtime code |
| `src/scraper/main.py`, `src/apply/main.py` | Superseded by `src/automation/main.py`; deleted after migration |

---

## Test disposition

Tests follow the source split:

| Current | New |
|---|---|
| `tests/unit/scraper/test_smart_adapter.py` | `tests/unit/automation/motors/crawl4ai/test_scrape_engine.py` |
| `tests/unit/apply/test_smart_adapter.py` | `tests/unit/automation/motors/crawl4ai/test_apply_engine.py` |
| `tests/unit/apply/test_models.py` | `tests/unit/automation/motors/crawl4ai/test_models.py` |
| `tests/unit/apply/browseros/test_client.py` | `tests/unit/automation/motors/browseros/cli/test_client.py` |
| `tests/unit/apply/browseros/test_executor.py` | `tests/unit/automation/motors/browseros/cli/test_executor.py` |
| `tests/unit/apply/browseros/test_models.py` | `tests/unit/automation/motors/browseros/cli/test_models.py` |
| `tests/unit/apply/providers/linkedin/test_adapter.py` | `tests/unit/automation/motors/crawl4ai/portals/linkedin/test_apply.py` |
| `tests/unit/apply/providers/stepstone/test_adapter.py` | `tests/unit/automation/motors/crawl4ai/portals/stepstone/test_apply.py` |
| `tests/unit/apply/providers/xing/test_adapter.py` | `tests/unit/automation/motors/crawl4ai/portals/xing/test_apply.py` |

---

## Known deferred items

- **Ariadne common language schema** — must be defined before the top-level `portals/` layer
  can be written. Current portal adapters in `motors/crawl4ai/portals/` are reference
  implementations pending this rewrite.
- **BrowserOS playbook schema → Ariadne** — `motors/browseros/cli/models.py` is the correct
  short-term home; migration to a backend-neutral Ariadne schema is a future step.
- **`motors/browseros/agent/`**, **`motors/os_native_tools/`**, **`motors/vision/`** — fully
  conceptual, no current code. Not part of this refactor.
- **`portals/*/routing.py`** — application routing logic (email vs. inline vs. ATS) does not
  exist yet. Not part of this refactor.
