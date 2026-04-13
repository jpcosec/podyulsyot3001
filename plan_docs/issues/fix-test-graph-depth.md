# Fix: test_graph_depth.py — Create From Scratch, No Mock LLM

**Explanation:** This file does not exist yet. The gaps issue (`gaps/fitness-graph-depth.md`) described the right intent but the wrong approach (mocking the LLM). This issue replaces it with a correct implementation.

**Reference:** `tests/architecture/test_graph_depth.py` (to be created), `gaps/fitness-graph-depth.md` (superseded by this issue)

**Status:** File does not exist.

**Why the gaps version was wrong:**
The original design used `mock_llm_node` to manually increment `agent_failures`. This defeats the purpose: if someone breaks the real agent's failure-handling logic, the mock still passes in green.

**Correct approach:**
Inject an invalid API key so the real LLM node fails with an auth error. LangGraph catches the exception, the routing function sees `errors` in state, increments `agent_failures`, and eventually routes to HITL. No mocks — the circuit breaker is tested end-to-end.

**Implementation:**

```python
"""Fitness Function 4: Graph Depth / Circuit Breaker.

Validates that the graph reaches human_in_the_loop within a bounded number
of steps when the full cascade fails — executor, heuristics, and LLM agent.
Uses a real invalid API key to make the LLM fail authentically.
"""

import pytest
from src.automation.ariadne.graph.orchestrator import create_ariadne_graph
from src.automation.motors.crawl4ai.executor import Crawl4AIExecutor

MAX_STEPS = 10

@pytest.mark.asyncio
async def test_circuit_breaker_halts_infinite_loops(monkeypatch):
    """Fitness: graph reaches HITL within MAX_STEPS when all cascade levels fail."""

    # Break the LLM authentically — real auth error, no mock
    monkeypatch.setenv("GOOGLE_API_KEY", "INVALID_KEY_FITNESS_TEST")

    initial_state = {
        "instruction": "easy_apply",
        "portal_name": "fitness_test",
        "job_id": "fitness-depth-test",
        "portal_mode": "fitness_test",
        "current_url": "https://example.com",
        "current_state_id": "start",
        "dom_elements": [],
        "screenshot_b64": None,
        "profile_data": {},
        "job_data": {},
        "session_memory": {},
        "errors": [],
        "history": [],
        "patched_components": {},
        "path_id": None,
        "current_mission_id": "easy_apply",
    }

    step_count = 0
    final_node = None

    executor = Crawl4AIExecutor()
    config = {
        "configurable": {
            "thread_id": "fitness-depth-test",
            "motor_name": "crawl4ai",
            "record_graph": False,
        }
    }

    async with executor as active_executor:
        config["configurable"]["executor"] = active_executor
        async with create_ariadne_graph(use_memory=False) as app:
            async for chunk in app.astream(initial_state, config, stream_mode="updates"):
                step_count += 1
                final_node = list(chunk.keys())[-1]
                assert step_count <= MAX_STEPS, (
                    f"Circuit breaker failed: graph exceeded {MAX_STEPS} steps "
                    f"without reaching HITL. Last node: {final_node}"
                )

    assert final_node == "human_in_the_loop", (
        f"Graph did not terminate at HITL. Final node: {final_node}"
    )
```

**Requires:**
- `fitness_test` portal map with states targeting non-existent elements (same map used by `test_single_browser.py` and `test_sync_io_detector.py`).
- No `GOOGLE_API_KEY` override needed in `.env` for this test — `monkeypatch.setenv` handles it per-test.

**Don't:**
- Mock `LangGraphBrowserOSAgent` or any node function.
- Catch the LLM auth exception inside the test — let the graph's error handling deal with it.

**Steps:**
1. Create `tests/architecture/test_graph_depth.py` with the implementation above.
2. Ensure a `fitness_test` portal map exists at `src/automation/portals/fitness_test/maps/easy_apply.json` with 1–2 states targeting `#element-that-does-not-exist`.
3. Run: `python -m pytest tests/architecture/test_graph_depth.py -v -s`
4. Confirm: `step_count <= 10` and `final_node == "human_in_the_loop"`.
5. Delete `gaps/fitness-graph-depth.md` — this issue supersedes it.

### 📦 Required Context Pills
- [Law 4 — Finite Routing](../context/law-4-finite-routing.md)
- [Async Test Pattern (LangGraph)](../context/async-test-pattern.md)
- [Ariadne State & Models](../context/ariadne-models.md)

### 🚫 Non-Negotiable Constraints
- **Law 4 (Finite Routing):** All loops must have finite circuit breakers. Escalation to HITL MUST occur after 3 agent failures.
- **Law 1 (No Blocking I/O):** All I/O in the test and graph MUST be `async`.
- **DIP Enforcement:** Domain layers (`ariadne`) MUST NOT import from infrastructure layers (`motors`).
