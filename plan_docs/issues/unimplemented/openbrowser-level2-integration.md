# OpenBrowser Level 2 Integration

## Explanation

The fallback agent-driven apply mode described in the design docs is not integrated yet. There is no implementation that invokes OpenBrowser, passes execution context, and stores returned playbooks.

## Reference in src

- `src/automation/ariadne/session.py`
- `src/automation/motors/browseros/`

## What to fix

Implement the Level 2 agent path for unknown or broken flows.

## How to do it

Wrap the OpenBrowser API behind a local service interface, pass job/profile/document context explicitly, validate returned playbook data, and hand successful outputs into the promotion/storage flow.

## Does it depend on another issue?

Yes — `plan_docs/issues/unimplemented/credential-store.md` and `plan_docs/issues/unimplemented/apply-hitl-channel.md`.
