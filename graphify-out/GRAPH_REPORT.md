# Graph Report - .  (2026-04-06)

## Corpus Check
- 130 files · ~86,279 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 547 nodes · 1265 edges · 15 communities detected
- Extraction: 43% EXTRACTED · 57% INFERRED · 0% AMBIGUOUS · INFERRED: 716 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `DataManager` - 111 edges
2. `LogTag` - 93 edges
3. `FormSelectors` - 59 edges
4. `ApplyAdapter` - 56 edges
5. `SmartScraperAdapter` - 52 edges
6. `BrowserOSClient` - 44 edges
7. `ApplicationRecord` - 33 edges
8. `ApplyMeta` - 33 edges
9. `PortalStructureChangedError` - 27 edges
10. `JobPosting` - 26 edges

## Surprising Connections (you probably didn't know these)
- `FormSelectors has all four mandatory fields populated.` --uses--> `XingApplyAdapter`  [INFERRED]
  tests/unit/automation/motors/crawl4ai/portals/xing/test_apply.py → src/automation/motors/crawl4ai/portals/xing/apply.py
- `Mandatory selectors match elements in the real XING apply modal HTML.` --uses--> `XingApplyAdapter`  [INFERRED]
  tests/unit/automation/motors/crawl4ai/portals/xing/test_apply.py → src/automation/motors/crawl4ai/portals/xing/apply.py
- `Optional selectors that are set should also be findable in the fixture.` --uses--> `XingApplyAdapter`  [INFERRED]
  tests/unit/automation/motors/crawl4ai/portals/xing/test_apply.py → src/automation/motors/crawl4ai/portals/xing/apply.py
- `get_open_modal_script() contains an idempotency guard (IF NOT check).` --uses--> `XingApplyAdapter`  [INFERRED]
  tests/unit/automation/motors/crawl4ai/portals/xing/test_apply.py → src/automation/motors/crawl4ai/portals/xing/apply.py
- `get_fill_form_script() uses {{placeholder}} syntax, not f-string values.` --uses--> `XingApplyAdapter`  [INFERRED]
  tests/unit/automation/motors/crawl4ai/portals/xing/test_apply.py → src/automation/motors/crawl4ai/portals/xing/apply.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (40): LinkedInApplyAdapter, C4AI apply adapter for LinkedIn Easy Apply., Return the browser session profile directory for LinkedIn authentication persist, Return CSS selectors for the LinkedIn Easy Apply form. Includes cv_select_existi, Return a C4A-Script snippet that opens the LinkedIn Easy Apply modal if not alre, Return a C4A-Script snippet that fills contact fields using {{template}} placeho, Return a C4A-Script snippet that clicks submit and waits for the success indicat, Return the German keyword that confirms a successful XING application. (+32 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (65): Shared base class for auto-application adapters.  Adapters provide portal-specif, Raise PortalStructureChangedError if any mandatory selector is absent., Block re-execution only when prior status is 'submitted'.          dry_run / fai, Persistent session browser config., Query the live DOM for all non-None selectors and validate.          Uses a befo, Return a before_retrieve_html hook that uploads files via raw Playwright., Check result content for expected success text fragment.          Returns True i, Open a visible browser for manual login. Cookies persist to profile dir. (+57 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (30): ApplyAdapter, get_fill_form_script(), get_form_selectors(), get_open_modal_script(), _get_portal_base_url(), get_session_profile_dir(), get_submit_script(), get_success_text() (+22 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (37): BrowserOSApplyProvider, build_browseros_providers(), BrowserOS-backed apply providers wired into the common apply CLI., Build BrowserOS-backed apply providers.      Args:         data_manager: Optiona, Open a visible BrowserOS page and wait for manual login.          Returns:, Run a BrowserOS-backed application flow for one job.          Args:, BaseModel, One interactive element parsed from BrowserOS snapshot text output. (+29 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (27): BrowserOSClient, BrowserOSError, BrowserOS MCP client used by the BrowserOS apply backend., Close a BrowserOS page.          Args:             page_id: Page identifier to c, Bring a BrowserOS page to the foreground.          Args:             page_id: Pa, Navigate a page to the provided URL.          Args:             url: Destination, Capture and parse the current interactive BrowserOS snapshot.          Args:, Click an element identified from a BrowserOS snapshot.          Args: (+19 more)

### Community 5 - "Community 5"
Cohesion: 0.1
Nodes (13): ABC, detect_language(), extract_job_id(), extract_links(), get_llm_instructions(), get_search_url(), normalize_relative_date(), _now_utc() (+5 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (24): LinkedIn apply portal definition in Ariadne common language., Enum, Standardized log tag enum for consistent observability across all pipeline modul, ApplyPortalDefinition, ApplyStep, FieldType, FormField, Ariadne portal schema — motor-agnostic portal intent models.  These models expre (+16 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (17): Return the canonical path for one artifact file., Check whether a canonical artifact already exists., Resolve a safe relative path under the job root.          Args:             sour, Ensure a job root and metadata file exist.          Args:             source: So, Return lifecycle metadata for a job, creating it if needed., Update and persist the lifecycle status for a job., Write a canonical JSON artifact under a job node stage., Read a canonical JSON artifact from a job node stage. (+9 more)

### Community 8 - "Community 8"
Cohesion: 0.1
Nodes (12): _render_script() correctly substitutes placeholders with profile values., FormSelectors has all four mandatory fields populated., Mandatory selectors match elements in the real XING apply modal HTML., Optional selectors that are set should also be findable in the fixture., get_open_modal_script() contains an idempotency guard (IF NOT check)., get_fill_form_script() uses {{placeholder}} syntax, not f-string values., test_fill_form_script_uses_placeholders(), test_get_form_selectors_returns_all_mandatory() (+4 more)

### Community 9 - "Community 9"
Cohesion: 0.22
Nodes (8): _FakeClient, _snapshot(), test_assert_expected_elements_raises_on_missing_snapshot_text(), test_conditional_human_required_prompts_operator(), test_execute_action_uses_fallback_when_primary_selector_missing(), test_render_template_resolves_nested_context_values(), test_resolve_element_id_supports_partial_matches(), test_run_skips_unresolved_prefill_actions_and_stops_at_dry_run()

### Community 10 - "Community 10"
Cohesion: 0.14
Nodes (13): DataManagerError, JobMetadata, Central schema-v0 data manager for job artifacts and lifecycle metadata.  The da, Base exception for schema-v0 data-plane errors., Lifecycle metadata stored in ``meta.json`` for each job., Exception, Shared utilities used across all pipeline modules., ErrorContext (+5 more)

### Community 11 - "Community 11"
Cohesion: 0.23
Nodes (5): _DummyAdapter, Tests for scraper artifact preservation behavior., _result(), test_process_results_fails_closed_but_persists_failed_artifacts(), test_process_results_persists_listing_and_raw_artifacts()

### Community 12 - "Community 12"
Cohesion: 0.22
Nodes (1): Tests for the unified automation CLI parser.

### Community 13 - "Community 13"
Cohesion: 0.22
Nodes (1): Tests for BrowserOS playbook models.

### Community 14 - "Community 14"
Cohesion: 0.25
Nodes (2): extract_links must return dicts with 'url' key so the scrape engine can normaliz, test_extract_links_returns_url_key()

## Knowledge Gaps
- **56 isolated node(s):** `Central schema-v0 data manager for job artifacts and lifecycle metadata.  The da`, `Base exception for schema-v0 data-plane errors.`, `Lifecycle metadata stored in ``meta.json`` for each job.`, `Manage schema-v0 job metadata and primitive artifact IO under ``data/jobs``.`, `Return the canonical filesystem root for one job.          Args:             sou` (+51 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DataManager` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 5`, `Community 7`, `Community 10`, `Community 11`?**
  _High betweenness centrality (0.348) - this node is a cross-community bridge._
- **Why does `LogTag` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.269) - this node is a cross-community bridge._
- **Why does `SmartScraperAdapter` connect `Community 5` to `Community 0`, `Community 1`, `Community 11`?**
  _High betweenness centrality (0.175) - this node is a cross-community bridge._
- **Are the 79 inferred relationships involving `DataManager` (e.g. with `Shared utilities used across all pipeline modules.` and `Unified automation CLI.  Subcommands:   scrape  — job discovery and ingestion`) actually correct?**
  _`DataManager` has 79 INFERRED edges - model-reasoned connections that need verification._
- **Are the 90 inferred relationships involving `LogTag` (e.g. with `Unified automation CLI.  Subcommands:   scrape  — job discovery and ingestion` and `Build and return the root ArgumentParser with scrape and apply subcommands regis`) actually correct?**
  _`LogTag` has 90 INFERRED edges - model-reasoned connections that need verification._
- **Are the 56 inferred relationships involving `FormSelectors` (e.g. with `PortalStructureChangedError` and `ApplyAdapter`) actually correct?**
  _`FormSelectors` has 56 INFERRED edges - model-reasoned connections that need verification._
- **Are the 37 inferred relationships involving `ApplyAdapter` (e.g. with `ApplicationRecord` and `ApplyMeta`) actually correct?**
  _`ApplyAdapter` has 37 INFERRED edges - model-reasoned connections that need verification._