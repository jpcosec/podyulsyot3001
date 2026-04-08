# BrowserOS Agent Interface Coverage

**Explanation:** BrowserOS Level 2 capture and promotion now work through `/chat`, but the BrowserOS integration still uses only a narrow subset of the documented BrowserOS interfaces. The remaining gap is no longer basic communication - it is incomplete interface coverage for real-world sessions.

**Reference:** `src/automation/motors/browseros/cli/client.py`, `src/automation/motors/browseros/cli/replayer.py`, `src/automation/motors/browseros/agent/openbrowser.py`, `src/automation/motors/browseros/agent/provider.py`, `docs/reference/external_libs/browseros/readme.txt`

**What to fix:** Expand BrowserOS integration coverage so the project supports the highest-value MCP and agent-facing interfaces needed for realistic deterministic replay and agent-assisted discovery.

**How to do it:** 1. Audit the still-unused BrowserOS MCP tools that matter for apply flows, especially `focus`, `handle_dialog`, `take_enhanced_snapshot`, `get_dom`, and `get_page_content`. 2. Add wrappers and tests only for the interfaces that materially improve replay or recording quality. 3. Remove or avoid any stale assumptions that still refer to superseded BrowserOS interface paths. 4. Add one low-load live proof for any newly adopted interface.

**Depends on:** `plan_docs/issues/gaps/browseros-runtime-endpoint-resolution.md`
