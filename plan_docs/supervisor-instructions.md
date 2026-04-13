# Supervisor Instructions: Final Validation & Gatekeeping

As the supervisor/orchestrator, your role is to ensure that the work delivered by zero-context subagents meets the absolute architectural standards of Ariadne 2.0 before any Phase is considered closed.

## 🛂 The Gatekeeper's Checklist

### 1. The "Laws of Physics" Audit
For every PR or completed task, run a manual and automated check for violations:
- **Law 1 (Async):** Grep for `open(`, `time.sleep(`, and `requests.` in `src/automation/ariadne/`.
- **Law 2 (Session):** Verify the `async with executor` wrapper hasn't been moved inside a node.
- **Law 3 (DOM):** Check `hinting.js` for `innerHTML` or `appendChild` on portal elements.
- **Law 4 (Circuit Breakers):** Verify that every loop has a counter and escalates to HITL.
- **DIP Enforcement:** Run `test_domain_isolation.py` to ensure no infrastructure leaks into the domain.

### 2. The Fitness Gauntlet
No Phase Completion Ritual is valid unless the following command is 100% green:
```bash
python -m pytest tests/architecture/ -v
```

### 3. Subagent Lifecycle Verification
Verify that the subagent performed the "Execution Ritual" from `STANDARDS.md`:
- [ ] Are existing tests updated or deleted?
- [ ] Are new tests added and passing?
- [ ] Is `changelog.md` updated with high-signal descriptions?
- [ ] Is the `.md` issue file deleted?
- [ ] Is the issue removed from `Index.md`?
- [ ] Does the commit message follow the `docs:` or `feat:` convention?

### 4. Real-World Calibration (Epic Gate)
Before closing an Epic (e.g., Epic 1 or Epic 2), you MUST execute the "Validation" commands listed in the Epic file using a real browser. Do not rely on unit tests for final Epic sign-off.

### 5. Context Pill Freshness
After major implementation changes, run the `plan_docs/context-pill-audit.md` guide to see if any Patterns or Models have become stale. If a subagent changed a function signature, you MUST update the corresponding Context Pill.

---

## 🛑 Failure Protocol
If a subagent violates a Law of Physics or breaks a fitness test:
1. **DO NOT MERGE.** 
2. **Re-Atomize:** Identify the specific gap that allowed the violation.
3. **Create Guardrail Pill:** If the violation was "creative," create a new Pill that explicitly forbids that specific implementation pattern.
4. **Re-Dispatch:** Send the task back to a subagent with the new, stricter context.

## 🏗️ Phase Completion Sign-off
A Phase is only complete when:
1. The `Index.md` section for that Phase is 100% checked.
2. The `Context Audit Report` for the Phase is updated.
3. All `tests/architecture/` are green.
4. (For Phase 1+) The Universal CLI can successfully execute a discovery mission.
