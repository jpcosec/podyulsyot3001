# Supervisor Instructions: Final Validation & Gatekeeping

As the supervisor/orchestrator, your role is to validate work delivered by executors, accept or reject issue-closing commits, and clear issue-tracking artifacts only after a whole phase is complete.

## Role Boundary

The executor fixes the issue and creates the closing commit.
The executor then reports that commit in `plan_docs/issues/Index.md`.
The supervisor reviews that commit and decides whether the issue remains closed.

Supervisor-only responsibilities:
- reviewing the exact commit recorded in `plan_docs/issues/Index.md`
- accepting or rejecting the close attempt
- reverting failed issue commits individually
- enriching the issue file with review findings when a fix is rejected
- dispatching one `context_compiler` per issue during the initialization ritual, before implementation begins
- dispatching a `context_compiler` when the issue package is not clear enough for safe execution
- deleting resolved issue files and removing Index entries only after full phase completion

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

### 3. Executor Lifecycle Verification
Verify that the executor performed the "Execution Ritual" from `STANDARDS.md`:
- [ ] Are existing tests updated or deleted?
- [ ] Are new tests added and passing?
- [ ] Is `changelog.md` updated with high-signal descriptions?
- [ ] Did the executor create exactly one resolving commit for the issue?
- [ ] Does `plan_docs/issues/Index.md` mark that issue as `{closed with commit id <sha>}`?
- [ ] Is the Index bookkeeping present even if it is not committed yet?
- [ ] Does the commit message identify the issue being closed?
- [ ] Was the issue file preserved for supervisor review instead of being deleted early?
- [ ] Was the issue entry preserved in `Index.md` instead of being removed early?

### 3.1 Commit Review Rule
For every issue marked `{closed with commit id <sha>}`:
- inspect that exact commit
- verify it closes only the intended issue
- verify the implementation, tests, and docs match the issue scope
- accept it or reject it explicitly before phase sign-off

### 4. Real-World Calibration (Epic Gate)
Before closing an Epic (e.g., Epic 1 or Epic 2), you MUST execute the "Validation" commands listed in the Epic file using a real browser. Do not rely on unit tests for final Epic sign-off.

### 5. Context Pill Freshness
After major implementation changes, run the `plan_docs/context-pill-audit.md` guide to see if any Patterns or Models have become stale. If an executor changed a function signature, you MUST update the corresponding Context Pill.

---

## 🛑 Failure Protocol
If an executor violates a Law of Physics or breaks a fitness test:
1. **DO NOT MERGE.** 
2. **Re-Atomize:** Identify the specific gap that allowed the violation.
3. **Create Guardrail Pill:** If the violation was "creative," create a new Pill that explicitly forbids that specific implementation pattern.
4. **Revert the exact issue commit:** Use the commit id recorded in `Index.md` for that issue.
5. **Update the issue file:** Record what failed in the prior attempt, what review found, and what extra context the next executor must receive.
6. **Re-Dispatch:** Send the task back to a new executor with the new, stricter context.

If a fix is correct but the phase is not finished yet:
1. Keep the commit.
2. Keep the issue file.
3. Keep the `Index.md` entry in the form `{closed with commit id <sha>}`.
4. Do not clear tracking artifacts until phase completion.

## 🏗️ Phase Completion Sign-off
A Phase is only complete when:
1. Every issue in the phase has been reviewed against its recorded closing commit.
2. The `Index.md` section for that Phase is 100% checked or explicitly marked with `{closed with commit id <sha>}` awaiting final cleanup.
3. The `Context Audit Report` for the Phase is updated.
4. All `tests/architecture/` are green.
5. (For Phase 1+) The Universal CLI can successfully execute a discovery mission.
6. Only then may the supervisor delete resolved issue files and remove their Index entries.

## Phase-Closing Ritual
When a phase is ready to close, the supervisor must execute this ritual in order:
1. Freeze the phase boundary: confirm no new issue is being added to the phase while sign-off is running.
2. Review every issue entry in `plan_docs/issues/Index.md` for that phase.
3. Inspect every `{closed with commit id <sha>}` commit and accept or reject it explicitly.
4. Revert every rejected closing commit individually and update the corresponding issue file with review findings.
5. Confirm every accepted issue still has its issue file and its `{closed with commit id <sha>}` entry.
6. Run the architecture and validation gates for the whole phase.
7. Update the phase-level context/reporting artifacts.
8. Only after all checks pass, delete resolved issue files and remove their Index entries.
9. Mark the phase as completed in the Index and any required reports.
