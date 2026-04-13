# 🔍 Ariadne 2.0: Consistency & Specificity Check (Ritual Phase A)

## 1. Role & Workflow Reset
*   **Correction**: Previous turns incorrectly mixed Supervisor and Executor roles.
*   **Current Mode**: Supervisor/Orchestrator.
*   **Goal**: Ensure the quality of the planning docs and context pills. **No implementation code will be written.**

## 2. Phase A: Pill Health Audit

### A1: Inventory
*   Total pills found: 39 (including newly created `interpreter-node.md`, `sensor-contract.md`, `motor-contract.md`).
*   Location: `plan_docs/context/`.

### A2: Freshness & Contradiction Check
*   **Contradiction Found**: `sensor-contract.md` and `motor-contract.md` define separate protocols. The code in `src/automation/ariadne/contracts/base.py` uses a combined `Executor`.
*   **Decision**: As per `STANDARDS.md`, the design (pills) wins. **A new gap issue MUST be created to refactor the code**, but the supervisor will NOT implement it.
*   **Staleness**: `ariadne-models.md` is stale (missing `job_id`, `portal_name`, etc.). `ariadne-map-model.md` uses incorrect class names.

## 3. Mandatory Actions (Supervisor)
*   [ ] Create Gap Issue: `refactor-protocol-separation.md` (to align code with pills).
*   [ ] Recreate Stale Pill: `ariadne-models.md` from `models.py:121`.
*   [ ] Recreate Stale Pill: `ariadne-map-model.md` from `models.py:161`.
*   [ ] Audit Phase 0.5 issues for Zero-Context Sufficiency (Phase B).

---

## 4. Questions for HITL
*   **B. Recorder & Motor Interaction**: Should we use an Observer pattern or a returning trace in `ExecutionResult`?
*   **C. HITL Escalation**: Should HITL be a dedicated node or a mode in `Delphi`?
*   **D. Persistence**: Should `Labyrinth` and `AriadneThread` handle their own DB connections or have them injected?
