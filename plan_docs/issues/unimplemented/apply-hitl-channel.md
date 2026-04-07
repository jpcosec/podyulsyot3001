# Apply HITL Channel

## Explanation

Apply flows need a pause-and-resume human-in-the-loop path for login walls, CAPTCHAs, unknown fields, and risky submissions, but that channel is not implemented yet.

## Reference in src

- `src/automation/ariadne/session.py`
- `src/automation/motors/browseros/cli/replayer.py`

## What to fix

Add a resumable HITL mechanism for active apply sessions.

## How to do it

Define an interrupt contract with screenshot/context payloads, terminal-first resume controls, and persisted operator decisions so interrupted runs can continue safely.

## Does it depend on another issue?

No.
