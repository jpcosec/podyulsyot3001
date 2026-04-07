# Changelog

All notable changes to this project will be documented in this file.

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
