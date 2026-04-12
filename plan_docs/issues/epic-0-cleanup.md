# EPIC 0: Demolition & Recycling (Cleanup)

**Explanation:** Prepare the workspace for the Ariadne 2.0 refactor by isolating legacy code and clearing contradictory specifications. This ensures a clean slate for implementing the LangGraph architecture.

**Tasks:**
1.  **Isolate Legacy Code**: Move "Valyrian Fire" files (`session.py`, `discovery_session.py`, `navigator.py`, `motor_protocol.py`) and "Major Surgery" files (`job_normalization.py`, `form_analyzer.py`, `danger_detection.py`, `hitl.py`) to a temporary `src/automation/ariadne/legacy/` directory.
2.  **Clear Contradictions**: Purge all legacy design documents and fragmented issue files identified in the architectural audit.
3.  **Setup QA Backlog**: Move all specific portal bugs and validation tasks to a root-level `QA_BACKLOG.md`.

**Success Criteria:**
- `src/automation/ariadne/` contains only "Safe Harbor" files and core models.
- All legacy logic is sequestered in `/legacy/`.
- No contradictory specs remain in `plan_docs/`.

**Depends on:** none
