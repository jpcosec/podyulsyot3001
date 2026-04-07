# Cross Motor ApplyMeta Consistency

## Explanation

Crawl4AI and BrowserOS can both execute apply flows, but there is no assertion that they emit the same `ApplyMeta` contract for equivalent runs. That leaves cross-backend behavior free to drift.

## Reference in src

- `src/automation/ariadne/models.py`
- `src/automation/motors/crawl4ai/apply_engine.py`
- `src/automation/motors/browseros/cli/backend.py`

## What to fix

Lock down the shared artifact contract across both motors.

## How to do it

Create paired test fixtures that run the same semantic path through each motor implementation and compare normalized `ApplyMeta` output and key side effects.

## Does it depend on another issue?

Yes — `plan_docs/issues/gaps/end-to-end-apply-coverage.md`.
