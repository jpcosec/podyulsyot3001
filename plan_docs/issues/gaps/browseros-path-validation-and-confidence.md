# BrowserOS Path Validation And Confidence

**Explanation:** The system can now produce draft BrowserOS-discovered paths, but it still lacks a formal acceptance gate that decides when a path is trustworthy enough to replay automatically versus when it must stay as review-only evidence.

**Reference:** `src/automation/motors/browseros/agent/promoter.py`, `src/automation/ariadne/session.py`, `plan_docs/contracts/browseros_level2_trace.md`, `docs/reference/external_libs/browseros/recording_for_ariadne.md`

**What to fix:** Add an explicit validation and confidence layer for BrowserOS-promoted paths before they are accepted as replay-ready Ariadne artifacts.

**How to do it:** 1. Define path-level validation rules for intents, targets, values, and required evidence. 2. Compute step-level and path-level confidence outcomes such as `promotable`, `partial`, or `blocked`. 3. Persist those outcomes alongside the raw trace and promoted draft path. 4. Add tests for accepted, partial, and rejected BrowserOS path candidates.

**Depends on:** `plan_docs/issues/gaps/browseros-level2-promotion-hardening.md`, `plan_docs/issues/gaps/browseros-level1-mcp-promotion.md`
