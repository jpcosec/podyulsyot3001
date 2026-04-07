# Credential Store

## Explanation

Login-required flows need domain-bound credentials or persistent sessions, but there is no implemented credential store or injection contract yet.

## Reference in src

- `src/automation/main.py`
- `src/automation/ariadne/session.py`

## What to fix

Create a safe credential/session contract for login-required apply flows.

## How to do it

Define domain-bound secrets metadata, prefer persistent browser profiles where possible, keep passwords out of run artifacts, and expose only the minimum runtime interface needed by motors or higher-level agents.

## Does it depend on another issue?

No.
