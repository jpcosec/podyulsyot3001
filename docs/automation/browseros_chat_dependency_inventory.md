# BrowserOS Chat Dependency Inventory

This document inventories the current BrowserOS `/chat` dependency surface in
this repository.

It exists to make `/chat` runtime validation scoping explicit.

## Classification Labels

- `required` - current repo workflow depends on `/chat` to function
- `optional` - workflow can work without `/chat`, but may use it when available
- `experimental` - intentionally exploratory or unstable path
- `legacy-doc-only` - documented/reference mention, but not part of the active required runtime path

## Current Inventory

| Area | File(s) | Purpose | Classification | Notes |
| --- | --- | --- | --- | --- |
| Level 2 trace client | `src/automation/motors/browseros/agent/openbrowser.py` | Capture BrowserOS `/chat` SSE traces | `required` | This is the main active code path that directly posts to `/chat` |
| Level 2 provider | `src/automation/motors/browseros/agent/provider.py` | Expose high-level agent session capture | `required` | Delegates into the `/chat` client |
| Level 2 models/normalizer | `src/automation/motors/browseros/agent/models.py`, `src/automation/motors/browseros/agent/normalizer.py` | Parse and normalize `/chat` SSE/tool events | `required` | Meaningful only when `/chat` traces are being captured |
| Runtime config | `src/automation/motors/browseros/runtime.py` | Expose `chat_url` alongside MCP URL | `optional` | Runtime config knows `/chat`, but scrape rescue no longer depends on it |
| BrowserOS setup doc | `docs/automation/browseros_setup.md` | Document optional `/chat` endpoint | `optional` | `/chat` is documented as optional for scrape rescue |
| BrowserOS reference docs | `docs/reference/external_libs/browseros/*.md` | External-lib research and validation notes | `legacy-doc-only` | Reference material, not a repo support guarantee by itself |
| Level 2 trace contract | `plan_docs/contracts/browseros_level2_trace.md` | Contract for `/chat` SSE traces | `required` | Contract still assumes `/chat` for Level 2 capture |

## Explicit Non-Dependencies

These important runtime paths do **not** currently depend on `/chat`:

- scrape rescue in `src/automation/motors/crawl4ai/scrape_engine.py`
  - uses BrowserOS MCP, not `/chat`
- `python -m src.automation.main browseros-check`
  - requires healthy MCP
  - reports `/chat`, but does not fail when `/chat` is unavailable
- BrowserOS startup guidance for basic repo use
  - MCP is the canonical required contract

## Current Support Reading

- `/chat` is still an active dependency for Level 2 trace capture workflows.
- `/chat` is not part of the required scrape rescue contract.
- `/chat` should currently be treated as workflow-specific, not universally required.

## Follow-up

The next validation task should test runtime reliability only for the
`required` `/chat` workflows listed here, not for MCP-first scrape rescue.
