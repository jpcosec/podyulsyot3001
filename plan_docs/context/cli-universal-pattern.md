---
type: pattern
domain: cli
source: plan_docs/design/browseros-adapter-lifecycle.md:111
---

# Pill: Universal CLI Pattern

## Pattern
The CLI is orchestration-only. It parses `instruction`, `--portal`, and dynamic `key=value` args, instantiates the chosen adapter, and runs the graph inside `async with adapter:`. Adapter startup, polling, and health logic do not live in `main.py`.

## Implementation
```python
args = _build_parser().parse_args(argv)
session_memory = parse_kwargs(args.kwargs)
adapter = build_adapter(args)

async with adapter as active_adapter:
    state = build_initial_state(args, session_memory)
    app = build_graph(active_adapter)
    await run_graph(app, state)
```

## When to use
Use for CLI entrypoints and command wiring in `src/automation/main.py`.

## Verify
```bash
python -m src.automation.main "easy_apply" --portal stepstone url=https://example.com
grep -rn "subprocess\|127.0.0.1:9000\|requests\.get" src/automation/main.py
```
