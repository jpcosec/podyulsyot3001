# Epic 2: Prueba de Humo y Calibración End-to-End

**Objective:** Validate that the assembled graph survives real browser conditions — not mocked state. Two tests: one that forces the full cascade to fail down to HITL, and one that completes a real discovery mission on StepStone.

**Priority:** HIGH — validates that Epic 1 actually works. No real confidence in the system until this passes.

**Contains:**
- [ ] **Task 2.1 — The Corneta Test** (smoke test, forces full cascade)
- [ ] **Task 2.2 — The Fire Test** (real StepStone discovery run)
- [ ] `404-danger-signal.md` — HTTP error pages must short-circuit to HITL without burning the cascade
- [ ] `single-browser-universal.md` — verify correct `async with` nesting in the new CLI's `run_ariadne()`
- [ ] `zero-shot-error-typing.md` — `MapNotFoundError` + `"explore"` fallback so unknown portals degrade cleanly

### 📦 Required Context Pills
- [Smoke Test Pattern (Corneta)](../context/smoke-test-pattern.md)
- [Async Test Pattern (LangGraph)](../context/async-test-pattern.md)

### 🚫 Infrastructure & Circuit Breaker Guardrails
- **Law 4 (Finite Routing):** The "Corneta Test" MUST verify that the graph escalates to HITL after 3 agent failures.
- **Law 1 (No Blocking I/O):** All integration tests MUST be `async`.

**Task 2.1: The Corneta Test**
Create `tests/integration/test_cascade_smoke.py`.

Run the graph with a `fitness_test` portal whose map targets non-existent elements. All four cascade levels should fail in sequence, and the graph must land at `human_in_the_loop` cleanly — no infinite loops, no unhandled exceptions.

```python
# Pseudo-structure
initial_state = {
    "instruction": "easy_apply",
    "portal_name": "fitness_test",
    "current_url": "https://example.com",
    ...
}
# Assert: graph terminates at human_in_the_loop within 15 steps
# Assert: no Python exception raised
# Assert: errors list is non-empty (proves cascade was exercised)
```

Requires: `GOOGLE_API_KEY` set in `.env` (LLM node will be invoked for real).

**Task 2.2: The Fire Test**
Manual run — not automated in CI. Execute the StepStone `search.json` map via Crawl4AI against the live site:

```bash
python -m src.automation.main "busca 5 trabajos de Python en Berlin" \
  --portal stepstone --motor crawl4ai limit=5
```

**Acceptance criteria:**
1. Corneta test: graph reaches `human_in_the_loop` without exception. Step count ≤ 15.
2. Fire test: `session_memory` in final state contains at least 3 job entries with `title` and `url` fields.
3. Fire test: LangGraph finalizes at `discovery_complete` success state (no HITL triggered by the cascade).
4. No `ObservationError` or `MapLoadError` in final state `errors` list.
5. Navigating to a 404 URL routes directly to HITL — `execute_deterministic` is never called.
6. The new CLI's executor is always wrapped in `async with` — browser opens once, closes once.
7. Running against an unmapped portal sets `current_mission_id = "explore"` and does not raise an unhandled exception.
