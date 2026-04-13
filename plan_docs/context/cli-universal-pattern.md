---
type: pattern
domain: cli
source: src/automation/main.py:1
---

# Pill: Universal CLI Pattern

## Pattern
The CLI must be an agnostic transport layer. It parses a user instruction and dynamic key-value pairs (`kwargs`), then passes them directly to the graph's `initial_state`.

## Implementation
```python
def parse_kwargs(kwarg_list: list[str]) -> dict:
    """Converts ['key=value'] into {'key': 'value'}"""
    return dict(item.split("=", 1) for item in kwarg_list if "=" in item)

# argparse setup
parser.add_argument("instruction", help="Natural language order")
parser.add_argument("kwargs", nargs="*", help="Dynamic key=value pairs")

# Injection into initial_state
initial_state = {
    "instruction": args.instruction,
    "session_memory": parse_kwargs(args.kwargs),
    # ... other standard fields
}
```

## When to use
Use in Phase 1 `cli-rewrite.md`.

## Verify
Run `python -m src.automation.main "test" key=val` and assert `initial_state["session_memory"]["key"] == "val"`.
