# Unified Automation Refactor — Design Spec

Date: 2026-04-06

## Goal

Move all runtime automation code under `src/automation/` with clear motor ownership and
explicit data contracts at each boundary. Portal knowledge is separated from motor-specific
translation. The Ariadne common language is established as the boundary between portals and
motors, but its full schema definition is deferred to a subsequent step.

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
      portals/                     # C4AI translation layer (CSS selectors, C4A-Script)
        stepstone.py               # ← C4AI mechanics from scraper + apply stepstone adapters
        tuberlin.py                # ← C4AI mechanics from scraper tuberlin adapter
        xing.py                    # ← C4AI mechanics from scraper + apply xing adapters
        linkedin.py                # ← C4AI mechanics from apply linkedin adapter
    browseros/
      cli/
        client.py                  # ← src/apply/browseros_client.py
        executor.py                # ← src/apply/browseros_executor.py
        backend.py                 # ← src/apply/browseros_backend.py
        models.py                  # ← src/apply/browseros_models.py
        traces/
          linkedin_easy_apply_v1.json  # ← src/apply/playbooks/linkedin_easy_apply_v1.json
  portals/                         # common language — portal knowledge only, no motor code
    stepstone/
      scrape.py                    # ← portal slice from src/scraper/providers/stepstone/adapter.py
      apply.py                     # ← portal slice from src/apply/providers/stepstone/adapter.py
    tuberlin/
      scrape.py                    # ← portal slice from src/scraper/providers/tuberlin/adapter.py
    xing/
      scrape.py                    # ← portal slice from src/scraper/providers/xing/adapter.py
      apply.py                     # ← portal slice from src/apply/providers/xing/adapter.py
    linkedin/
      apply.py                     # ← portal slice from src/apply/providers/linkedin/adapter.py
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

**Portal translation layer (`motors/crawl4ai/portals/`):**

One file per portal containing the C4AI-specific translation of portal intent into Crawl4AI
mechanics: CSS selectors, C4A-Script blocks, `crawl_result` parsing logic. These files
consume definitions from `portals/` and produce C4AI-executable operations.

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

## Portals (`portals/`)

Portal files contain only portal knowledge expressed in terms that are motor-agnostic:

- base URLs and URL construction rules
- search parameter support declarations
- job ID extraction patterns
- application entry-point descriptions
- form field names in human terms (e.g. "first name", "CV upload")
- flow step descriptions in Ariadne common language

**What portals must not contain:** CSS selectors, C4A-Script DSL, BrowserOS `tool:` calls,
`crawl_result` API references, or any import from a motor package.

### Ariadne common language — prerequisite

The portal files cannot be written cleanly until the Ariadne common language schema is defined.
This schema specifies how a scrape intent, apply step, and form field are expressed in
motor-agnostic terms. Defining it is the first task in implementation and gates the portal split.

Until the common language exists, portal files will hold structured metadata only (URLs, ID
patterns, supported params) and the C4AI adapter classes will continue to hold selectors and
scripts — co-located in `motors/crawl4ai/portals/` rather than split.

---

## Data contracts at each boundary

| Boundary | Input | Output |
|---|---|---|
| C4AI scrape engine ← portal | portal scrape definition (URL, params) | `JobPosting` |
| C4AI apply engine ← portal | portal apply definition (selectors, scripts) | `ApplyMeta`, `ApplicationRecord` |
| BrowserOS executor ← trace | `BrowserOSPlaybook` | `ApplyMeta`, `ApplicationRecord` |
| portals ← Ariadne common language | Ariadne step definitions | portal intent descriptions |

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

### Splits (logic separated by responsibility)

Each current portal adapter splits into two files:

| Current | Portal slice → `portals/` | C4AI slice → `motors/crawl4ai/portals/` |
|---|---|---|
| `src/scraper/providers/stepstone/adapter.py` | `portals/stepstone/scrape.py` | `motors/crawl4ai/portals/stepstone.py` |
| `src/scraper/providers/tuberlin/adapter.py` | `portals/tuberlin/scrape.py` | `motors/crawl4ai/portals/tuberlin.py` |
| `src/scraper/providers/xing/adapter.py` | `portals/xing/scrape.py` | `motors/crawl4ai/portals/xing.py` |
| `src/apply/providers/linkedin/adapter.py` | `portals/linkedin/apply.py` | `motors/crawl4ai/portals/linkedin.py` |
| `src/apply/providers/stepstone/adapter.py` | `portals/stepstone/apply.py` | merged into `motors/crawl4ai/portals/stepstone.py` |
| `src/apply/providers/xing/adapter.py` | `portals/xing/apply.py` | merged into `motors/crawl4ai/portals/xing.py` |

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
| `tests/unit/apply/providers/linkedin/test_adapter.py` | split: `tests/unit/automation/portals/linkedin/` + `tests/unit/automation/motors/crawl4ai/portals/` |
| `tests/unit/apply/providers/stepstone/test_adapter.py` | split: `tests/unit/automation/portals/stepstone/` + `tests/unit/automation/motors/crawl4ai/portals/` |
| `tests/unit/apply/providers/xing/test_adapter.py` | split: `tests/unit/automation/portals/xing/` + `tests/unit/automation/motors/crawl4ai/portals/` |

---

## Known deferred items

- **Ariadne common language schema** — must be defined before portal files can be fully
  written. Gates the portal split.
- **BrowserOS playbook schema → Ariadne** — `motors/browseros/cli/models.py` is the correct
  short-term home; migration to a backend-neutral Ariadne schema is a future step.
- **`motors/browseros/agent/`**, **`motors/os_native_tools/`**, **`motors/vision/`** — fully
  conceptual, no current code. Not part of this refactor.
- **`portals/*/routing.py`** — application routing logic (email vs. inline vs. ATS) does not
  exist yet. Not part of this refactor.
