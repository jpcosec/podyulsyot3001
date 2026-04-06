# `src/automation/` — Unified Automation Package

## 🏗️ Architecture & Features

All runtime automation code lives here: job discovery (scraping) and job application, organized around two concerns that are kept strictly separate.

**Portal intent** (`portals/`) describes *what* a portal offers — field names, flow steps, supported search parameters — in motor-agnostic terms defined by the Ariadne schema. No CSS selectors or script DSLs here.

**Motor translators** (`motors/`) describe *how* to interact with a portal. Each motor owns its own execution mechanics, models, and portal-specific translation layers.

```text
src/automation/
  main.py                            # unified CLI: scrape / apply subcommands
  ariadne/
    portal_models.py                 # ScrapePortalDefinition, ApplyPortalDefinition, ApplyStep, FormField, FieldType
  portals/
    stepstone/{scrape,apply}.py      # STEPSTONE_SCRAPE, STEPSTONE_APPLY
    xing/{scrape,apply}.py           # XING_SCRAPE, XING_APPLY
    tuberlin/scrape.py               # TUBERLIN_SCRAPE
    linkedin/apply.py                # LINKEDIN_APPLY
  motors/
    crawl4ai/
      models.py                      # JobPosting, FormSelectors, ApplicationRecord, ApplyMeta
      scrape_engine.py               # SmartScraperAdapter — base class for all C4AI scrape adapters
      apply_engine.py                # ApplyAdapter — base class for all C4AI apply adapters
      schemas/                       # source-controlled Crawl4AI extraction schemas (JSON)
      portals/
        stepstone/{scrape,apply}.py  # StepStoneAdapter, StepStoneApplyAdapter
        xing/{scrape,apply}.py       # XingAdapter, XingApplyAdapter
        tuberlin/scrape.py           # TUBerlinAdapter
        linkedin/apply.py            # LinkedInApplyAdapter
    browseros/
      cli/
        client.py                    # BrowserOSClient — MCP tool-call client
        executor.py                  # BrowserOSPlaybookExecutor — deterministic playbook runner
        backend.py                   # build_browseros_providers() — apply backend factory
        models.py                    # BrowserOSPlaybook and related MCP schema models
        traces/
          linkedin_easy_apply_v1.json  # packaged BrowserOS runtime trace
```

### Boundary rules

- `portals/` files import only from `src.automation.ariadne.portal_models`. No motor imports.
- `motors/crawl4ai/portals/` files import their portal definition from `src.automation.portals.*` and add C4AI mechanics (CSS selectors, C4A-Script, crawl_result parsing).
- `motors/browseros/` files import `ApplicationRecord` and `ApplyMeta` from `src.automation.motors.crawl4ai.models` (shared apply contracts).

---

## ⚙️ Configuration

```env
PLAYWRIGHT_BROWSERS_PATH=0   # for Crawl4AI browser automation
```

BrowserOS requires a running BrowserOS MCP server. See `motors/browseros/cli/client.py` for the connection setup.

---

## 🚀 CLI / Usage

Unified entry point for all automation:

```bash
# Scrape job postings
python -m src.automation.main scrape --source stepstone --job-query "data engineer" --city berlin

# Apply to a job (C4AI backend)
python -m src.automation.main apply --source xing --job-id 12345 --cv path/to/cv.pdf --dry-run

# Apply via BrowserOS
python -m src.automation.main apply --backend browseros --source linkedin --job-id 99 --cv path/to/cv.pdf --profile-json path/to/profile.json
```

CLI arguments are defined in `build_parser()` in `src/automation/main.py`.

---

## 📝 Data Contract

### Ariadne portal schema

Motor-agnostic portal intent: `src/automation/ariadne/portal_models.py`

- `ScrapePortalDefinition` — source name, base URL, supported search params, job-ID regex
- `ApplyPortalDefinition` — source name, base URL, entry description, apply steps with fields
- `ApplyStep`, `FormField`, `FieldType` — step and field definitions

### C4AI motor contracts

Scrape and apply data models: `src/automation/motors/crawl4ai/models.py`

- `JobPosting` — structured extraction output from a scrape run
- `FormSelectors` — CSS selectors validated against the live DOM before interaction
- `ApplicationRecord` — persisted record of one apply attempt
- `ApplyMeta` — status artifact from one apply run (`submitted` / `dry_run` / `failed` / `portal_changed`)

### BrowserOS motor contracts

MCP tool-call schema: `src/automation/motors/browseros/cli/models.py`

- `BrowserOSPlaybook`, `PlaybookStep`, `PlaybookAction` — deterministic BrowserOS replay schema

---

## 🛠️ How to Add a New Portal

### Scrape portal

1. Add `src/automation/portals/<portal>/scrape.py` exporting a `ScrapePortalDefinition` instance.
2. Add `src/automation/motors/crawl4ai/portals/<portal>/scrape.py` extending `SmartScraperAdapter`. Import the definition from step 1. Implement `get_search_url`, `extract_links`, `get_llm_instructions`.
3. Register the adapter in `_run_scrape()` in `src/automation/main.py`.
4. Add `src/automation/motors/crawl4ai/schemas/<portal>_schema.json` if the portal uses deterministic extraction.
5. Add tests: `tests/unit/automation/portals/` and `tests/unit/automation/motors/crawl4ai/portals/<portal>/`.

### Apply portal (C4AI)

1. Add `src/automation/portals/<portal>/apply.py` exporting an `ApplyPortalDefinition` instance.
2. Add `src/automation/motors/crawl4ai/portals/<portal>/apply.py` extending `ApplyAdapter`. Import the definition from step 1. Implement `get_form_selectors`, `get_open_modal_script`, `get_fill_form_script`, `get_submit_script`, `get_success_text`, `get_session_profile_dir`.
3. Register the adapter in `_run_apply()` in `src/automation/main.py`.
4. Add tests mirroring `tests/unit/automation/motors/crawl4ai/portals/linkedin/`.

---

## 💻 How to Use

```python
from src.automation.motors.crawl4ai.portals.stepstone.scrape import StepStoneAdapter
from src.core.data_manager import DataManager

adapter = StepStoneAdapter(DataManager())
# adapter.run() is async — use asyncio.run() or await inside an async context
```

---

## 🚑 Troubleshooting

**All XING scrape runs produce zero ingested jobs**
→ `extract_links` must return dicts with a `"url"` key. The scrape engine normalizer silently skips entries without it.

**`PortalStructureChangedError` raised during apply**
→ A mandatory CSS selector was not found in the live DOM. The portal changed its UI. Update `get_form_selectors()` in the relevant apply translator.

**`RuntimeError: already submitted` on retry**
→ `ApplyMeta.status == "submitted"` blocks re-execution. Use `--dry-run` to test without writing a submitted record, or manually clear the `apply_meta.json` artifact.
