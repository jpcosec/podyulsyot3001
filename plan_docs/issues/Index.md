# unified-automation Issues Index

This file is the entrypoint for subagents deployed to solve issues in this repository.

All issue-fixing work must stay aligned with the rest of plan_docs/ and docs/, with special care for STANDARDS.md so implementation, tests, and documentation remain consistent with the project's rules.

## Initialization Procedure (Before Execution)

Before executing any issue or assigning work to a subagent, you MUST perform this ritual:
  1. Atomize: break down work into the smallest possible units.
  2. See what's redundant > merge.
  3. Legacy > delete.
  4. Contradictory > resolve.
  5. Iterate until the plan is clean and straightforward.
  6. Update `plan_docs/issues/Index.md`.
  7. Execute using the smallest possible/available subagent for each step. Provide the subagent with explicit context (e.g., architectural boundaries, limits, or relevant reference files) to prevent them from making wrong choices. Review their work.

## Working rule for every issue

Once an issue is solved, the next step is always:

  1. Check whether any existing test is no longer valid and delete it if needed.
  2. Add new tests where necessary.
  3. Run the relevant tests.
  4. Update changelog.md.
  5. Delete the solved issue from both this index and the corresponding file in plan_docs/issues/.
  6. Make a commit that clearly states what was fixed, making sure all required files are staged.

## Phase Completion Ritual

When all parallelizable issues in a given Phase/Level are completed, you MUST perform a compliance check before moving to the next Phase:
  1. Verify compliance: Check that the combined implementations of the phase comply with all project standards and architectural boundaries.
  2. Run all architectural fitness functions and full test suites to ensure no regressions were introduced.

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

### Phase 0 — Epic 0: Fitness Tests (prerequisite for everything)
Run in parallel. These must be green before any Phase 1 work is merged.
- [ ] **`epic-0-fitness-tests.md`** ← read this first
  - [ ] `fix-test-domain-isolation.md` — delete dummy classes from lines 31–130
  - [ ] `fix-test-single-browser.md` — run real graph, not just `take_snapshot()`
  - [ ] `fix-test-sync-io-detector.md` — run real graph, not just `take_snapshot()`
  - [ ] `fix-test-graph-depth.md` — create from scratch, invalid API key, no mock LLM

**Note:** `gaps/fitness-*.md` are superseded by the above. Delete them when Epic 0 closes.

### Phase 1 — Epic 1: CLI + Interpreter
- [ ] **`epic-1-cli-and-interpreter.md`** ← read this first
  - [ ] `interpreter-node.md`
  - [ ] `agent-context-aware.md`
  - [ ] `cli-rewrite.md`
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
  - [ ] `set-of-mark-observe.md`
  - [ ] `hint-failure-fallback.md`

### Phase 4 — Epic 4: Map Factory
- [ ] **`epic-4-map-factory.md`** ← read this first
  - [ ] `recording-promoter-guard.md`
  - [ ] Live recording session (XING or LinkedIn)
  - [ ] Promotion + canonical map validation

### Docs (anytime)
- [ ] `map-concept-docs.md`

## Parallelization map

**Phase 0:** All three fitness tests are independent.
**Phase 1:** `interpreter-node` → `agent-context-aware` (sequential). `cli-rewrite` is independent but integrates after interpreter node lands.
**Phase 2:** Corneta test and Fire test are sequential (Corneta first). Robustness issues (`404`, `single-browser`, `zero-shot`) are parallel to each other and to Epic 2.
**Phase 3:** `set-of-mark-observe` before `hint-failure-fallback`. No other dependencies.
**Phase 4:** `recording-promoter-guard` before Tasks 4.1 and 4.2. Docs are independent of everything.