# Epic 0: Fitness Tests (Architecture Gate)

**Objective:** Establish the three architectural invariants as passing tests before any feature work lands. These are the laws of physics for the system — if any of them is red, no Phase 1 work merges.

**Priority:** HIGHEST — hard gate for all other epics. Resolve any conflict with sub-issues in favor of this epic's objective.

**Contains:**
- [ ] `fix-test-domain-isolation.md` — delete dummy `AriadneNode`/`NormalizationEngine` classes (lines 31–130); keep only the two `archrule` tests
- [ ] `fix-test-single-browser.md` — replace `take_snapshot()` with real `app.astream()` so the orchestrator's session management is actually tested
- [ ] `fix-test-sync-io-detector.md` — same: replace `take_snapshot()` with real `app.astream()` so node-level sync I/O is detected
- [ ] `fix-test-graph-depth.md` — create `test_graph_depth.py` from scratch; use invalid API key via `monkeypatch`, no mock LLM node

### 🚫 Non-Negotiable Constraints (Laws of Physics)

1. **Law 1 (No Blocking I/O):** All tests must verify that no synchronous I/O occurs during graph execution. If `test_sync_io_detector.py` is red, no other work is valid.
2. **Law 2 (One Browser Session):** Tests must assert that the browser is NOT opened or closed within the graph nodes.
3. **Law 4 (Finite Routing):** `test_graph_depth.py` must use a real invalid API key to trigger a real failure and verify the circuit breaker escalates to HITL.
4. **DIP Enforcement:** `test_domain_isolation.py` must enforce that `ariadne/` does not import from `motors/`.

**Supersedes:** `gaps/fitness-sync-io.md`, `gaps/fitness-single-browser.md`, `gaps/fitness-graph-depth.md` — those described the right intent with the wrong approach. Delete them once this epic closes.

**Execution order:** All four are independent — run in parallel.

**Key constraint:** All three tests require `GOOGLE_API_KEY` (set in `.env`) to invoke the real LLM node. Do not mock the LLM — that defeats the purpose of these tests.

**Validation:**
All three must pass green with no mocks on the cascade path:

```bash
python -m pytest tests/architecture/ -q
```

Expected output: 3 passed, 0 warnings.

**Acceptance criteria:**
1. `test_sync_io_detector.py` — no sync I/O detected during node execution (boot-time I/O is allowed).
2. `test_single_browser.py` — `__aenter__` call count == 1 across a multi-step graph run.
3. `test_domain_isolation.py` — no circular imports between `ariadne/` and `motors/`.
4. `test_graph_depth.py` (or equivalent) — step count ≤ 10 when executor always fails, circuit breaker triggers, HITL reached.
5. Zero mocks on the LLM or executor in these tests — real cascade only.
