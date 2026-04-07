# End To End Apply Coverage

## Explanation

Current automation coverage is mostly unit-level. There is no test that drives the full CLI apply command through a real motor contract from argument parsing to `ApplyMeta` persistence.

## Reference in src

- `src/automation/main.py`
- `src/automation/ariadne/session.py`
- `src/automation/motors/`
- `tests/unit/automation/`

## What to fix

Add end-to-end style tests that exercise the actual apply path across CLI, AriadneSession, motor provider, and storage.

## How to do it

Use fixture-backed motor doubles or lightweight real-session shims, run `main.py apply` with test maps and job state, and assert final persisted artifacts and execution ordering.

## Does it depend on another issue?

No.
