# Implement: Observe Node Logic

**Explanation:** The `observe_node` in `src/automation/ariadne/graph/orchestrator.py` is currently a stub that returns mock data. To enable real-world navigation, it must call an Executor or Capability to fetch the current page URL, accessibility tree (DOM), and a base64 screenshot.

**Reference:** 
- `src/automation/ariadne/graph/orchestrator.py`
- `src/automation/ariadne/contracts/base.py` (Capability interfaces)

**What to fix:** A functional `observe_node` that updates the `AriadneState` with live browser data.

**How to do it:**
1.  Define a `SnapshotCapability` or update the `Executor` protocol to support a `take_snapshot` command.
2.  Implement the snapshot logic in the `BrowserOS` and `Crawl4AI` executors.
3.  Update the `observe_node` to dispatch the snapshot request and update the state fields.

**Depends on:** none
