---
type: guardrail
law: 1
domain: ariadne
source: src/automation/ariadne/graph/orchestrator.py:1
---

# Pill: Law 1 — No Blocking I/O

## Rule
No graph node, portal mode, or capability inside `ariadne/` may block the event loop. All disk, network, and subprocess calls must use `async/await`.

## ❌ Forbidden
```python
open("config.json", "r")   # blocks event loop
time.sleep(1)              # blocks event loop
requests.get(url)          # blocks event loop
json.load(open(path))      # double violation
```

## ✅ Correct
```python
import aiofiles, asyncio, httpx

async with aiofiles.open("config.json", mode="r") as f:
    content = await f.read()

await asyncio.sleep(1)

async with httpx.AsyncClient() as client:
    resp = await client.get(url)
```

## Verify
```bash
python -m pytest tests/architecture/test_sync_io_detector.py -q
# spot-check:
grep -rn "time\.sleep\|requests\.\|open(" src/automation/ariadne/
```
