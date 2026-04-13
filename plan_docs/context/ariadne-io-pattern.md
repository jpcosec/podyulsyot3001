---
type: pattern
domain: ariadne
source: src/automation/ariadne/io.py:1
---

# Pill: Ariadne Shared I/O Pattern

## Pattern
Route Ariadne JSON and JSONL persistence through `src/automation/ariadne/io.py`. Graph-time paths should prefer the async helpers so recording, map loading, and trace reads do not block the event loop.

## Implementation
```python
from src.automation.ariadne.io import append_jsonl_async, read_json_async, write_json

payload = await read_json_async(map_path)
trace_path = await append_jsonl_async(trace_path, event)
output_path = write_json(output_path, draft_map, indent=2)
```

Use `asyncio.to_thread(...)` inside helper implementations when filesystem setup, JSON parsing, or serialization would otherwise run synchronously in the hot loop.

## When to use
Use for Ariadne modules that read or write JSON/JSONL artifacts, especially `repository.py`, `recording.py`, `promotion.py`, and graph hot-loop recording hooks.

## Verify
```bash
python -m pytest tests/architecture/test_sync_io_detector.py -q
python -m pytest tests/unit/automation/ariadne/test_recording_and_promotion.py -q
```
