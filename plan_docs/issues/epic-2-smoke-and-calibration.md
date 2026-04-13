# Epic 2: Prueba de Humo y Calibración End-to-End

**Umbrella:** depends on `ariadne-oop-skeleton.md` and `interpreter-node.md`.

### 1. Explanation
 Validate that the assembled OOP graph (`Theseus` → `Delphi` → HITL, wrapped in `async with adapter:`) survives real browser conditions — not mocked state. Two tests: one that forces the full cascade to fail down to HITL, and one that completes a real discovery mission on StepStone.

### 2. Reference
`plan_docs/design/design_spec.md`

### 3. Real fix
 HIGH — validates that the skeleton actually works end to end.

### 4. Steps

- [ ] **Task 2.1 — The Corneta Test** (smoke test, forces full cascade)
- [ ] **Task 2.2 — The Fire Test** (real StepStone discovery run)
- [ ] `404-danger-signal.md` — HTTP error pages short-circuit to HITL from `Theseus.__call__`
- [ ] `zero-shot-error-typing.md` — `MapNotFoundError` + `"explore"` fallback so unknown portals degrade cleanly

Single-browser enforcement is no longer a sub-issue: `BrowserAdapter.__aenter__` owns the lifecycle per `ariadne-oop-skeleton.md`, and the Corneta test's fitness assertion (browser opens/closes exactly once) validates it.

### 📦 Required Context Pills
- [Async Test Pattern (LangGraph)](../context/async-test-pattern.md)
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Law 2 - One Browser Per Mission](../context/law-2-single-browser.md)
- [Law 4 - Finite Routing](../context/law-4-finite-routing.md)
- [Smoke Test Pattern (Corneta)](../context/smoke-test-pattern.md)

### 🚫 Non-Negotiable Constraints
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
- **Law 2 (One Browser Per Mission):** A single `async with executor` block must wrap the entire graph execution. Nodes must never open or close the browser themselves.
- **Law 4 (Finite Routing):** All loops must have finite circuit breakers. Escalation through counters (heuristic_retries >= 2, agent_failures >= 3) to HITL is mandatory.
