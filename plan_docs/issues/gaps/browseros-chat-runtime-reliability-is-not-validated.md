# BrowserOS Chat Runtime Reliability Is Not Validated

**Explanation:** Even where `/chat` is still intentionally used, the repository lacks a bounded statement of runtime reliability backed by current live evidence.

**Reference:**
- `src/automation/motors/browseros/agent/openbrowser.py`
- `src/automation/motors/browseros/agent/provider.py`
- `docs/reference/external_libs/browseros/live_agent_validation.md`

**What to fix:** Validate the runtime reliability of BrowserOS `/chat` for the workflows that still intentionally depend on it and document the actual support level.

**How to do it:**
1. Use the `/chat` dependency inventory as the scope boundary.
2. Exercise the in-scope `/chat` workflows against the local BrowserOS runtime.
3. Record whether each workflow is supported, optional, experimental, or best-effort.
4. Update docs/contracts to match observed reality.

**Depends on:** none
