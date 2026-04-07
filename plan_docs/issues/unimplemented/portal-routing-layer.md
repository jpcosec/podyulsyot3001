# Portal Routing Layer

## Explanation

There is no runtime routing module yet for portal-specific apply branching such as inline form, ATS redirect, or email handoff. The apply stack has fields for these cases but no dedicated routing implementation.

## Reference in src

- `src/automation/portals/`
- `src/automation/ariadne/session.py`

## What to fix

Add per-portal routing modules that decide which apply path to invoke from the enriched job state.

## How to do it

Introduce `routing.py` modules under portal packages, define a small routing result contract, and let `AriadneSession` or the CLI dispatch according to that result before opening a motor session.

## Does it depend on another issue?

Yes — `plan_docs/issues/unimplemented/application-routing-enrichment.md`.
