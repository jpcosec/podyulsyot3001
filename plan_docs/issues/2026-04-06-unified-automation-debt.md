# Unified Automation Debt & Gaps

This document tracks known technical debt, structural gaps, and missing features across the unified automation system.

## 1. Structural Debt
- [x] **Residual Directories**: `src/scraper/` and `src/apply/` have been fully deleted.
- [ ] **Scraper Refactor**: Scrape adapters in `src/automation/portals/*/scrape.py` still use Python models instead of JSON Maps.
- [ ] **Registry Logic**: Backend and portal selection are hardcoded in `src/automation/main.py`. Should move to a dynamic factory.

## 2. Ariadne Lifecycle Gaps
- [ ] **Promotion Workflow**: No CLI command or logic to promote a `draft` trace to a `canonical` map.
- [ ] **Trace Normalization Logic**: `normalizer.py` currently uses basic heuristics; needs enhancement to infer states from screenshots/DOM.
- [ ] **Recording Persistence**: Normalization currently doesn't persist to the final map location.

## 3. Motor Gaps
- [ ] **Conceptual Motors**: Implement stubs for `motors/browseros/agent/`, `motors/os_native_tools/`, and `motors/vision/`.
- [ ] **BrowserOS CSS Support**: BrowserOS motor currently relies on text matching; needs to support the `css` field in `AriadneTarget`.

## 4. Feature Debt
- [ ] **Candidate Field Management**: `ApplyAdapter` uses hardcoded profile fields. Integrate with a real candidate profile store.
- [ ] **Language Detection**: Improve naive heuristic in `scrape_engine.py`.
- [ ] **Application Routing**: Implement `portals/*/routing.py` to handle ATS vs. Inline vs. Email redirects.

## 5. Test Gaps
- [ ] **End-to-End Integration**: Tests that run the full CLI command through a real motor.
- [ ] **Cross-Motor Artifact Consistency**: Ensure Crawl4AI and BrowserOS produce identical `ApplyMeta` for the same path.
