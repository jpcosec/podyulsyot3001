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
Before assigning work to an executor, the orchestrator MUST perform this ritual:
0. **Pill Audit - Phase A**: Run `plan_docs/context-pill-audit.md` Phase A. Delete stale pills, create missing mandatory pills, resolve contradictions. Do this before touching any issue.
1. **Atomize**: Break down work into the smallest possible child issues.
2. **Context Injection**: Route relevant "Context Pills" from `plan_docs/context/` into the issue `.md` file.
3. **Redundant > Merge**: Merge overlapping issues to ensure unambiguous ownership.
4. **Legacy > Delete**: Review issues for dead content. Delete and record as an ADR in `docs/adrs/` if necessary.
5. **Pill Audit - Phase B**: Run `plan_docs/context-pill-audit.md` Phase B. Verify every issue has the correct pills, no broken links, and zero-context sufficiency. Must reach `READY FOR EXECUTION: YES` before continuing.
6. **Update Index.md**: Regenerate the dependency graph and parallelization map.
7. **Execute**: Provide the executor with the specific issue file and verify they have access to the linked context pills.

### Stage 3: Role Instructions
Role-specific execution rules live in these documents and are mandatory:
- `plan_docs/executor-instructions.md`
- `plan_docs/supervisor-instructions.md`

### Stage 3.1: Traceability Contract
Every closed issue must remain traceable through all three artifacts until the supervisor clears it:
- the issue file in `plan_docs/issues/`
- the matching entry in `plan_docs/issues/Index.md`
- the git commit that resolved it

There must be a one-to-one mapping between a closed issue and its resolving commit. Do not batch multiple closed issues into one commit, and do not close one issue across multiple commits unless the supervisor explicitly re-opens it after review.

### QA & Validation Issues
- **Validation-Type Issues:** If a validation fails, do not close silently. Atomize every uncovered real problem into new gap issues before closing the validation issue.

### Phase Completion (Level-up Ritual)
When all parallelizable issues in a given Phase/Level are completed:
- Verify every issue in the phase is either still open or marked `{closed with commit id <sha>}` in `plan_docs/issues/Index.md`.
- Review and accept or reject each closing commit before phase sign-off.
- Only after the phase is accepted, delete the resolved issue files and clear their corresponding Index entries.
- Run all architectural fitness functions (`pytest-archon`, `pyfakefs`) and full test suites to ensure no regressions were introduced before moving to the next Phase.

---

## 2. Code Architecture & Style

### Layer Separation & SOLID Principles
Every module is self-contained. The rule: **no file does two things.**
- `models.py` or `contracts.py`: Owns all Pydantic schemas.
- `storage.py` or `repository.py`: Owns all file I/O and persistence. No business logic.
- `main.py`: CLI entry point only. Delegates to the orchestrator. Must accept an optional `argv: list[str] | None = None` parameter for testing, and must return an integer exit code. CLI arguments must be defined in a `_build_parser()` function. READMEs should never duplicate argument tables, but rather point to this function.
- **Dependency Inversion (DIP)**: Domain layers (`ariadne`) must NEVER import from infrastructure layers (`motors`). Infrastructure must be injected or resolved via dynamic registries.
- **Docstring Rigor**: Module-level docstrings must exist at the top of every file. ABCs must list all abstract methods in their class docstring as a developer contract.
- **Operational Limits**: Expose operational limits (chunk sizes, retry budgets, rate limits) as `@property` on ABCs — not buried in loops or config dicts.

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
- `[⏭️]` `LogTag.SKIP` (idempotency).
- `[📦]` `LogTag.CACHE` (loaded existing artifact).

---

## 3. Documentation & Schemas

### Test Structure Mirror
Tests MUST mirror the `src/` structure. For every `src/package/module.py` that needs a test, create `tests/unit/package/module.py`:

```
src/automation/motors/browseros/executor.py
→ tests/unit/automation/motors/test_browseros_executor.py

src/automation/ariadne/modes/default.py
→ tests/unit/automation/ariadne/test_modes.py
```

This ensures test discoverability and prevents orphaned tests.

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

### Documentation Philosophy
- **Core Principle**: Clean, well-structured code beats documentation. Documentation that duplicates code always drifts; documentation that points to code stays honest.
- **Inline TODOs**: Use small inline TODOs only when they are tightly local to the code. For anything larger, add the follow-up to the relevant `plan_docs` file.

---

## 4. Git Hygiene
- **Never edit files while the git tree is dirty.** First make a snapshot commit, then edit on top of a clean state.
- Do not ask the user for permission to commit if the workflow dictates it. Just do it.
- Executors must create the resolving commit for their assigned issue before handing work back to the supervisor.
- Supervisors must revert failed issue commits individually; do not squash away traceability.

---

## 5. Architectural Invariants (Laws of Physics)

These are non-negotiable constraints on the Ariadne 2.0 runtime. **Any implementation that violates one of these invariants is wrong by definition, regardless of whether tests pass.** Every executor must check their work against these before closing an issue.

Each invariant is enforced by an automated fitness test in `tests/architecture/`. If a fitness test is red, no feature work merges.

---

### Law 1 — The Event Loop is Sacred (No Blocking I/O)

> No graph node, portal mode, or translator may block the main thread.

All disk reads (loading map JSON), network calls (LLM prompts, HTTP requests), and subprocess waits inside `src/automation/ariadne/` must use `async/await`. Synchronous calls (`open()`, `requests.get()`, `time.sleep()`) are forbidden in the hot loop — the window between the first `observe_node` call and mission completion.

**Why:** A single blocking call freezes the entire event loop, preventing parallel job processing and causing silent timeouts in LangGraph checkpoints.

**Enforced by:** `tests/architecture/test_sync_io_detector.py` — patches `builtins.open` during node execution and fails if called synchronously.

**Allowed exception:** Boot-time I/O (before the first node fires) is permitted — e.g. Crawl4AI initializing its browser process.

---

### Law 2 — One Browser Per Mission (Session Singleton)

> The graph must operate on a single browser context from `observe_node` through mission completion. Opening or closing the browser mid-graph is architecturally prohibited.

`Executor.__aenter__` must be called exactly once per graph run, and `__aexit__` exactly once at the end. This is enforced by wrapping the entire graph execution in `async with executor`.

**Why:** SPA frameworks (React, Vue) store state in JavaScript memory. Destroying and recreating the browser context between `observe` and `execute` wipes cookies, open modals, and in-memory form state — breaking every multi-step portal flow.

**Enforced by:** `tests/architecture/test_single_browser.py` — spies on `AsyncWebCrawler.__aenter__` and asserts call count == 1 across a multi-step run.

**Implementation:** `async with executor as active_executor` wraps `create_ariadne_graph()` in `main.py`. See `cli-rewrite.md`.

---

### Law 3 — The DOM is Hostile (Non-Destructive Capabilities)

> Capabilities that inject code into portal pages (e.g. Link Hinting) must not mutate the original DOM tree.

All JS injection must attach to a dedicated overlay element anchored to `document.body`. Never use `appendChild` or `innerHTML` directly on page elements — this destroys event listeners and breaks SPA routing.

**Why:** Portal pages built on React/Vue bind event listeners to DOM nodes at render time. Mutating those nodes detaches the listeners, making subsequent `click` commands silently fail or trigger the wrong handler.

**Enforced by:** `tests/architecture/test_hostile_dom.py` — loads a "poisoned" HTML fixture (void elements, iframes, nested shadow roots) and asserts that `hinting.js` injects without throwing `DOMException`.

---

### Law 4 — Routing is Finite (Mandatory Circuit Breakers)

> The graph is forbidden from spinning in blind loops. Every cyclic fallback path must have a counter that escalates to the next intelligence level or terminates at HITL.

Counters live in `session_memory` and are checked by routing functions:
- `heuristic_retries >= MAX_HEURISTIC_RETRIES (2)` → escalate to `llm_rescue_agent`
- `agent_failures >= 3` → escalate to `human_in_the_loop`

No routing function may return to a previous node unconditionally.

**Why:** Without circuit breakers, a portal A/B test or a missing element causes infinite `observe → execute → heuristics → observe` loops, burning tokens and blocking the thread indefinitely.

**Enforced by:** `tests/architecture/test_graph_depth.py` — uses an executor that always fails and asserts the graph reaches `human_in_the_loop` within 10 steps.

---

*Fitness tests live in `tests/architecture/`. See `plan_docs/issues/epic-0-fitness-tests.md` for current status.*
