# 📜 Unified Project Standards

This document is the single source of truth for coding, documentation, and workflow standards. **Agents and human developers must read and adhere to these protocols.**

---

## 1. The Issue & Design Cycle (Workflow)

Every change must be managed through the `plan_docs/issues/Index.md` execution queue.

### Stage 1: Mapping
Produce one `.md` file per concern under `plan_docs/issues/gaps/` or `plan_docs/issues/unimplemented/`.
Each issue file MUST follow this format:
- **Explanation:** What is wrong/missing.
- **Reference:** Files where the issue lives.
- **What to fix:** The concrete end state.
- **How to do it:** Suggested implementation path.
- **Depends on:** Explicit dependencies.

### Stage 2: Initialization Procedure (Before Execution)
Before assigning work to a subagent, the orchestrator MUST perform this ritual:
1. **Atomize**: Break down work into the smallest possible child issues.
2. **Redundant > Merge**: Merge overlapping issues to ensure unambiguous ownership.
3. **Legacy > Delete**: Review issues for dead content. Delete and record as an ADR in `docs/adrs/` if necessary.
4. **Contradictory > Resolve**: Resolve incompatible end states.
5. **Update Index.md**: Regenerate the dependency graph and parallelization map.
6. **Execute**: Provide the subagent with explicit context (e.g., architectural boundaries) to prevent wrong choices.

### Stage 3: Lifecycle (Execution Ritual)
Once an issue is solved, the subagent MUST follow these steps:
1. Check if existing tests are invalid and delete/update them.
2. Add and run new tests to verify the fix.
3. **Verify compliance**: Check that the implementation strictly complies with all standards in this document (e.g., no DIP violations, correct log tags).
4. Update `changelog.md`.
5. Delete the solved issue from `plan_docs/issues/` and remove it from `Index.md`.
6. Make a commit stating exactly what was fixed.

### Phase Completion (Level-up Ritual)
When all parallelizable issues in a given Phase/Level are completed:
- Run all architectural fitness functions (`pytest-archon`, `pyfakefs`) and full test suites to ensure no regressions were introduced before moving to the next Phase.

---

## 2. Code Architecture & Style

### Layer Separation & SOLID Principles
Every module is self-contained. The rule: **no file does two things.**
- `models.py` or `contracts.py`: Owns all Pydantic schemas.
- `storage.py` or `repository.py`: Owns all file I/O and persistence. No business logic.
- `main.py`: CLI entry point only. Delegates to the orchestrator.
- **Dependency Inversion (DIP)**: Domain layers (`ariadne`) must NEVER import from infrastructure layers (`motors`). Infrastructure must be injected or resolved via dynamic registries.

### Error Contracts
- Define domain-specific exceptions at the top of the file (e.g., `TranslationError`, `TargetNotFound`).
- **Never use bare `Exception` for flow control.**
- Never swallow errors silently. Catch, log with `[⚠️]`, and re-raise with `from e`.

### Observability & Log Tags
Logs are real-time execution documentation. Import `LogTag` from `src/shared/log_tags.py` (if available) or use the standardized string prefixes. **Do not invent emojis.**
- `[🧠]` LLM reasoning (Non-deterministic).
- `[⚡]` Fast / deterministic path.
- `[🤖]` Fallback mechanism active.
- `[✅]` Success / validation passed.
- `[⚠️]` Expected / handled error.
- `[❌]` Hard failure — pipeline breaks.

---

## 3. Documentation & Schemas

### Pydantic Field Descriptions
`Field(description=...)` is consumed by LLMs for structured outputs.
- Write semantic, specific descriptions with examples.
- Mark MANDATORY vs OPTIONAL fields clearly.

### README Structure
Every module must have a `README.md` containing these sections:
1. `## 🏗️ Architecture & Features`: Describe shape and link to authoritative files (do not duplicate code).
2. `## ⚙️ Configuration`: Env vars and setup.
3. `## 🚀 CLI / Usage`: Intent and entry points.
4. `## 📝 Data Contract`: Point to the Pydantic model file.

### Ephemeral Planning
Active plans live in `plan_docs/`. Once a feature is built, tested, and documented in the module README, the planning document MUST be deleted. There is no archive folder.

---

## 4. Git Hygiene
- **Never edit files while the git tree is dirty.** First make a snapshot commit, then edit on top of a clean state.
- Do not ask the user for permission to commit if the workflow dictates it. Just do it.
