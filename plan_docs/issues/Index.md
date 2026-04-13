# unified-automation Issues Index

This file is the entrypoint for executors deployed to solve issues in this repository.

All issue-fixing work must stay aligned with the rest of plan_docs/ and docs/, with special care for STANDARDS.md so implementation, tests, and documentation remain consistent with the project's rules.

Role-specific instructions:
- Executors must follow `plan_docs/executor-instructions.md`.
- Context compilers must follow `plan_docs/context_compiler-instructions.md`.
- Supervisors must follow `plan_docs/supervisor-instructions.md`.

## Initialization Procedure (Before Execution)

Before executing any issue or assigning work to an executor, you MUST perform this ritual:
  1. Atomize: break down work into the smallest possible units.
  2. See what's redundant > merge.
  3. Legacy > delete.
  4. Contradictory > resolve.
  5. Iterate until the plan is clean and straightforward.
  6. Dispatch one `context_compiler` per executable issue to validate the issue package, linked pills, dependencies, and zero-context sufficiency before implementation starts.
  7. Update `plan_docs/issues/Index.md`.
  8. Execute using the smallest possible/available executor for each step. Provide the executor with explicit context (e.g., architectural boundaries, limits, or relevant reference files) to prevent them from making wrong choices. Review their work.
  9. If the assigned executor still reports unclear issue scope or insufficient context, dispatch a new `context_compiler` before allowing implementation work to continue.

## Working rule for every issue

When an executor finishes an issue, the next step is always:

  1. Check whether any existing test is no longer valid and delete it if needed.
  2. Add new tests where necessary.
  3. Run the relevant tests.
  4. Update changelog.md.
  5. Make exactly one commit for that closed issue, with the issue id in the commit message.
  6. After that commit, overwrite the issue entry in this file with the status form `{closed with commit id <sha>}`.
  7. Do not delete the issue file and do not remove the entry from this index. That is supervisor-only cleanup after the full phase is accepted.
  8. The Index bookkeeping may remain uncommitted until the phase-closing ritual.

## Supervisor-only cleanup rule

The supervisor is the only actor allowed to delete a resolved issue file or remove its entry from this index.

- If the closing commit is accepted, keep the issue file and keep the `{closed with commit id <sha>}` entry until the entire phase is complete.
- If the closing commit is rejected, revert that exact commit, update the issue file with failure notes and missing context, and dispatch a new executor.
- Once the whole phase is complete, the supervisor deletes the resolved issue files and removes their entries from this index.

## Entry state contract

Each executable issue listed in this index must be in exactly one of these states:
- open
- `{closed with commit id <sha>}`

No issue may disappear from the index before the supervisor finishes phase-level validation.

## Phase Completion Ritual

When all parallelizable issues in a given Phase/Level are completed, you MUST perform a compliance check before moving to the next Phase:
  1. Verify compliance: Check that the combined implementations of the phase comply with all project standards and architectural boundaries.
  2. Run all architectural fitness functions and full test suites to ensure no regressions were introduced.
  3. Review every `{closed with commit id <sha>}` entry before clearing any issue file or removing any index entry.
  4. Delete resolved issue files and clear their index entries only after the whole phase is accepted.

The authoritative phase-closing checklist lives in `plan_docs/supervisor-instructions.md` under `## Phase-Closing Ritual`.

## Priority convention

**Epic issues have the highest priority.** When a sub-issue conflicts with or is ambiguous relative to its parent epic, the epic's stated objective wins. Sub-issues exist to atomize work — they do not override the epic's intent.

Epic issues are identified by the `epic-` prefix. Each epic ends with a real-browser validation step that must pass before the epic is considered closed.

### ⚠️ Risk Mitigation Guardrails (Read First)

Before starting any work, verify these "Laws of Physics" are not violated:
1. **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
2. **Law 2 (One Browser Per Mission):** The graph must share a single browser context. No `Executor.__aenter__` inside the loop.
3. **Law 3 (DOM Hostility):** All JS injection must use an isolated overlay. Do not mutate existing DOM nodes or event listeners.
4. **Law 4 (Finite Routing):** All loops must have finite circuit breakers. Escalation to LLM rescue (2 retries) or HITL (3 agent failures) is mandatory.
5. **DIP Enforcement:** Domain layers (`ariadne`) MUST NOT import from infrastructure layers (`motors`).

### Priority roadmap

### Phase 0 — Completed
- [x] Fitness Tests closed on 2026-04-13. `python -m pytest tests/architecture/ -v` is green, and the superseded `gaps/fitness-*.md` files were removed.
- [x] Posthumous issue `fix-ariadne-io-refactor.md` was closed in `cc29691`, extending the Phase 0 sync-I/O cleanup across Ariadne recording, promotion, repository access, and shared JSON/JSONL helpers before final phase closure.

### Phase 1 — Epic 1: CLI + Interpreter
- [ ] **`epic-1-cli-and-interpreter.md`** ← read this first
  - [ ] `interpreter-node.md`
  - [ ] `agent-context-aware.md`
  - [ ] `cli-engine-implementation.md`
  - [ ] `cli-dead-code-cleanup.md`
  - [ ] test cleanup (inline in epic)

### Phase 2 — Epic 2: Smoke & Calibration
Validates Epic 1 on real data. Cannot start until Epic 1 validation passes.
- [ ] **`epic-2-smoke-and-calibration.md`** ← read this first
  - [ ] Corneta test (integration test, forces full cascade)
  - [ ] Fire test (live StepStone discovery run)

Parallel robustness work (can land alongside Epic 2):
- [ ] `404-danger-signal.md`
- [ ] `single-browser-universal.md`
- [ ] `zero-shot-error-typing.md`

### Phase 3 — Epic 3: Agent Hints
- [ ] **`epic-3-agent-hints.md`** ← read this first
  - [ ] `som-hint-injection.md`
  - [ ] `som-agent-prompt-update.md`
  - [ ] `hint-failure-fallback.md`

### Phase 4 — Epic 4: Map Factory
- [ ] **`epic-4-map-factory.md`** ← read this first
  - [ ] `recording-promoter-guard.md`
  - [ ] Live recording session (XING or LinkedIn)
  - [ ] Promotion + canonical map validation

### Docs (anytime)
- [ ] `map-concept-docs.md`

## Parallelization map

**Phase 0:** All four fitness tests are independent.
**Phase 1:** `interpreter-node` → `agent-context-aware` (sequential). `cli-engine-implementation` → `cli-dead-code-cleanup` (sequential).
**Phase 2:** Corneta test and Fire test are sequential (Corneta first). Robustness issues (`404`, `single-browser`, `zero-shot`) are parallel to each other and to Epic 2.
**Phase 3:** `som-hint-injection` → `som-agent-prompt-update` (sequential) → `hint-failure-fallback`.
**Phase 4:** `recording-promoter-guard` before Tasks 4.1 and 4.2. Docs are independent of everything.
