# Unit Tests: Automation

Tests **mirror** `src/automation/` structure. For every `src/automation/module.py` that needs a test, create `tests/unit/automation/test_module.py`.

## Structure

```
tests/unit/automation/
├── test_main_*.py           # CLI tests (mirrors src/automation/main.py)
├── ariadne/                 # Mirrors src/automation/ariadne/
│   ├── test_*.py
├── motors/                  # Mirrors src/automation/motors/
│   └── test_*.py
├── adapters/                # Mirrors src/automation/adapters/
│   └── test_*.py
└── portals/                 # Mirrors src/automation/portals/
    └── test_*.py
```

## Running Tests

```bash
python -m pytest tests/unit/automation/ -q
```