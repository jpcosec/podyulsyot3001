# Automation Issues Index

This file is the entrypoint for subagents deployed to solve issues in this repository.

## Working rule for every issue

Once an issue is solved:
1. Check whether any existing test is no longer valid.
2. Add new tests where necessary.
3. Run the relevant tests.
4. Update `changelog.md`.
5. Delete the solved issue from both this index and the corresponding file in `plan_docs/issues/`.
6. Make a commit that clearly states what was fixed.

## Legacy audit

- No indexed issue is currently marked for deletion instead of repair.
- The prior root-level issues entrypoint and ad-hoc root issue file were replaced so the issue entrypoint now follows `docs/standards/issue_guide.md`.
- Extraction and normalization issues are resolved on the currently tested live scrape pages (XING, StepStone, TU Berlin).
- Remaining issues now cover backend-specific live apply validation and evaluation of a possible LangGraph MCP-adapter path as an alternative to `/chat`-style agent orchestration.

## Roots

- `plan_docs/issues/gaps/browseros-appimage-path-is-hardcoded.md`
- `plan_docs/issues/gaps/browseros-xing-live-apply-is-not-validated.md`
- `plan_docs/issues/gaps/browseros-stepstone-live-apply-is-not-validated.md`
- `plan_docs/issues/gaps/browseros-linkedin-live-apply-is-not-validated.md`
- `plan_docs/issues/gaps/crawl4ai-xing-live-apply-is-not-validated.md`
- `plan_docs/issues/gaps/crawl4ai-stepstone-live-apply-is-not-validated.md`
- `plan_docs/issues/gaps/crawl4ai-linkedin-live-apply-is-not-validated.md`
- `plan_docs/issues/unimplemented/langgraph-mcp-adapter-integration-is-not-evaluated.md`

## Parallelizable groups

- Depth 0:
  - `plan_docs/issues/gaps/browseros-appimage-path-is-hardcoded.md`
  - `plan_docs/issues/gaps/browseros-xing-live-apply-is-not-validated.md`
  - `plan_docs/issues/gaps/browseros-stepstone-live-apply-is-not-validated.md`
  - `plan_docs/issues/gaps/browseros-linkedin-live-apply-is-not-validated.md`
  - `plan_docs/issues/gaps/crawl4ai-xing-live-apply-is-not-validated.md`
  - `plan_docs/issues/gaps/crawl4ai-stepstone-live-apply-is-not-validated.md`
  - `plan_docs/issues/gaps/crawl4ai-linkedin-live-apply-is-not-validated.md`
  - `plan_docs/issues/unimplemented/langgraph-mcp-adapter-integration-is-not-evaluated.md`
- Depth 1: `plan_docs/issues/gaps/live-apply-flows-are-not-fully-validated.md`

## Blockers

- `plan_docs/issues/gaps/live-apply-flows-are-not-fully-validated.md` blocks confidence in real end-to-end application behavior because scrape validation does not prove live apply correctness.
- `plan_docs/issues/unimplemented/langgraph-mcp-adapter-integration-is-not-evaluated.md` blocks architectural clarity on whether future agent orchestration should keep leaning on `/chat`-style flows or move toward a stronger MCP-adapter path.

## Dependency graph

- `plan_docs/issues/gaps/browseros-appimage-path-is-hardcoded.md` -> no dependencies
- `plan_docs/issues/gaps/browseros-xing-live-apply-is-not-validated.md` -> no dependencies
- `plan_docs/issues/gaps/browseros-stepstone-live-apply-is-not-validated.md` -> no dependencies
- `plan_docs/issues/gaps/browseros-linkedin-live-apply-is-not-validated.md` -> no dependencies
- `plan_docs/issues/gaps/crawl4ai-xing-live-apply-is-not-validated.md` -> no dependencies
- `plan_docs/issues/gaps/crawl4ai-stepstone-live-apply-is-not-validated.md` -> no dependencies
- `plan_docs/issues/gaps/crawl4ai-linkedin-live-apply-is-not-validated.md` -> no dependencies
- `plan_docs/issues/gaps/live-apply-flows-are-not-fully-validated.md` -> `plan_docs/issues/gaps/browseros-xing-live-apply-is-not-validated.md`, `plan_docs/issues/gaps/browseros-stepstone-live-apply-is-not-validated.md`, `plan_docs/issues/gaps/browseros-linkedin-live-apply-is-not-validated.md`, `plan_docs/issues/gaps/crawl4ai-xing-live-apply-is-not-validated.md`, `plan_docs/issues/gaps/crawl4ai-stepstone-live-apply-is-not-validated.md`, `plan_docs/issues/gaps/crawl4ai-linkedin-live-apply-is-not-validated.md`
- `plan_docs/issues/unimplemented/langgraph-mcp-adapter-integration-is-not-evaluated.md` -> no dependencies

## Current indexed issues

1. `plan_docs/issues/gaps/live-apply-flows-are-not-fully-validated.md`
   - Scope: Parent issue for live apply validation after child tasks define the matrix and validate each backend
   - Depends on:
     - `plan_docs/issues/gaps/browseros-xing-live-apply-is-not-validated.md`
     - `plan_docs/issues/gaps/browseros-stepstone-live-apply-is-not-validated.md`
     - `plan_docs/issues/gaps/browseros-linkedin-live-apply-is-not-validated.md`
     - `plan_docs/issues/gaps/crawl4ai-xing-live-apply-is-not-validated.md`
     - `plan_docs/issues/gaps/crawl4ai-stepstone-live-apply-is-not-validated.md`
     - `plan_docs/issues/gaps/crawl4ai-linkedin-live-apply-is-not-validated.md`
   - Expected outputs: Working live apply matrix, backend-specific evidence, updated docs/routing assumptions

2. `plan_docs/issues/gaps/browseros-appimage-path-is-hardcoded.md`
   - Scope: Remove hardcoded AppImage path from runtime resolution and move to env configuration.
   - Depends on: none
   - Expected outputs: Configurable AppImage path, updated docs.

3. `plan_docs/issues/gaps/browseros-xing-live-apply-is-not-validated.md`
   - Scope: Validate BrowserOS-backed live apply flows for XING against the matrix
   - Depends on: none
   - Expected outputs: BrowserOS XING live apply evidence and support status

4. `plan_docs/issues/gaps/browseros-stepstone-live-apply-is-not-validated.md`
   - Scope: Validate BrowserOS-backed live apply flows for StepStone against the matrix
   - Depends on: none
   - Expected outputs: BrowserOS StepStone live apply evidence and support status

5. `plan_docs/issues/gaps/browseros-linkedin-live-apply-is-not-validated.md`
   - Scope: Validate BrowserOS-backed live apply flows for LinkedIn against the matrix
   - Depends on: none
   - Expected outputs: BrowserOS LinkedIn live apply evidence and support status

6. `plan_docs/issues/gaps/crawl4ai-xing-live-apply-is-not-validated.md`
   - Scope: Validate Crawl4AI-backed live apply flows for XING against the matrix
   - Depends on: none
   - Expected outputs: Crawl4AI XING live apply evidence and support status

7. `plan_docs/issues/gaps/crawl4ai-stepstone-live-apply-is-not-validated.md`
   - Scope: Validate Crawl4AI-backed live apply flows for StepStone against the matrix
   - Depends on: none
   - Expected outputs: Crawl4AI StepStone live apply evidence and support status

8. `plan_docs/issues/unimplemented/langgraph-mcp-adapter-integration-is-not-evaluated.md`
    - Scope: Evaluate whether LangGraph MCP adapters should become the preferred graph/agent orchestration path for MCP-backed workflows in this repo
    - Depends on: none
    - Expected outputs: Architectural decision, scope analysis, and follow-up issue split if adoption is recommended

