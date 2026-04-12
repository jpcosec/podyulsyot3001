# Fitness Function 4: Graph Depth Limit

**Explanation:** Protect against infinite loops - graph must reach HITL or success within X steps when executor always fails.

**Reference:** `tests/unit/automation/fitness/test_graph_depth.py`

**Status:** Test design is wrong - needs redesign.

**Why it fails:** Test tries to mock LLM - but LLM is part of cascade. Wrong approach.

**Real fix:** Test should use real flow:
1. Use `fitness_test` portal with targets that always fail
2. Let cascade run: Observe → Deterministic(FAIL) → Heuristics(FAIL) → LLM(FAIL) → repeat
3. Circuit breaker triggers at 3 LLM failures
4. Assert HITL reached within N steps

**Don't:** Mock LLM node - it breaks the test's purpose.

**Steps:**
1. Create `fitness_test` portal with 3 states that target non-existent elements
2. Real executor tries to click missing elements → fails
3. Real heuristics try → fail
4. Real LLM fails (no API key or returns error) → increment counter
5. After 3 failures → circuit breaker → HITL
6. Assert: step_count <= 10

**API Key:** Tests need GOOGLE_API_KEY or mock at integration level (env var)