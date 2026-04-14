# 📜 Unified Project Standards

This document is the single source of truth for coding, documentation, and workflow standards. **Agents and human developers must read and adhere to these protocols.**

---

## 1. The Issue & Design Cycle (Workflow)

Every change must be managed through the `plan_docs/tasks/Index.md` execution queue.

### Stage 1: Mapping
Produce one `.md` file per concern directly under `plan_docs/tasks/`. The prior `gaps/` vs `unimplemented/` split is retired — there is one flat issue pool.
Each issue file MUST follow this format:
- **Explanation:** What is wrong/missing.
- **Reference:** Files where the issue lives.
- **What to fix:** The concrete end state.
- **How to do it:** Suggested implementation path.
- **Depends on:** Explicit dependencies.

### Stage 2: Initialization Procedure (Before Execution)
Before assigning work to an executor, the orchestrator MUST perform this ritual:
0. **Pill Audit - Phase A**: Run `plan_docs/context-pill-audit.md` Phase A. Delete stale pills, create missing mandatory pills, resolve contradictions.
   - **The Lifecycle Rule**: Contradictions between code and Pills result in either a Gap Issue (if `lifecycle: target`) or Pill Regeneration (if `lifecycle: current`).
1. **Atomize**: Break down work into the smallest possible child issues.
2. **Context Injection**: Route relevant "Context Pills" from `plan_docs/context/` into the issue `.md` file.
3. **Redundant > Merge**: Merge overlapping issues to ensure unambiguous ownership.
4. **Legacy > Delete**: Review issues for dead content. Delete and record as an ADR in `docs/adrs/` if necessary.
5. **Context Compiler Pass**: For each executable issue, dispatch a `context_compiler` to review the issue package.
6. **Pill Audit - Phase B**: Run `plan_docs/context-pill-audit.md` Phase B. Verify every issue has the correct pills, no broken links, and zero-context sufficiency. Must reach `READY FOR EXECUTION: YES` before continuing.
7. **Update Index.md**: Regenerate the dependency graph and parallelization map.
8. **Execute**: Provide the executor with the specific issue file and verify they have access to the linked context pills.

### Stage 3: Role Instructions
Role-specific execution rules live in these documents and are mandatory:
- `plan_docs/executor-instructions.md`
- `plan_docs/context_compiler-instructions.md`
- `plan_docs/supervisor-instructions.md`

### Stage 3.1: Traceability Contract
Every closed issue must remain traceable through all three artifacts until the supervisor clears it:
- the issue file in `plan_docs/tasks/`
- the matching entry in `plan_docs/tasks/Index.md`
- the git commit that resolved it

There must be a one-to-one mapping between a closed issue and its resolving commit. Do not batch multiple closed issues into one commit.

### QA & Validation Issues
- **Validation-Type Issues:** If a validation fails, do not close silently. Atomize every uncovered real problem into new gap issues before closing the validation issue.

---

## 2. Code Architecture & Style

### Function size
- **Hard limit: 10 lines.** A function that exceeds 10 lines has more than one purpose. Split it.
- Each helper must do exactly one thing and be named after that one thing.
- If a function needs more than ~3 local variables it is likely a class in disguise — make it one.

### Class size and decomposition
- **Hard limit: 80 lines per class.** A class that exceeds 80 lines owns more than one concept. Split it.
- Prefer **primitive classes + inheritance** over large monoliths. Extract the primitive behavior first, then subclass for specialization.
- One class per file when the class is longer than 10 lines.

### Self-documenting code
- Code is the primary documentation. Names must make intent obvious without comments.
- Comments are only permitted where the *why* cannot be expressed in code (e.g. non-obvious algorithmic choice or external constraint).
- Module-level docstrings must exist at the top of every file and state the single responsibility of the module.

### Layer Separation & SOLID Principles
Every module is self-contained. The rule: **no file does two things.**
- **Dependency Inversion (DIP)**: Domain layers (`ariadne`) must NEVER import from infrastructure layers (`adapters`). Infrastructure must be injected via constructor.
- **Operational Limits**: Expose operational limits (retry budgets, circuit breaker thresholds) as named constants at module top — never buried in loops.

### Non-implemented work
- **No stub implementations, mocks, or scaffolding outside of `tests/`.** If something is not implemented, it must not exist in `src/` — not even as a placeholder class or `pass` body.
- Every piece of unimplemented work must be explicitly recorded as an issue file in `plan_docs/tasks/` before the task is committed.
- The only valid exceptions are `NotImplementedError` raised inside abstract methods that are genuinely part of an ABC contract.

### Error Contracts
- Define domain-specific exceptions at the top of the file (e.g., `TranslationError`, `TargetNotFound`).
- **Never use bare `Exception` for flow control.**
- Never swallow errors silently. Catch, log with `[⚠️]`, and re-raise with `from e`.

### Observability & Log Tags
Import `LogTag` from `src/shared/log_tags.py` (if available) or use standardized prefixes:
- `[🧠]` LLM reasoning (Non-deterministic).
- `[⚡]` Fast / deterministic path.
- `[🤖]` Fallback mechanism active.
- `[✅]` Success / validation passed.
- `[⚠️]` Expected / handled error.
- `[❌]` Hard failure — pipeline breaks.
- `[📍]` State Pointer (e.g. `[📍] Current state: job_search`)

---

## 3. Documentation & Schemas

### README as navigation index
- `README.md` files are **navigation indexes**, not comprehensive documentation. They point to the authoritative source, they do not duplicate it.
- Root `README.md` points to module READMEs and key docs.
- Module READMEs point to the relevant source files and design docs.
- `__init__.py` files serve the same indexing role at the package level: export the public surface and nothing else. A reader opening `__init__.py` should immediately understand what the package provides.

### Test Structure Mirror
Tests mirror `src/automation/` directly under `tests/` (no `unit/` prefix):

```
tests/
├── ariadne/
│   ├── labyrinth/      # mirrors src/automation/ariadne/labyrinth/
│   └── thread/         # mirrors src/automation/ariadne/thread/
└── langgraph/
    └── nodes/          # mirrors src/automation/langgraph/nodes/
```

Run the full suite with:
```bash
python -m pytest tests/ariadne tests/langgraph --asyncio-mode=auto -v
```

All async tests use `@pytest.mark.asyncio`. The `conftest.py` at the root of `tests/` sets `pytest_plugins = ["pytest_asyncio"]`.

### Ephemeral Planning
Active plans live in `plan_docs/`. Once a feature is built, tested, and documented, the planning document MUST be deleted. `plan_docs/` is a scratchpad, not a history.

---

## 4. Git Hygiene
- **Never edit files while the git tree is dirty.** First make a snapshot commit, then edit on top of a clean state.
- Do not ask the user for permission to commit if the workflow dictates it. Just do it.
- Executors must create the resolving commit for their assigned issue before handing work back to the supervisor.

---

## 5. Architectural Invariants (Laws of Physics)

1. **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
2. **Law 2 (One Browser Per Mission):** The graph must share a single browser context. No `Executor.__aenter__` inside the loop.
3. **Law 3 (DOM Hostility):** All JS injection must use an isolated overlay. Do not mutate existing DOM nodes or event listeners.
4. **Law 4 (Finite Routing):** All loops must have finite circuit breakers. Escalation to LLM rescue (2 retries) or HITL (3 agent failures) is mandatory.
