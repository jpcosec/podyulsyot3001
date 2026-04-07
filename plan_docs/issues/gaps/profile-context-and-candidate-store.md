# Profile Context And Candidate Store

## Explanation

Apply runs still use a hardcoded profile stub even though `--profile-json` is already parsed by the CLI. Candidate data is not yet sourced from a real profile store or injected into the apply context.

## Reference in src

- `src/automation/main.py`
- `src/automation/ariadne/session.py`

## What to fix

Wire CLI profile input into `AriadneSession.run()` and replace the development stub with a durable candidate profile source.

## How to do it

Add a `profile` parameter to `AriadneSession.run()`, pass the parsed JSON from `main.py`, validate it against a typed model, and centralize candidate/profile loading so later features can reuse the same contract.

## Does it depend on another issue?

No.
