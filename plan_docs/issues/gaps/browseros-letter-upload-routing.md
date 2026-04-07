# BrowserOS Letter Upload Routing

## Explanation

`letter_path` reaches the BrowserOS step executor but is not actually consumed by action execution yet. Cover-letter uploads cannot be routed independently from CV uploads.

## Reference in src

- `src/automation/motors/browseros/cli/replayer.py`
- `src/automation/ariadne/models.py`

## What to fix

Define and wire a semantic action path for cover-letter uploads.

## How to do it

Add a dedicated intent or metadata contract for letter uploads, route `letter_path` into `_execute_action`, and cover the new behavior with replay tests.

## Does it depend on another issue?

No.
