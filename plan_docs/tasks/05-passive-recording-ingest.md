# Task: Passive recording — Chrome DevTools Recorder ingestion

## Explanation
A human can navigate a portal manually in Chrome, then export the session as a Chrome DevTools Recorder JSON. This JSON can be ingested to build an `AriadneThread` without running the LangGraph loop at all. This is the zero-code bootstrap path for a new portal: record once manually, promote to a Thread, then let the system take over.

Currently there is no ingestion path. `AriadneThread` can only be built via active recording (Theseus/Delphi traces).

## Reference
- `src/automation/ariadne/thread/thread.py` — `AriadneThread.add_step()`, `save()`
- `src/automation/ariadne/thread/action.py` — action types that must be inferred from raw Puppeteer events
- Chrome DevTools Recorder format: each step has `type` (`click`, `navigate`, `keyDown`, etc.), `target`, `selectors`

## What to fix
Implement `ingest_passive_trace(devtools_json: dict) -> AriadneThread`:
1. Parse the Chrome DevTools Recorder JSON format
2. Map each step's `type` + `selectors` to the closest `TransitionAction` or `PassiveAction`
3. Build a sequence of transitions and construct an `AriadneThread`
4. The resulting thread is "draft" — it should be verified by a live run before being treated as canonical

## How to do it
- Add `src/automation/ariadne/thread/passive_ingest.py` — `ingest(devtools_json: dict, portal_name: str, mission_id: str) -> AriadneThread`
- Mapping logic: Chrome `click` → `TransitionAction(operation="click")`, `navigate` → `TransitionAction(operation="navigate")`, `keyDown` → `PassiveAction` or `TransitionAction(operation="fill")` depending on context
- Room IDs in the resulting thread will be URL-based (from `navigate` steps) and will need Labyrinth verification on first live run
- Mark thread as `draft=True` (field to add to `AriadneThread`) until a live run confirms all transitions

## Depends on
- Chrome DevTools Recorder JSON schema must be documented or tested against a real export
- `AriadneThread` may need a `draft: bool` field to distinguish unverified threads from confirmed ones
