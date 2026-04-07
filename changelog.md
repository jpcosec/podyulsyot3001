# Changelog

All notable changes to this project will be documented in this file.

## [2026-04-07] - Apply HITL Channel

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
