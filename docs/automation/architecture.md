# Automation Architecture

## Design rationale

The old `src/scraper/` and `src/apply/` packages mixed two concerns that don't belong together: portal knowledge (what fields a form has, what a job URL looks like) and execution mechanics (CSS selectors, C4A-Script DSL, MCP tool calls). This made it impossible to add a second execution backend for an existing portal without duplicating the portal knowledge.

The refactor introduced an explicit boundary: the **Ariadne portal schema**.

---

## The Ariadne boundary

`src/automation/ariadne/portal_models.py` defines the motor-agnostic portal intent schema. A `ScrapePortalDefinition` or `ApplyPortalDefinition` instance describes *what* a portal offers — field names, flow steps, supported search parameters — without any motor-specific detail.

```
portals/xing/apply.py
  └── XING_APPLY: ApplyPortalDefinition
        source_name: "xing"
        base_url: "https://www.xing.com"
        steps:
          - fill_contact  [first_name, last_name, email, phone]
          - upload_cv     [cv: FILE_PDF, required]
          - submit        [dry_run_stop=True]
```

Portal files import only from `ariadne/portal_models.py`. **No motor imports are allowed in `portals/`.**

---

## Motor separation

Each execution backend is a self-contained motor under `src/automation/motors/`. A motor owns:

- its own base engine / client
- its own data models
- its own portal translators (which consume portal intent and add motor mechanics)

### Crawl4AI motor (`motors/crawl4ai/`)

Owns everything that depends on the Crawl4AI library: `AsyncWebCrawler`, `BrowserConfig`, `CrawlerRunConfig`, C4A-Script DSL, CSS selectors, and extraction schema files.

Portal translators in `motors/crawl4ai/portals/` import the portal intent from `portals/` and add the C4AI-specific layer: CSS selectors, C4A-Script blocks, URL builders, BeautifulSoup link parsing.

Shared contracts live in `motors/crawl4ai/models.py` (`JobPosting`, `FormSelectors`, `ApplicationRecord`, `ApplyMeta`). These are C4AI motor artifacts consumed by both the scrape and apply sides of the motor, and shared with the BrowserOS motor's `ApplicationRecord`/`ApplyMeta` output.

### BrowserOS CLI motor (`motors/browseros/cli/`)

Owns everything that depends on the BrowserOS MCP interface: the MCP client, deterministic playbook executor, BrowserOS tool-call schema, and packaged runtime traces.

The BrowserOS motor currently uses pre-recorded playbook traces (`traces/linkedin_easy_apply_v1.json`) rather than consulting portal intent at runtime. Bridging `ApplyPortalDefinition` to BrowserOS tool-call sequences is a deferred Phase 2 item.

---

## Data flow — scrape pipeline

```
CLI: python -m src.automation.main scrape --source stepstone

  main.py:_run_scrape()
      │
      ├── StepStoneAdapter(DataManager)
      │     portal = STEPSTONE_SCRAPE          ← portal intent
      │     get_search_url(**kwargs)            ← C4AI-specific URL builder
      │     extract_links(crawl_result)         ← C4AI-specific link extractor
      │     get_llm_instructions()              ← C4AI extraction hint
      │
      └── SmartScraperAdapter.run()             ← scrape_engine.py
              │
              ├── AsyncWebCrawler: fetch listing page
              ├── extract_links() → discovery entries [{url, listing_data, ...}]
              ├── AsyncWebCrawler: fetch each detail page
              ├── LLM extraction → raw JSON
              ├── JobPosting.model_validate()   ← C4AI model, fails closed
              └── DataManager.write()
                    data/jobs/stepstone/<job_id>/nodes/ingest/proposed/
                      state.json
                      content.md
                      raw_page.html
                      listing.json
                      ...
```

`source_name`, `supported_params`, and `extract_job_id` are all derived from the `STEPSTONE_SCRAPE` definition at the Ariadne layer. The C4AI translator only adds execution mechanics.

---

## Data flow — apply pipeline (C4AI backend)

```
CLI: python -m src.automation.main apply --source xing --job-id 12345 --cv cv.pdf

  main.py:_run_apply()
      │
      ├── XingApplyAdapter(DataManager)
      │     portal = XING_APPLY               ← portal intent
      │     source_name  ← portal.source_name
      │     get_form_selectors()               ← CSS selectors (C4AI-specific)
      │     get_open_modal_script()            ← C4A-Script (C4AI-specific)
      │     get_fill_form_script(profile)      ← C4A-Script with {{placeholders}}
      │     get_submit_script()                ← C4A-Script (C4AI-specific)
      │
      └── ApplyAdapter.run()                   ← apply_engine.py
              │
              ├── _check_idempotency()         ← blocks re-apply if already submitted
              ├── AsyncWebCrawler: navigate to job page
              ├── _check_selector_results()    ← validates mandatory selectors in live DOM
              ├── C4A-Script: open modal
              ├── C4A-Script: fill form (profile placeholders resolved)
              ├── C4A-Script: upload CV
              ├── dry_run check (stop before submit if --dry-run)
              ├── C4A-Script: submit
              └── DataManager.write()
                    data/jobs/xing/12345/nodes/apply/
                      apply_meta.json     ← ApplyMeta: status, timestamp, error
                      application_record.json  ← ApplicationRecord: full attempt record
```

---

## Data flow — apply pipeline (BrowserOS backend)

```
CLI: python -m src.automation.main apply --backend browseros --source linkedin --job-id 99 --cv cv.pdf

  main.py:_run_apply()
      │
      └── build_browseros_providers(DataManager)   ← backend.py
              │
              ├── BrowserOSPlaybookExecutor
              │     playbook = traces/linkedin_easy_apply_v1.json
              │
              └── BrowserOSPlaybookExecutor.execute()  ← executor.py
                      │
                      ├── BrowserOSClient: MCP tool calls (navigate, click, fill, upload_file)
                      └── DataManager.write()
                            apply_meta.json
                            application_record.json
```

The BrowserOS path does not yet consume `LINKEDIN_APPLY` portal intent. It replays a pre-recorded trace directly. Connecting `ApplyPortalDefinition` to BrowserOS execution is a Phase 2 item.

---

## Boundary summary

| Layer | Owns | Must not import |
|---|---|---|
| `portals/` | Portal intent (what) | Anything from `motors/` |
| `motors/crawl4ai/portals/` | C4AI mechanics (how) | Nothing from `src.scraper` or `src.apply` |
| `motors/browseros/cli/` | BrowserOS MCP execution | Nothing from `src.apply` |
| `motors/crawl4ai/models.py` | Shared apply/scrape contracts | Nothing from `motors/browseros/` |

---

## Deferred (Phase 2)

- **Ariadne storage, recorder, replayer, promotion** — only `portal_models.py` is implemented. The full Ariadne layer (storage, normalized traces, backend-neutral replay) is tracked in `plan_docs/ariadne/` and `plan_docs/automation/2026-04-04-ariadne-common-language-issues.md`.
- **BrowserOS playbook → Ariadne** — `motors/browseros/cli/models.py` is the correct short-term home. Future: `ApplyPortalDefinition` drives BrowserOS tool-call generation instead of pre-recorded traces.
- **`portals/*/routing.py`** — application routing (email vs. inline vs. ATS) does not exist yet.
- **BrowserOS agent motor, OS-native tools motor, vision motor** — conceptual only, no code.
