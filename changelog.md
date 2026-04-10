# Changelog

All notable changes to this project will be documented in this file.

## [2026-04-10] - Unified Agent Entrypoint

### Changed
- Replaced the separate agent guidance variants in `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` with one consolidated canonical document in `AGENTS.md` that combines the strongest repo-specific instructions from each.
- Standardized compatibility behavior so `CLAUDE.md` and `GEMINI.md` are intended to exist only as symlinks back to `AGENTS.md`.
- Refined `AGENTS.md` so it now leads with repository orientation, requires BrowserOS launch before BrowserOS-backed work, points code and documentation edits to `docs/standards/`, formalizes the issue-guide execution order, and records the git-cleanliness rule for agent work.
- Fixed the `AGENTS.md` shared-routing reference to `src/automation/portals/routing.py` after doc-link validation exposed the old broken path.
- Repaired active markdown references across `docs/`, `src/`, and `plan_docs/issues/`, converted local `/tmp` proof paths in BrowserOS reference docs into plain text, and narrowed `scripts/validate_doc_links.py` to active documentation instead of historical/spec/archive markdown.
- Added explicit documentation-lifecycle rules to `AGENTS.md` covering `docs/superpowers/`, `plan_docs/archive/`, `future_docs/`, `session-ses_*.md`, and deletion of completed planning artifacts after implementation knowledge is absorbed.
- Added issue-guide-compliant cleanup issues for rehoming `docs/superpowers/`, ingesting and pruning `plan_docs/archive/`, triaging `session-ses_*.md`, and deleting completed `plan_docs/` artifacts once their knowledge is fully absorbed.
- Clarified `AGENTS.md` git hygiene so agents should create the required snapshot commit automatically instead of asking the user whether to do it.
- Resolved the session-trace triage cleanup issue by deleting `session-ses_28e6.md` after confirming it did not contain unique durable knowledge that was missing from canonical docs or active issues.
- Resolved the `docs/superpowers/` rehoming cleanup issue by moving any remaining durable guidance into canonical docs or transitional planning space, deleting superseded superpowers specs/plans, and repointing `AGENTS.md` to current architecture docs.
- Resolved the archive-ingestion cleanup issue by absorbing the remaining placement rules into `src/automation/README.md` and `plan_docs/ariadne/storage.md`, then deleting the obsolete `plan_docs/archive/automation/` files.
- Pruned stale completed planning overviews in `plan_docs/planning/stage1_baseline.md`, `plan_docs/automation/README.md`, `plan_docs/ariadne/README.md`, and `plan_docs/contracts/README.md` after confirming their guidance is already covered by current docs and code-adjacent READMEs.
- Pruned additional completed planning docs in `plan_docs/motors/browseros.md`, `plan_docs/motors/crawl4ai.md`, and `plan_docs/automation/2026-04-04-ariadne-common-language-issues.md` after confirming their guidance had been absorbed into current architecture docs, standards, and Ariadne models.

## [2026-04-10] - BrowserOS Auto-Launch and Health Management

### Added
- Added `ensure_browseros_running` and `is_runtime_ready` to `src/automation/motors/browseros/runtime.py` to proactively check BrowserOS health and auto-launch the AppImage if unreachable.
- Added `--launch` flag to `python -m src.automation.main browseros-check` to attempt auto-launching from the CLI.
- Added 9 unit tests for BrowserOS runtime health and launch logic in `tests/unit/automation/motors/browseros/test_runtime.py`.

### Changed
- Updated `BrowserOSClient.initialize` in `src/automation/motors/browseros/cli/client.py` to call `ensure_browseros_running` before initiating MCP sessions.
- Updated `OpenBrowserClient.communicate` in `src/automation/motors/browseros/agent/openbrowser.py` to call `ensure_browseros_running` before starting Level 2 /chat sessions.
- Updated existing `BrowserOSClient` and `OpenBrowserClient` unit tests to mock `ensure_browseros_running`, reducing test execution time from ~40s to <0.1s.

## [2026-04-09] - Portal Real-Life Validation Plan

### Added
- Added `_normalize_payload()` method to `SmartScraperAdapter` in `src/automation/motors/crawl4ai/scrape_engine.py` to handle four common extraction failure modes from real portal CSS schemas: (1) `{ "data": {...} }` dict wrappers, (2) `{ "data": [...] }` list wrappers, (3) `[{ "item": "..." }]` list-item shapes, and (4) missing mandatory scalars backfilled from listing_case teaser fields. Also mines German heading sections (`Das erwartet Dich`, `Das bringst Du mit`, etc.) from markdown to populate `responsibilities` and `requirements`.
- Added 8 regression tests for `_normalize_payload` and `_extract_payload` normalization integration covering wrapped payloads, item-shape flattening, listing_case backfill, and markdown bullet mining.
- Added `plan_docs/issues/gaps/portal-real-life-validation.md` in the issue-guide format to define the live-validation gap for real scrape, routing, and safe onsite apply dry-runs across the currently supported portals.
- Added `plan_docs/issues/Index.md` as the issue-guide-compliant issues entrypoint and dependency index for the current portal validation work.
- Added child issue files for scrape validation, routing validation, onsite apply dry-run validation, and live-validation triage under `plan_docs/issues/gaps/`.

### Changed
- Added `docs/automation/browseros_chat_runtime_support.md` to state the current runtime support level for BrowserOS `/chat`: historical live evidence exists, but the current session probe returned `503`, so `/chat` is now explicitly documented as a best-effort surface for Level 2/exploratory workflows rather than a guaranteed runtime path.
- Closed the parent live-portal-coverage issue after documenting broader live coverage samples for XING, StepStone, and TU Berlin in `docs/automation/live_scrape_coverage.md`. The remaining StepStone concern was first narrowed to a live location-normalization defect.
- Tightened the Ariadne location heuristic in `src/automation/ariadne/job_normalization.py` so StepStone hero metadata no longer accepts contract labels like `Feste Anstellung` as `location`. A newer broader live StepStone sample then exposed a different rescue/detail-page defect, which is now tracked separately.
- Expanded `docs/automation/live_scrape_coverage.md` with a broader live TU Berlin sample (`limit 3`). All sampled TU Berlin postings ingested successfully, including one BrowserOS-rescued variant, so TU Berlin broader-coverage is now considered resolved for the currently observed page envelope.
- Expanded `docs/automation/live_scrape_coverage.md` with a broader live XING sample (`limit 3`). All sampled XING postings ingested successfully, so XING broader-coverage is now considered resolved for the currently observed page envelope.
- Added `docs/automation/live_scrape_coverage.md` to record broader live scrape coverage evidence. The first broader StepStone sample confirms successful ingest across three live postings but exposes a remaining location-classification defect on some hero layouts.
- Added `docs/automation/browseros_chat_dependency_inventory.md` to explicitly inventory the current BrowserOS `/chat` dependency surface and distinguish Level 2 `/chat` workflows from MCP-first scrape rescue.
- Added `docs/automation/live_apply_validation_matrix.md` as the canonical live apply validation matrix, aligned BrowserOS setup/integration docs with the `127.0.0.1:9000/mcp` runtime contract, and added integration-test coverage that the matrix doc exists.
- Moved canonical job normalization ownership into `src/automation/ariadne/job_normalization.py` and updated `src/automation/motors/crawl4ai/scrape_engine.py` to delegate to that Ariadne semantic module. Added backend-neutral normalization tests in `tests/unit/automation/ariadne/test_job_normalization.py`, so the `raw` / `cleaned` / `extracted` contract is now owned and tested at the semantic layer rather than the motor layer.
- Extended XING normalization in `src/automation/motors/crawl4ai/scrape_engine.py` so rescue payloads preserve good CSS scalars, listing metadata can repair polluted teaser company/location values, and additional XING headings like `Deine Rolle`, `Qualifikation`, and `Beschreibung` are mined into canonical responsibility/requirement fields. Repeated live XING scrapes now ingest successfully.
- Updated BrowserOS runtime guidance so MCP is the required local contract for this repo's scrape rescue path, while `/chat` is optional for basic health checks. Added an ADR under `wiki/adrs/` and updated `browseros-check` to require healthy MCP rather than failing when `/chat` is unavailable.
- Tightened StepStone hero-field recovery in `src/automation/motors/crawl4ai/scrape_engine.py` so scalar extraction only reads the actual hero block, skips company-like values when recovering locations, and avoids matching navigation or description text as `company_name` or `location`. Repeated live StepStone scrapes now ingest clean company and location values.
- Updated `src/automation/motors/crawl4ai/scrape_engine.py` so `_extract_payload()` now follows an explicit `raw -> cleaned -> extracted` flow in memory, with cleaned-stage normalization diagnostics persisted into `cleaned.json`. This makes the extraction/normalization boundary explicit instead of mutating one payload through the whole pipeline.
- Updated `src/automation/motors/crawl4ai/scrape_engine.py` so every ingest attempt now persists explicit `raw.json`, `cleaned.json`, and `extracted.json` artifacts where applicable, plus `validation_error.json` for failed validations. This makes failed live scrape runs debuggable from one artifact bundle and formalizes the `raw` / `cleaned` / `extracted` output contract in stored artifacts.
- Updated `README.md`, `docs/automation/browseros_setup.md`, and `AGENTS.md` so BrowserOS startup is documented from the top level: launch `/home/jp/BrowserOS.AppImage --no-sandbox`, use `http://127.0.0.1:9000` as the stable local front door, and start BrowserOS work from `docs/reference/external_libs/browseros/readme.txt`.
- Updated scrape fallback configuration in `src/automation/motors/crawl4ai/scrape_engine.py` so extraction rescue order is explicitly defined by `AUTOMATION_EXTRACTION_FALLBACKS`, with BrowserOS as the default fallback and Gemini rescue opt-in.
- Updated the BrowserOS scrape rescue path in `src/automation/motors/crawl4ai/scrape_engine.py` to use documented BrowserOS MCP tools (`new_hidden_page`, `navigate_page`, `get_page_content`, `get_dom`) instead of depending on BrowserOS `/chat`.
- Updated `src/automation/main.py` so the CLI basic usage now includes BrowserOS startup guidance, a `browseros-check` subcommand for runtime verification, and help text that points users to the AppImage launch flow and fallback configuration.
- Updated `src/automation/motors/crawl4ai/scrape_engine.py` normalization to merge CSS scalars with BrowserOS rescue output, recover hero-block scalars, clean teaser-style locations, and convert prose-only responsibility sections into canonical list fields; this restored live ingest for StepStone and TU Berlin while leaving StepStone scalar scoping as a remaining live-data issue.
- Updated `plan_docs/issues/gaps/portal-real-life-validation.md` from a broad execution plan into a parent atomization issue and regenerated `plan_docs/issues/Index.md` with the resulting dependency graph.
- Removed the parent atomization issue after splitting it into executable child issues and updated `plan_docs/issues/Index.md` to make scrape validation the next root issue.
- Executed the live scrape validation issue against real XING, StepStone, and TU Berlin portal pages, then replaced it with `plan_docs/issues/gaps/crawl4ai-live-portal-navigation-aborts.md` after all three failed on the same shared BrowserOS-injected Crawl4AI navigation abort.
- Added three follow-up Crawl4AI auth issues for persistent profile reuse, BrowserOS session import, and env-secret login automation so authenticated Crawl4AI execution can be built explicitly instead of remaining only contractual.
- Resolved the shared live portal navigation blocker by switching scrape runs to Crawl4AI's local browser in `src/automation/motors/crawl4ai/scrape_engine.py`, confirmed XING, StepStone, and TU Berlin listing pages now load, then updated `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md` with precise diagnosis after a broad normalization patch attempt was reverted to avoid breaking existing tests. The remaining shared blocker is extraction normalization in `SmartScraperAdapter`.

### Fixed
- Stabilized StepStone rescue extraction in `src/automation/ariadne/job_normalization.py` by blacklisting error page titles (e.g. "Your connection was interrupted") and adding a swap guard to recover misclassified company names from the location field. Broader StepStone live scrapes now correctly ingest or fail with explicit degraded-page diagnostics.
- Fixed `build_default_portal_route` in `src/automation/portals/routing.py` — removed `detail_url` from routing decisions (was causing `mailto:` and `ftp://` schemes to incorrectly resolve as "onsite") and fixed email routing condition (was missing cases where `application_url` was a non-http scheme).

### Added
- Added 15 comprehensive routing unit tests covering all 4 outcomes (onsite, external_url, email, unsupported) for XING, StepStone, and LinkedIn in `tests/unit/automation/portals/test_routing.py`.
- Added `_retry_crawl()` to `src/automation/motors/crawl4ai/scrape_engine.py` with 3 retries and exponential backoff (up to 2^attempt seconds wait), applied to `_load_schema_samples()` and `fetch_job()`. Added `LogTag.RETRY = "[🔁]"`. Resolved TU Berlin transient `net::ERR_NETWORK_CHANGED` errors.
- Added 4 retry regression tests for `_retry_crawl()` in `tests/unit/automation/motors/crawl4ai/test_scrape_engine.py`.
- Added `C4AIMotorProvider` auth support in `src/automation/motors/crawl4ai/apply_engine.py` — three tracks: (1) `persistent_profile` uses `user_data_dir` in BrowserConfig, (2) `env_secrets` bootstraps login via C4AI DSL script (navigates to login URL, fills username/password selectors, submits), (3) `mixed` executes both. All guarded against missing secrets or absent login forms.
- Added 5 auth tests in `TestC4AIMotorProviderAuth` covering `persistent_profile`, `env_secrets`, `mixed`, and missing-secret guard paths.
- Added 15 structural portal map tests across XING, LinkedIn, and StepStone (`tests/unit/automation/portals/{xing,linkedin,stepstone}/test_apply_map.py`).
- Added 2 new E2E apply tests in `tests/unit/automation/test_apply_e2e.py` for email handoff and unsupported routing failures.
- Added 2 new danger detection tests in `tests/unit/automation/ariadne/test_danger_detection.py` for email and unsupported routing scenarios.
- Added test infrastructure: `tests/fixtures/test-cv.pdf` (minimal valid PDF), `tests/integration/test_live_apply.py` (BrowserOS infrastructure tests that skip when unavailable), `tests/integration/__init__.py`.
- Added `docs/automation/browseros_setup.md` documenting BrowserOS setup, session management, and troubleshooting.

### Removed
- Removed all gap and unimplemented issue files from `plan_docs/issues/`. Index is now empty. `plan_docs/issues/Index.md` retains only the root instructions and legacy audit.

## [2026-04-08] - BrowserOS Recording Contracts And Level 2 Trace Capture

### Added
- Added split external-library reference indexes under `docs/reference/external_libs/browseros/` and `docs/reference/external_libs/crawl4ai/`, including focused BrowserOS docs for live validation, deep findings, recording strategy, and Ariadne recording guidance.
- Added `plan_docs/contracts/browseros_level2_trace.md` to formalize BrowserOS `/chat` SSE capture as the Level 2 trace boundary.
- Added `plan_docs/issues/unimplemented/browseros-recording-to-ariadne.md` plus follow-up BrowserOS issue refinements for deep interface alignment and level separation.
- Added regression coverage in `tests/unit/automation/motors/browseros/agent/test_openbrowser.py` for BrowserOS `/chat` trace capture, tool-event parsing, and rate-limit handling.
- Added `src/automation/motors/browseros/agent/normalizer.py` plus regression coverage in `tests/unit/automation/motors/browseros/agent/test_normalizer.py` for turning BrowserOS Level 2 tool streams into Ariadne step candidates.
- Added `src/automation/motors/browseros/agent/promoter.py` plus regression coverage in `tests/unit/automation/motors/browseros/agent/test_promoter.py` for promoting deterministic Level 2 candidates into draft replay paths.
- Added `src/automation/motors/browseros/cli/recording.py` plus regression coverage in `tests/unit/automation/motors/browseros/cli/test_recording.py` for deterministic BrowserOS MCP call and snapshot recording.
- Added `src/automation/motors/browseros/cdp_recorder.py` plus regression coverage in `tests/unit/automation/motors/browseros/test_cdp_recorder.py` for low-level BrowserOS CDP capture parsing.
- Added `src/automation/motors/browseros/runtime.py` plus regression coverage in `tests/unit/automation/motors/browseros/test_runtime.py` for shared BrowserOS runtime endpoint resolution.
- Added `src/automation/motors/browseros/promotion_models.py`, `src/automation/motors/browseros/promotion_pipeline.py`, and `src/automation/motors/browseros/cli/promoter.py` plus regression coverage for shared BrowserOS promotion intermediates, grouping, validation, and deterministic MCP promotion.

### Changed
- Updated `src/automation/motors/browseros/agent/openbrowser.py` to capture raw BrowserOS `/chat` SSE traces instead of driving the internal BrowserOS UI as if it were a deterministic motor.
- Updated `src/automation/motors/browseros/cli/client.py` to default to the stable local BrowserOS front door on `9000` and optionally record MCP calls/snapshots.
- Updated BrowserOS MCP and `/chat` clients to resolve endpoints through the shared BrowserOS runtime config instead of ad-hoc hardcoded assumptions.
- Updated BrowserOS and automation docs in `docs/automation/README.md`, `docs/reference/README.md`, `src/automation/README.md`, and `src/automation/motors/README.md` to point at the new external-reference indexes and recording guidance.
- Updated BrowserOS planning contracts and references so Level 2 BrowserOS recording is modeled as raw trace capture first, Ariadne normalization second.
- Updated `src/automation/ariadne/session.py` so failed Level 2 BrowserOS path discovery persists both the captured raw trace and normalized Level 2 step candidates for later promotion.
- Updated `src/automation/motors/browseros/agent/openbrowser.py` so successful deterministic Level 2 candidates are promoted into a draft replay path instead of remaining capture-only.
- Updated `src/automation/motors/browseros/agent/provider.py` so BrowserOS agent sessions can delegate Level 2 capture/discovery into the working `/chat` client even though deterministic motor execution is still not implemented.
- Updated BrowserOS MCP and Level 2 promotion paths so both now converge through one shared promotion intermediate and one shared validation/grouping pipeline before replay-path emission.
- Updated `src/automation/motors/browseros/cli/client.py` with explicit wrappers for `focus`, `handle_dialog`, `take_enhanced_snapshot`, `get_dom`, and `get_page_content`.
- Updated BrowserOS live validation docs with a successful low-load discovery -> promotion -> deterministic replay proof against `https://example.com/`.

## [2026-04-08] - ATS Analyzer And Conceptual Motor Coverage

### Added
- Added `src/automation/ariadne/form_analyzer.py` to classify unknown ATS form fields, map them to candidate-profile semantics, and escalate unsafe or unresolved fields for human review.
- Added conceptual BrowserOS agent scaffolding docs in `src/automation/motors/browseros/agent/README.md` plus regression coverage for BrowserOS agent, vision, and OS-native stub providers under `tests/unit/automation/motors/`.
- Added analyzer regression coverage in `tests/unit/automation/ariadne/test_form_analyzer.py` and dynamic form-analysis coverage for BrowserOS and Crawl4AI replayers.

### Changed
- Updated `src/automation/motors/browseros/cli/replayer.py` to execute the backend-neutral `analyze_form` intent, prefer interactive BrowserOS targets over label text, and pause for HITL review when form semantics are unknown.
- Updated `src/automation/motors/crawl4ai/replayer.py` to expand `analyze_form` into concrete actions, require actionable selectors before deterministic replay, and preserve CV/cover-letter upload routing.
- Updated conceptual motor tests and package layout so duplicated `test_provider.py` basenames collect cleanly and assert against the current danger-report contract.

## [2026-04-07] - OpenBrowser Level 2 Agent Integration

### Added
- Added Level 2 agent fallback integration using `OpenBrowserClient` in `src/automation/motors/browseros/agent/openbrowser.py` to wrap the OpenBrowser `/chat` API.
- Added OpenBrowser fallback logic in `src/automation/ariadne/session.py` to dynamically generate and store a deterministic `AriadnePath` when a portal flow is missing or broken.
- Updated documentation in `docs/automation/ariadne_semantics.md` to clarify the OpenBrowser Level 2 agent's role as the author of semantic paths.

## [2026-04-07] - Apply Danger Detection

### Added
- Added shared apply danger contracts and detection logic in `src/automation/ariadne/danger_contracts.py` and `src/automation/ariadne/danger_detection.py` for DOM-text, screenshot-text, routing, and prior-submission guards.
- Added regression coverage in `tests/unit/automation/ariadne/test_danger_detection.py` and expanded Ariadne/apply regression tests for danger-driven pauses and updated motor protocol fixtures.

### Changed
- Updated `src/automation/ariadne/session.py` to evaluate normalized danger reports before and after step execution, pausing on CAPTCHA/login/anti-bot signals and aborting on duplicate or offsite routing risks.
- Updated BrowserOS and Crawl4AI motor sessions to expose shared danger inspection hooks, and refreshed apply end-to-end expectations for the new guard checks.

## [2026-04-07] - Apply HITL Channel

## [2026-04-07] - Credential Store Contract

### Added
- Added `src/automation/credentials.py` with domain-bound credential metadata, env-var secret references, and persistent-profile hints for login-required apply flows.
- Added regression coverage in `tests/unit/automation/test_credentials.py`, `tests/unit/automation/test_cli.py`, and `tests/unit/automation/ariadne/test_session.py` for credential-store validation, CLI wiring, and motor injection.

### Changed
- Updated `src/automation/main.py`, `src/automation/storage.py`, and `src/automation/ariadne/session.py` so apply runs and manual session setup can load a metadata-only credential store without persisting secret values.
- Updated BrowserOS and Crawl4AI motor providers to accept resolved credential metadata and expose only non-secret login context during HITL capture.

### Added
- Added persisted apply HITL contracts in `src/automation/ariadne/hitl.py` plus storage helpers for interrupt payloads, operator decisions, and per-step BrowserOS artifacts.
- Added Ariadne and BrowserOS regression coverage for interrupt persistence, operator resume/abort handling, and BrowserOS observation-to-HITL escalation.

### Changed
- Updated `src/automation/ariadne/session.py` so apply runs pause into an `interrupted` state, capture HITL context, and resume the active session after a terminal operator decision.
- Updated BrowserOS and Crawl4AI motor sessions to expose the new human-intervention hook, including BrowserOS screenshot and snapshot capture in `src/automation/motors/browseros/cli/backend.py`.
- Updated `src/automation/motors/browseros/cli/replayer.py` so human-required steps and live observation blockers raise the shared HITL interrupt contract instead of hard-aborting inline.

## [2026-04-07] - Portal Routing Layer

### Added
- Added portal-specific routing modules in `src/automation/portals/*/routing.py` plus shared routing contracts in `src/automation/portals/contracts.py`.
- Added routing regression coverage in `tests/unit/automation/portals/test_routing.py`, `tests/unit/automation/ariadne/test_session.py`, and `tests/unit/automation/test_apply_e2e.py` for onsite, external ATS, and email handoff decisions.

### Changed
- Updated `src/automation/ariadne/session.py` so apply runs resolve portal routing before opening a motor session and fail early when the job requires an unsupported external or email handoff.
- Updated automation architecture docs to document the new portal routing layer.

## [2026-04-07] - Cross-Portal Discovery

### Added
- Added company-domain discovery contracts plus scrape-engine regression coverage for ATS-aware link filtering and seeded company-source fan-out.

### Changed
- Updated `src/automation/motors/crawl4ai/scrape_engine.py` so scrape runs follow external `application_url` targets into same-domain ATS or careers pages, then ingest the discovered roles under dedicated `company-<domain>` source namespaces.
- Updated automation docs to describe the new cross-portal company-domain discovery pass.

## [2026-04-07] - Application Routing Enrichment

### Added
- Added Crawl4AI routing enrichment coverage in `tests/unit/automation/motors/crawl4ai/test_scrape_engine.py` for heuristic email routing, selective LLM interpretation, and persisted review diagnostics.

### Changed
- Enriched `src/automation/motors/crawl4ai/scrape_engine.py` with a post-ingest routing pass that normalizes application targets, selectively invokes Crawl4AI's LLM extraction only for low-confidence cases, and persists routing confidence and diagnostics into the validated ingest payload.
- Extended `src/automation/ariadne/models.py` so `JobPosting` carries routing confidence and diagnostics alongside the resolved application fields.

## [2026-04-07] - Cross-Motor ApplyMeta Consistency

### Added
- Added paired cross-motor apply regression coverage in `tests/unit/automation/test_apply_e2e.py` to run equivalent BrowserOS and Crawl4AI apply flows, normalize persisted `ApplyMeta`, and compare the shared execution side effects for submitted and dry-run runs.

## [2026-04-07] - Apply End-To-End Coverage

### Added
- Added end-to-end style apply coverage in `tests/unit/automation/test_apply_e2e.py` to drive the real CLI apply path through `AriadneSession`, motor-provider contracts, and persisted `apply_meta.json` artifacts for submitted and dry-run runs.

## [2026-04-07] - XING Listing Metadata Composition

### Added
- Added XING scrape regression coverage for teaser-card metadata extraction and pre-validation listing/detail payload composition.

### Changed
- Reworked `src/automation/motors/crawl4ai/portals/xing/scrape.py` to capture job-scoped listing card fragments, preserve richer teaser evidence, and feed listing-side publication metadata into the shared scrape-engine merge path before `JobPosting` validation.

## [2026-04-07] - BrowserOS Letter Upload Routing

### Added
- Added BrowserOS replay regression coverage for dedicated cover-letter upload routing and missing-letter guardrails.
- Added Crawl4AI compiler coverage to keep the new cover-letter upload intent on the shared Ariadne execution path.

### Changed
- Added the backend-neutral `upload_letter` Ariadne intent and replay-contract variant.
- Wired `letter_path` through `src/automation/motors/browseros/cli/replayer.py` so BrowserOS can route cover-letter uploads independently from CV uploads.
- Mapped `upload_letter` to Crawl4AI upload compilation so the semantic action stays portable across deterministic motors.

## [2026-04-07] - BrowserOS Replay Contract Boundary

### Added
- Added `src/automation/ariadne/contracts.py` with narrow replay DTOs and adaptation helpers for motor-facing step execution.
- Added BrowserOS regression coverage for replay-contract navigation, Ariadne-to-replay step adaptation, and direct-model import guardrails.

### Changed
- Refactored `src/automation/motors/browseros/cli/backend.py` and `src/automation/motors/browseros/cli/replayer.py` to consume Ariadne replay contracts instead of importing the full domain model module.

## [2026-04-07] - Crawl4AI LLM Rescue Strategy

### Added
- Added fallback extraction coverage in `tests/unit/automation/motors/crawl4ai/test_scrape_engine.py` to assert the scrape engine wires Crawl4AI-native `LLMExtractionStrategy` during rescue runs.

### Changed
- Replaced the scrape-engine's direct LiteLLM fallback in `src/automation/motors/crawl4ai/scrape_engine.py` with a second Crawl4AI pass that uses `LLMExtractionStrategy` and preserves the existing `JobPosting` validation contract.

## [2026-04-07] - Representative Crawl4AI Schema Samples

### Added
- Added representative-schema regression coverage in `tests/unit/automation/motors/crawl4ai/test_scrape_engine.py` to verify multi-sample schema selection and blocked teaser-selector rejection.

### Changed
- Reworked `src/automation/motors/crawl4ai/scrape_engine.py` so schema generation learns from multiple representative detail pages, validates each generated schema across the sample set, and rejects selectors that target teaser or related-job modules before caching.

## [2026-04-07] - Language Detection Hardening

### Added
- Added Crawl4AI scrape-engine coverage for short English titles, mixed-language postings, and persisted fallback `original_language` values in `tests/unit/automation/motors/crawl4ai/test_scrape_engine.py`.

### Changed
- Replaced the scrape-engine's naive German-marker fallback in `src/automation/motors/crawl4ai/scrape_engine.py` with deterministic `langdetect` scoring blended with job-posting lexical heuristics.
- Declared `langdetect` in `pyproject.toml` so editable installs keep the hardened language detector available.

## [2026-04-07] - Trace Normalization Quality

### Added
- Added normalization regression coverage in `tests/unit/automation/ariadne/test_normalizer.py` for canonical state inference, observation synthesis, and selector fallback behavior.

### Changed
- Reworked `src/automation/ariadne/normalizer.py` to infer draft Ariadne states from screenshot and page signatures, group actions on navigation and state changes, and synthesize stable `observe.required_elements` from action and visibility evidence.
- Added inferred task generation for normalized traces so draft portal maps include a usable task contract instead of path-only output.

## [2026-04-07] - Discovery Entry Contract

### Added
- Added `src/automation/motors/crawl4ai/contracts.py` with typed discovery-entry models for listing-side scrape evidence.
- Added portal scrape coverage for StepStone, XING, and TU Berlin structured discovery entries.

### Changed
- Normalized `SmartScraperAdapter` discovery handling around validated `ScrapeDiscoveryEntry` payloads.
- Persisted job-scoped discovery metadata, including `job_id` and source metadata, into `listing.json` and `listing_case.json` artifacts.
- Updated Crawl4AI portal adapters to return structured discovery entries instead of plain URLs.

## [2026-04-07] - Profile Context And Candidate Store

### Added
- Added `src/automation/contracts.py` with typed `CandidateProfile`, `ApplyJobContext`, and `ExecutionContext` models for apply runs.
- Added storage and CLI coverage in `tests/unit/automation/test_storage.py` and `tests/unit/automation/test_cli.py` for candidate profile loading.

### Changed
- Wired `--profile-json` through `src/automation/main.py` into `AriadneSession.run()`.
- Centralized candidate profile validation in `src/automation/storage.py` and replaced the hardcoded apply profile stub in `src/automation/ariadne/session.py`.
- Updated automation docs to point at the new runtime profile contract.

## [2026-04-07] - AriadneSession Orchestrator

### Added
- Added `AriadneSession` as the apply orchestrator in `src/automation/ariadne/session.py`.
- Added `MotorProvider` and `MotorSession` protocols in `src/automation/ariadne/motor_protocol.py`.
- Added AST-based boundary guardrails in `tests/unit/automation/test_boundary_guardrails.py`.

### Changed
- Refactored the Crawl4AI apply backend to `C4AIMotorProvider` and `C4AIMotorSession` in `src/automation/motors/crawl4ai/apply_engine.py`.
- Refactored the BrowserOS apply backend to `BrowserOSMotorProvider` and `BrowserOSMotorSession` in `src/automation/motors/browseros/cli/backend.py`.
- Inlined backend selection into `src/automation/main.py` and removed the old registry-based flow.
- Moved portal map coverage under `tests/unit/automation/portals/`.

### Fixed
- Fixed the pre-existing `navigate()` argument order bug in `BrowserOSReplayer`.

## [2026-04-06] - Unified Automation Phase 2

### Added
- **Ariadne Semantic Layer**: Implemented `AriadnePortalMap`, `AriadneState`, `AriadneTask`, and `AriadnePath` models in `src/automation/ariadne/models.py`.
- **Crawl4AI Compiler**: New motor-specific compiler in `src/automation/motors/crawl4ai/compiler/` that translates Ariadne Paths into optimized C4A-Scripts.
- **Ariadne Navigator**: Added state-aware replay logic in `src/automation/ariadne/navigator.py` for handling portal deviations.
- **Ariadne Recorder**: Implemented session capture and raw trace persistence in `src/automation/ariadne/recorder.py`.
- **Capability Registry**: Documented motor-specific superpowers and intent mapping in `docs/automation/ariadne_capabilities.md`.
- **Standardized Storage**: Created `src/automation/storage.py` to decouple execution engines from the data plane.

### Changed
- **Unified CLI**: Refactored `src/automation/main.py` to use the new semantic maps and standardized storage.
- **Engine Refactor**: Migrated Crawl4AI and BrowserOS motors to consume unified JSON maps instead of motor-specific Python adapters.
- **Documentation**: Standardized `README.md` and `CLAUDE.md` to follow mandatory project guidelines.

### Fixed
- Restored **Dry-Run** functionality in the Crawl4AI engine.
- Fixed closure bug in `_check_state_presence`.
- Re-implemented **File Upload** hooks for semantic paths.
- Standardized error handling with specific `AriadneError` exceptions and screenshot capture on failure.

### Removed
- Deprecated `src/automation/ariadne/portal_models.py` and its associated Phase 1 models.
- Removed dead Python-based portal definitions in `src/automation/portals/`.
- Cleaned up legacy `BrowserOSPlaybook` models and traces.
