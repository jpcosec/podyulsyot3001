# Anti Bot Danger Detection

## Explanation

The design already names anti-bot, CAPTCHA, duplicate-submit, and other risk signals, but there is no implemented detection library that turns those ideas into reusable guards.

## Reference in src

- `src/automation/ariadne/session.py`
- `src/automation/motors/browseros/cli/replayer.py`
- `src/automation/motors/crawl4ai/apply_engine.py`

## What to fix

Add a shared detection layer for risky states during apply execution.

## How to do it

Create reusable detectors for DOM text, screenshots, routing signals, and prior submission state; return normalized danger codes; and let Ariadne/motors decide whether to retry, pause, or abort.

## Does it depend on another issue?

Yes — `plan_docs/issues/unimplemented/apply-hitl-channel.md`.
