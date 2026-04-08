# BrowserOS Discovery To Replay Validation

**Explanation:** Unit tests now cover BrowserOS capture, normalization, and draft promotion, but there is still no end-to-end proof that a BrowserOS-discovered path can be promoted and then replayed deterministically through the normal Ariadne execution path.

**Reference:** `src/automation/ariadne/session.py`, `src/automation/motors/browseros/agent/openbrowser.py`, `src/automation/motors/browseros/agent/promoter.py`, `src/automation/motors/browseros/cli/replayer.py`, `docs/reference/external_libs/browseros/live_agent_validation.md`

**What to fix:** Add one end-to-end validation flow that starts from BrowserOS discovery, produces a draft path, and confirms that the promoted result is replayable through the deterministic automation path.

**How to do it:** 1. Create one low-load live validation scenario suitable for BrowserOS on this machine. 2. Capture the BrowserOS trace, promoted path, and replay artifacts under one session. 3. Replay the promoted path through the deterministic execution layer and verify the expected outcome. 4. Record the procedure and results in the BrowserOS live validation docs.

**Depends on:** `plan_docs/issues/gaps/browseros-path-validation-and-confidence.md`
