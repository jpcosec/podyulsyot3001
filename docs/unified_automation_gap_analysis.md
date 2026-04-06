# Unified Automation Gap Analysis — 2026-04-06

This document identifies gaps between the current state of the `unified-automation` repository and the goals defined in the **Unified Automation Refactor Plan** and **Design Spec**.

## 1. Structural Migration Gaps

While the `src/automation/` package is mostly functional, some structural remnants of the old architecture persist.

- [ ] **Stale Root Files**:
    - `README.md` (root): Still describes `src/scraper/` and `src/apply/` as the primary modules. Needs a full update to reflect the unified `src.automation.main` CLI.
    - `CLAUDE.md`: Severely outdated. Describes "Postulator 3000" features (matching, translation, TUI) that are not part of this narrowed worktree or have been superseded by the new structure.
- [ ] **Residual Directories**:
    - `src/scraper/` and `src/apply/` still exist as empty directories with `__pycache__`. They should be fully deleted as per the plan.
- [ ] **Module Exports**:
    - `src/automation/ariadne/__init__.py` and `src/automation/motors/__init__.py` are empty. They could be used to expose primary models or entry points for better ergonomics.

## 2. Functional Implementation Gaps

Several components mentioned in the architectural vision are missing or only partially implemented.

### Ariadne Subsystem
Ariadne is currently just a schema for portal definitions.
- [ ] **Lifecycle Modules**: `storage.py`, `recorder.py`, `replayer.py`, and `promotion.py` are missing. These are required for full recording and replay of automation paths.
- [ ] **Common Language Translator**: There is no neutral "translator" that compiles Ariadne steps into motor-specific representations. Currently, each motor translator (e.g., in `motors/crawl4ai/portals/`) manually implements the steps.
- [ ] **Recording Persistence**: No mechanism currently exists to normalize BrowserOS or Crawl4AI traces into Ariadne replay artifacts.

### Motors
- [ ] **Conceptual Motors**: `motors/browseros/agent/`, `motors/os_native_tools/`, and `motors/vision/` are entirely missing.
- [ ] **BrowserOS Replay**: BrowserOS currently uses its own `models.py` for playbooks. The plan to migrate this to a backend-neutral Ariadne schema is deferred.

### Portals
- [ ] **Routing Knowledge**: `portals/*/routing.py` is missing. This is needed to handle application routing (email vs. inline vs. ATS) as planned.
- [ ] **Portal Coverage**: While StepStone, XING, TU Berlin, and LinkedIn are partially implemented, their capabilities are inconsistent (e.g., LinkedIn only has an `apply` definition, no `scrape`).

## 3. Implementation Gaps & Technical Debt

- [ ] **Candidate Fields**: The `ApplyAdapter` in `motors/crawl4ai/apply_engine.py` has a `TODO` for including candidate personal fields. Currently, only basic contact info is handled.
- [ ] **Language Detection**: `motors/crawl4ai/scrape_engine.py` uses a "naive heuristic" for language detection (`TODO` L113).
- [ ] **Application Routing Choice**: A `TODO` in `motors/crawl4ai/models.py` (L58) indicates an open decision about whether application routing belongs in the scrape-time contract.
- [ ] **Registry Logic**: Backend and portal selection are currently hardcoded in `src/automation/main.py`. As the number of portals and motors grows, this should move to a dedicated registry or factory.
- [ ] **Environment Consistency**: `README.md` and `src/automation/README.md` have slightly different environment variable recommendations (e.g., `GOOGLE_API_KEY` vs `GEMINI_API_KEY`).

## 4. Test Gaps

- [ ] **Integration Tests**: There are no integration tests that exercise the full flow from `src.automation.main` through a motor into a portal.
- [ ] **Data Plane Validation**: Tests in `tests/unit/automation/` mostly mock the `DataManager`. There are no tests verifying that the directory structure created on disk (`data/jobs/.../nodes/ingest/`) strictly follows the new design.
- [ ] **Cross-Motor Consistency**: No tests ensure that different motors (Crawl4AI vs. BrowserOS) produce compatible `ApplyMeta` or `ApplicationRecord` artifacts for the same portal.

## 5. Documentation Gaps

- [ ] **External References**: `docs/reference/external_libs/` is mentioned in the plan but contains only `crawl4ai_custom_context.md`. Other library references (BrowserOS MCP, Playwright) are missing.
- [ ] **How-to Guides**: While the `README.md` explains how to *add* a portal, there is no guide on how to *record* a new path or *promote* a trace to a stable replay asset.
