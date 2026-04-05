# Unified Automation Refactor — Design Spec

Date: 2026-04-06

## Goal

Move all runtime automation code under `src/automation/` with clear motor ownership and
explicit data contracts at each boundary. The Ariadne portal schema is defined first as the
boundary between portal knowledge and motor execution. Portal intent files are written against
that schema. C4AI portal adapters are rewritten to consume portal intent and add C4AI-specific
translation on top. Only then does the structural move happen.

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
  ariadne/
    __init__.py
    portal_models.py               # NEW: ScrapePortalDefinition, ApplyPortalDefinition,
                                   #       ApplyStep, FormField, FieldType
  portals/                         # NEW: portal intent in Ariadne common language
    stepstone/
      __init__.py
      scrape.py                    # STEPSTONE_SCRAPE: ScrapePortalDefinition
      apply.py                     # STEPSTONE_APPLY: ApplyPortalDefinition
    tuberlin/
      __init__.py
      scrape.py                    # TUBERLIN_SCRAPE: ScrapePortalDefinition
    xing/
      __init__.py
      scrape.py                    # XING_SCRAPE: ScrapePortalDefinition
      apply.py                     # XING_APPLY: ApplyPortalDefinition
    linkedin/
      __init__.py
      apply.py                     # LINKEDIN_APPLY: ApplyPortalDefinition
  motors/
    crawl4ai/
      scrape_engine.py             # ← src/scraper/smart_adapter.py
      apply_engine.py              # ← src/apply/smart_adapter.py
      models.py                    # ← src/scraper/models.py + src/apply/models.py
      schemas/                     # ← data/ariadne/assets/crawl4ai_schemas/*.json
        stepstone_schema.json
        tuberlin_schema.json
        xing_schema.json
      portals/                     # C4AI translators — consume portals/, add CSS/scripts
        stepstone/
          scrape.py                # ← rewritten from src/scraper/providers/stepstone/adapter.py
          apply.py                 # ← rewritten from src/apply/providers/stepstone/adapter.py
        tuberlin/
          scrape.py                # ← rewritten from src/scraper/providers/tuberlin/adapter.py
        xing/
          scrape.py                # ← rewritten from src/scraper/providers/xing/adapter.py
          apply.py                 # ← rewritten from src/apply/providers/xing/adapter.py
        linkedin/
          apply.py                 # ← rewritten from src/apply/providers/linkedin/adapter.py
    browseros/
      cli/
        client.py                  # ← src/apply/browseros_client.py
        executor.py                # ← src/apply/browseros_executor.py
        backend.py                 # ← src/apply/browseros_backend.py
        models.py                  # ← src/apply/browseros_models.py
        traces/
          linkedin_easy_apply_v1.json  # ← src/apply/playbooks/linkedin_easy_apply_v1.json
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

**Portal translators (`motors/crawl4ai/portals/`):**

One file per portal per operation. Each file imports the portal intent from `portals/` and
adds the C4AI-specific translation: CSS selectors, C4A-Script blocks, URL builders, and
`crawl_result` parsing logic. The portal intent (what fields exist, what steps the flow has)
is read from `portals/`; the motor decides how to interact with those fields via the DOM.

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

## Ariadne portal schema (`ariadne/portal_models.py`)

The minimal Ariadne schema for this refactor. Only portal-level models are defined here;
storage, recording, replay, and promotion are deferred.

```python
class FieldType(str, Enum):
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    FILE_PDF = "file_pdf"

class FormField(BaseModel):
    name: str           # semantic name: "first_name", "cv", "letter"
    label: str          # human-readable label
    required: bool
    field_type: FieldType

class ApplyStep(BaseModel):
    name: str           # "open_modal", "fill_contact", "upload_cv", "submit"
    description: str
    fields: list[FormField]
    dry_run_stop: bool = False

class ApplyPortalDefinition(BaseModel):
    source_name: str
    base_url: str
    entry_description: str
    steps: list[ApplyStep]

class ScrapePortalDefinition(BaseModel):
    source_name: str
    base_url: str
    supported_params: list[str]   # ["job_query", "city", "max_days"]
    job_id_pattern: str           # regex applied to a job detail URL
```

URL construction and link extraction are portal-specific logic that cannot be cleanly
expressed as pure data — these remain as methods in the C4AI portal translators.

## Portals (`portals/`)

One file per portal per operation. Each file exports a single instance of
`ScrapePortalDefinition` or `ApplyPortalDefinition`. No motor imports allowed.

Portal files describe **what** — field names, flow steps, entry points — in terms any motor
can consume. The motors describe **how** to interact with those fields.

---

## Data contracts at each boundary

| Boundary | Input | Output |
|---|---|---|
| `portals/` → C4AI translator | `ScrapePortalDefinition` / `ApplyPortalDefinition` | CSS selectors, scripts, URL |
| C4AI scrape engine ← C4AI portal translator | URL, params, schema | `JobPosting` |
| C4AI apply engine ← C4AI portal translator | selectors, scripts | `ApplyMeta`, `ApplicationRecord` |
| BrowserOS executor ← trace | `BrowserOSPlaybook` | `ApplyMeta`, `ApplicationRecord` |
| `portals/` → BrowserOS (future) | `ApplyPortalDefinition` | BrowserOS tool-call sequence |

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

### New files — Ariadne schema and portal intent

| File | Content |
|---|---|
| `src/automation/ariadne/portal_models.py` | `FieldType`, `FormField`, `ApplyStep`, `ApplyPortalDefinition`, `ScrapePortalDefinition` |
| `src/automation/portals/stepstone/scrape.py` | `STEPSTONE_SCRAPE: ScrapePortalDefinition` |
| `src/automation/portals/stepstone/apply.py` | `STEPSTONE_APPLY: ApplyPortalDefinition` |
| `src/automation/portals/tuberlin/scrape.py` | `TUBERLIN_SCRAPE: ScrapePortalDefinition` |
| `src/automation/portals/xing/scrape.py` | `XING_SCRAPE: ScrapePortalDefinition` |
| `src/automation/portals/xing/apply.py` | `XING_APPLY: ApplyPortalDefinition` |
| `src/automation/portals/linkedin/apply.py` | `LINKEDIN_APPLY: ApplyPortalDefinition` |

### Portal adapters — rewritten to consume portal intent

| Current | New | Change |
|---|---|---|
| `src/scraper/providers/stepstone/adapter.py` | `src/automation/motors/crawl4ai/portals/stepstone/scrape.py` | imports `STEPSTONE_SCRAPE`; URL builder and link extraction remain as methods |
| `src/scraper/providers/tuberlin/adapter.py` | `src/automation/motors/crawl4ai/portals/tuberlin/scrape.py` | imports `TUBERLIN_SCRAPE` |
| `src/scraper/providers/xing/adapter.py` | `src/automation/motors/crawl4ai/portals/xing/scrape.py` | imports `XING_SCRAPE` |
| `src/apply/providers/linkedin/adapter.py` | `src/automation/motors/crawl4ai/portals/linkedin/apply.py` | imports `LINKEDIN_APPLY`; CSS selectors and scripts remain as C4AI translation |
| `src/apply/providers/stepstone/adapter.py` | `src/automation/motors/crawl4ai/portals/stepstone/apply.py` | imports `STEPSTONE_APPLY` |
| `src/apply/providers/xing/adapter.py` | `src/automation/motors/crawl4ai/portals/xing/apply.py` | imports `XING_APPLY` |

### Other new files

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
| (new) | `tests/unit/automation/ariadne/test_portal_models.py` |
| (new) | `tests/unit/automation/portals/test_stepstone.py` |
| (new) | `tests/unit/automation/portals/test_xing.py` |
| (new) | `tests/unit/automation/portals/test_tuberlin.py` |
| (new) | `tests/unit/automation/portals/test_linkedin.py` |

---

## Known deferred items

- **Ariadne beyond portal models** — storage, recorder, replayer, and promotion are deferred.
  Only `portal_models.py` is in scope for this refactor.
- **BrowserOS playbook schema → Ariadne** — `motors/browseros/cli/models.py` is the correct
  short-term home; migration to a backend-neutral Ariadne schema is a future step.
- **`motors/browseros/agent/`**, **`motors/os_native_tools/`**, **`motors/vision/`** — fully
  conceptual, no current code. Not part of this refactor.
- **`portals/*/routing.py`** — application routing logic (email vs. inline vs. ATS) does not
  exist yet. Not part of this refactor.
