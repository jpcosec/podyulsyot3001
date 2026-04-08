# BrowserOS Level 1 MCP Promotion

**Explanation:** Deterministic BrowserOS MCP recording is now available, but the recorded calls and snapshots are not yet promoted into draft Ariadne paths through the same quality bar as Level 2 traces. That leaves the deterministic BrowserOS path incomplete as a recording source.

**Reference:** `src/automation/motors/browseros/cli/client.py`, `src/automation/motors/browseros/cli/recording.py`, `src/automation/motors/browseros/agent/promoter.py`, `docs/reference/external_libs/browseros/recording_for_ariadne.md`

**What to fix:** Implement promotion from recorded BrowserOS MCP traces into draft Ariadne paths using the shared BrowserOS promotion intermediate.

**How to do it:** 1. Add MCP-trace normalization into the shared BrowserOS promotion intermediate. 2. Resolve snapshot-local element IDs into stable target hints using adjacent snapshots and call context. 3. Reuse the existing promotion pipeline to emit draft replay paths from deterministic MCP sessions. 4. Add regression tests for click, fill, select, upload, and navigate MCP recordings.

**Depends on:** `plan_docs/issues/unimplemented/browseros-shared-promotion-intermediate.md`
