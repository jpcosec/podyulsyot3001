# ATS Form Analyzer

## Explanation

The system can replay known forms, but it still lacks the analyzer that maps unknown ATS fields to candidate/profile values for first-time or unrecorded portals.

## Reference in src

- `src/automation/ariadne/session.py`
- `src/automation/motors/browseros/cli/replayer.py`
- `src/automation/motors/crawl4ai/apply_engine.py`

## What to fix

Implement form analysis that identifies fillable fields, classifies their semantics, and resolves them against available profile and artifact inputs.

## How to do it

Define a typed field-map model, inspect apply pages to extract labels/selectors/types, map them to candidate semantics, and require review for unknown or unsafe fields before submission.

## Does it depend on another issue?

Yes — `plan_docs/issues/gaps/profile-context-and-candidate-store.md`.
