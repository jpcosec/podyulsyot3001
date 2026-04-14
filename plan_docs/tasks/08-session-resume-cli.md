# Task 08: Session resume — pick up from any domain mid-browse

## Explanation
After tasks 06+07, portals accumulate on disk automatically. Task 08 adds explicit
session continuity: the CLI can resume a prior navigation session at the URL the
browser is currently on (or a given URL), loading the existing Labyrinth and Thread
for that domain without starting from scratch.

## What to change

### 1. `main.py` — `--resume` flag
- `--resume` (flag, no arg): read current browser URL, derive domain, load PortalRegistry for that domain, skip `navigate` to homepage, start the loop at Observe
- `--portal` remains for when you want to force a specific portal name regardless of URL

### 2. `AriadneState` seeding
- When `--resume` is set, seed `domain` and `portal_name` from the current URL rather than requiring them as CLI args
- `mission_id` can be `"session_<date>"` if not provided

### 3. `InterpreterNode` — tolerate pre-seeded domain
- If `state["domain"]` is already set on entry, skip the URL-to-portal derivation step
- Just map instruction → mission_id as today

## Depends on
- Task 06 (PortalRegistry, domain in state)

## Tests to add
- Integration-level test: seed state with a pre-existing domain, verify Labyrinth/Thread are loaded from disk
