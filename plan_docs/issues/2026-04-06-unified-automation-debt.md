# Unified Automation Debt & Gaps

This document tracks known technical debt, structural gaps, and missing features across the unified automation system.

## 1. Structural & Boundary Debt
- [x] **Residual Directories**: `src/scraper/` and `src/apply/` have been fully deleted.
- [ ] **Translator Layer**: `ApplyAdapter` (crawl4ai) is still "domain-aware". It should be a pure translator/replayer that doesn't know about `AriadnePath` internals beyond the translation boundary.
- [ ] **Portal Adapter Location**: `src/automation/motors/crawl4ai/portals/*/apply.py` should be moved or refactored to a cleaner "Mapper" pattern.
- [ ] **BrowserOS Executor Imports**: The executor still imports domain models from `src.automation.ariadne.models`. It should depend on a clean interface.
- [ ] **Registry Logic**: Backend and portal selection moved to a dynamic factory, but `registry.py` still does inline map loading for BrowserOS. This knowledge belongs in the provider.

## 2. Ariadne Lifecycle Gaps
- [ ] **Promotion Workflow**: No CLI command or logic to promote a `draft` trace to a `canonical` map.
- [ ] **Trace Normalization Logic**: `normalizer.py` currently uses basic heuristics; needs enhancement to infer states from screenshots/DOM.
- [ ] **Recording Persistence**: Normalization currently doesn't persist to the final map location.

## 3. Motor Implementation Issues
- [ ] **Crawl4AI Performance**: `_get_live_state` opens a new crawler/session per step. It should reuse the active crawler instance.
- [ ] **Status Shadowing**: The `run()` method in `apply_engine.py` shadows the `status` variable, leading to potential logic errors.
- [ ] **BrowserOS CSS Support**: BrowserOS motor now supports the `css` field in `AriadneTarget` using the `search_dom` tool.
- [ ] **Conceptual Motors**: Implement stubs for `motors/browseros/agent/`, `motors/os_native_tools/`, and `motors/vision/`.

## 4. Feature & Doc Debt
- [ ] **UPLOAD Conflict**: `ariadne_capabilities.md` and `translators.md` disagree on how UPLOAD is handled (DSL vs. Hook).
- [ ] **Candidate Field Management**: `ApplyAdapter` uses hardcoded profile fields. Integrate with a real candidate profile store.
- [ ] **Language Detection**: Improve naive heuristic in `scrape_engine.py`.
- [ ] **Application Routing**: Implement `portals/*/routing.py` to handle ATS vs. Inline vs. Email redirects.

## 5. Test Gaps
- [ ] **End-to-End Integration**: Tests that run the full CLI command through a real motor.
- [ ] **Cross-Motor Artifact Consistency**: Ensure Crawl4AI and BrowserOS produce identical `ApplyMeta` for the same path.
