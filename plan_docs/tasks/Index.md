# Task Index

Execution queue for Ariadne 2.0. One issue per file. Each must be closed with a single resolving commit.

## Open

| # | File | Description | Depends on |
|---|------|-------------|------------|
| 02 | [delphi-llm-implementation](02-delphi-llm-implementation.md) | Full Delphi cold path: LLM call via BrowserOS MCP, Set-of-Mark, HITL escalation | — |
| 03 | [extraction-action-portal-dictionary](03-extraction-action-portal-dictionary.md) | Wire `ExtractionAction` through `PortalDictionary` and `Extractor` protocol | — |
| 04 | [c4a-script-compilation](04-c4a-script-compilation.md) | Thread → C4AScript compiler (Level 0 execution) | — |
| 05 | [passive-recording-ingest](05-passive-recording-ingest.md) | Chrome DevTools Recorder JSON → `AriadneThread` ingestion path | — |

## Closed

| # | Description |
|---|---|
| 01 | `is_mission_complete` field + terminal routing in `builder.py` |
