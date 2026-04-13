# 📜 Unified Project Standards

This document is the single source of truth for coding, documentation, and workflow standards. **Agents and human developers must read and adhere to these protocols.**

---

## 1. The Issue & Design Cycle (Workflow)

Every change must be managed through the `plan_docs/issues/Index.md` execution queue.

### Stage 1: Mapping
Produce one `.md` file per concern directly under `plan_docs/issues/`. The prior `gaps/` vs `unimplemented/` split is retired — there is one flat issue pool.
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
- the issue file in `plan_docs/issues/`
- the matching entry in `plan_docs/issues/Index.md`
- the git commit that resolved it

There must be a one-to-one mapping between a closed issue and its resolving commit. Do not batch multiple closed issues into one commit.

### QA & Validation Issues
- **Validation-Type Issues:** If a validation fails, do not close silently. Atomize every uncovered real problem into new gap issues before closing the validation issue.

---

## 2. Code Architecture & Style

### Layer Separation & SOLID Principles
Every module is self-contained. The rule: **no file does two things.**
- `models.py` or `contracts.py`: Owns all Pydantic schemas.
- `storage.py` or `repository.py`: Owns all file I/O and persistence. No business logic.
- `main.py`: CLI entry point only.
- **Dependency Inversion (DIP)**: Domain layers (`ariadne`) must NEVER import from infrastructure layers (`motors`). Infrastructure must be injected or resolved via dynamic registries.
- **Docstring Rigor**: Module-level docstrings must exist at the top of every file. ABCs must list all abstract methods in their class docstring as a developer contract.
- **Operational Limits**: Expose operational limits (chunk sizes, retry budgets, rate limits) as `@property` on ABCs — not buried in loops or config dicts.

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

### Test Structure Mirror
Tests MUST mirror the `src/` structure. For every `src/package/module.py` that needs a test, create `tests/unit/package/module.py`.

### README Structure
Every module must have a `README.md` containing these sections:
1. `## 🏗️ Architecture & Features`
2. `## ⚙️ Configuration`
3. `## 🚀 CLI / Usage`
4. `## 📝 Data Contract`

### Ephemeral Planning
Active plans live in `plan_docs/`. Once a feature is built, tested, and documented in the module README, the planning document MUST be deleted.

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
