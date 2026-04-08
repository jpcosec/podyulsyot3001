# Changelog

All notable changes to this project will be documented in this file.

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

### Changed
- Updated `src/automation/motors/browseros/agent/openbrowser.py` to capture raw BrowserOS `/chat` SSE traces instead of driving the internal BrowserOS UI as if it were a deterministic motor.
- Updated `src/automation/motors/browseros/cli/client.py` to default to the stable local BrowserOS front door on `9000` and optionally record MCP calls/snapshots.
- Updated BrowserOS and automation docs in `docs/automation/README.md`, `docs/reference/README.md`, `src/automation/README.md`, and `src/automation/motors/README.md` to point at the new external-reference indexes and recording guidance.
- Updated BrowserOS planning contracts and references so Level 2 BrowserOS recording is modeled as raw trace capture first, Ariadne normalization second.
- Updated `src/automation/ariadne/session.py` so failed Level 2 BrowserOS path discovery persists both the captured raw trace and normalized Level 2 step candidates for later promotion.
- Updated `src/automation/motors/browseros/agent/openbrowser.py` so successful deterministic Level 2 candidates are promoted into a draft replay path instead of remaining capture-only.

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
