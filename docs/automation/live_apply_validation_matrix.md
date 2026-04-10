# Live Apply Validation Matrix

This document defines the canonical live apply validation scope for this repository.

It exists so real apply validation can be executed safely and consistently across
portals and backends.

## Status Labels

- `supported` - intended validation target
- `dry-run only` - may be validated only with `--dry-run`
- `unsupported` - should not be validated as a live apply path
- `unknown` - not yet classified with enough confidence

## Global Prerequisites

- BrowserOS runtime available at `http://127.0.0.1:9000/mcp`
- Portal session authenticated when the backend/portal requires it
- Real CV path available, preferably `tests/fixtures/test-cv.pdf`
- Validation must persist evidence and outcomes for every run

## Matrix

| Portal | Backend | Mode | Status | Auth prerequisite | Expected outcome |
| --- | --- | --- | --- | --- | --- |
| `xing` | `browseros` | `dry-run` | `supported` | XING BrowserOS session | Ariadne path executes to dry-run stop or fails with a documented routing/apply reason |
| `xing` | `browseros` | live submit | `unknown` | XING BrowserOS session | Do not run until explicitly approved for real submission validation |
| `xing` | `crawl4ai` | `dry-run` | `supported` | portal-specific auth/profile if required | Ariadne path executes to dry-run stop or fails with a documented routing/apply reason |
| `xing` | `crawl4ai` | live submit | `unknown` | portal-specific auth/profile if required | Do not run until explicitly approved for real submission validation |
| `stepstone` | `browseros` | `dry-run` | `supported` | BrowserOS session if onsite apply is used | Either reaches dry-run stop or fails with documented `email` / `external_url` / `unsupported` routing outcome |
| `stepstone` | `browseros` | live submit | `unknown` | BrowserOS session if onsite apply is used | Do not run until explicitly approved for real submission validation |
| `stepstone` | `crawl4ai` | `dry-run` | `supported` | portal-specific auth/profile if onsite apply is used | Either reaches dry-run stop or fails with documented `email` / `external_url` / `unsupported` routing outcome |
| `stepstone` | `crawl4ai` | live submit | `unknown` | portal-specific auth/profile if onsite apply is used | Do not run until explicitly approved for real submission validation |
| `linkedin` | `browseros` | `dry-run` | `supported` | LinkedIn BrowserOS session | Ariadne path executes to dry-run stop or fails with a documented routing/apply reason |
| `linkedin` | `browseros` | live submit | `unknown` | LinkedIn BrowserOS session | Do not run until explicitly approved for real submission validation |
| `linkedin` | `crawl4ai` | `dry-run` | `unknown` | portal-specific auth/profile | Needs live validation before repo confidence can be claimed |
| `linkedin` | `crawl4ai` | live submit | `unknown` | portal-specific auth/profile | Do not run until explicitly approved for real submission validation |
| `tuberlin` | `browseros` | any apply mode | `unsupported` | none | Scrape portal only; not an onsite Ariadne apply target today |
| `tuberlin` | `crawl4ai` | any apply mode | `unsupported` | none | Scrape portal only; not an onsite Ariadne apply target today |

## Execution Rules

- Prefer `--dry-run` for all live validation unless a separate explicit approval
  exists for real submission behavior.
- If routing resolves to `email`, `external_url`, or `unsupported`, that counts
  as a valid observed outcome when it matches the job's real routing.
- Each validation run should record:
  - portal
  - backend
  - mode
  - job id / URL
  - auth/session assumption
  - observed outcome
  - artifact/evidence path

## Current Intended Follow-up Issues

- BrowserOS live apply backend validation
- Crawl4AI live apply backend validation
- Routing/docs updates when real apply behavior differs from assumptions

## Latest Evidence

- `2026-04-11` - `xing` + `browseros` + `dry-run` on job `150077807`
  - Runtime: BrowserOS MCP reachable at `http://127.0.0.1:9000/mcp`
  - Observed outcome: HITL pause at `open_modal`; required target `css="[data-testid='apply-button']"` was not found
  - Evidence: `data/jobs/xing/150077807/nodes/apply/meta/hitl_interrupt.json`
  - Snapshot: `data/jobs/xing/150077807/nodes/apply/proposed/hitl/step-001/browseros_snapshot.txt`
  - Note: the captured snapshot shows XING navigation/home elements instead of an apply surface, so the current map or route assumptions do not yet prove a successful dry-run path for this live posting
- `2026-04-11` - `stepstone` + `browseros` + `dry-run` on job `13314431`
  - Runtime: BrowserOS MCP reachable at `http://127.0.0.1:9000/mcp`
  - Observed outcome: HITL pause at `open_modal`; required target `css="[data-at='apply-button']"` was not found
  - Evidence: `data/jobs/stepstone/13314431/nodes/apply/meta/hitl_interrupt.json`
  - Snapshot: `data/jobs/stepstone/13314431/nodes/apply/proposed/hitl/step-001/browseros_snapshot.txt`
  - Note: the live StepStone page exposed visible `Ich bin interessiert` buttons in the BrowserOS snapshot instead of the mapped selector, so the current apply map assumptions do not yet prove a successful dry-run path for this posting
