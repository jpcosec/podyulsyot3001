# Task Index

Execution queue for Ariadne 2.0. One issue per file. Each must be closed with a single resolving commit.

## Open

| #  | File | Description | Status |
|----|------|-------------|--------|
| 06 | [url-first-portal-registry](06-url-first-portal-registry.md) | `domain` in state + `PortalRegistry` — dynamic Labyrinth/Thread per visited domain | — |
| 07 | [llm-schema-discovery](07-llm-schema-discovery.md) | `PortalExtractor` LLM fallback — propose + cache CSS selectors for unknown portals | — |
| 08 | [session-resume-cli](08-session-resume-cli.md) | `--resume` CLI flag — pick up from current browser URL without restarting | — |

## Closed

| # | Description |
|---|---|
| 01 | `is_mission_complete` field + terminal routing in `builder.py` |
| 02 | Delphi LLM cold path: Gemini reasoning, circuit breaker, HITL escalation |
| 03 | ExtractionAction wiring through PortalDictionary and Extractor protocol |
| 04 | Thread → C4AScript compiler + degradation wrapper in CLI |
| 05 | Passive recording ingest: Chrome DevTools Recorder JSON → draft AriadneThread |
