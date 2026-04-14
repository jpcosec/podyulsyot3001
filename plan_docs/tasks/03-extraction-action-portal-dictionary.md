# Task: ExtractionAction wiring through PortalDictionary

## Explanation
`ExtractionAction` exists in `src/automation/ariadne/thread/action.py` and `PortalDictionary` exists in `src/automation/ariadne/extraction/portal_dictionary.py`, but there is no path that connects them. When `TheseusNode` receives an `ExtractionAction` from `AriadneThread.get_next_step()`, it has no way to execute it — the motor only handles `MotorCommand` (click, fill, navigate, etc.), not extraction.

## Reference
- `src/automation/ariadne/thread/action.py` — `ExtractionAction` dataclass
- `src/automation/ariadne/extraction/portal_dictionary.py` — `PortalDictionary`, maps `schema_id → JsonCssExtractionStrategy`
- `src/automation/ariadne/extraction/schema_builder.py` — `build()` generates schemas (LLM, cached)
- `src/automation/adapters/browser_os.py` — `BrowserOSAdapter.act()` only handles motor commands
- `src/automation/langgraph/nodes/theseus.py` — dispatches actions from the thread

## What to fix
1. `TheseusNode` must detect when a step contains `ExtractionAction` and route it to the extraction path instead of `Motor.act()`
2. `BrowserOSAdapter` (or a separate `Extractor` protocol) must accept an `ExtractionAction`, look up the schema in `PortalDictionary`, and run `JsonCssExtractionStrategy` against the current snapshot
3. Extraction results must be appended to `state["extracted_data"]`

## How to do it
- Add an `Extractor` protocol to `contracts/` with `async def extract(action: ExtractionAction, snapshot: SnapshotResult) -> list[dict]`
- Implement it in `adapters/browser_os.py` using `PortalDictionary.load(portal_name)` to resolve the strategy
- Inject `Extractor` into `TheseusNode` alongside `Motor`
- In `TheseusNode.__call__`, dispatch based on action type: `Motor.act()` for transition/passive, `Extractor.extract()` for extraction

## Depends on
- `PortalDictionary.load()` must be called before the graph runs (same as `Labyrinth.load()` in `builder.py`)
- `schema_builder.build()` handles the LLM call + caching — no changes needed there
