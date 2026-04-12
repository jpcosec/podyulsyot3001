# Fitness Function 4: Graph Depth Limit

**Explanation:** Protect against infinite loops - graph must reach HITL or success within X steps when executor always fails.

**Reference:** `tests/unit/automation/fitness/test_graph_depth.py`

**What to fix:** Test that circuit breaker triggers within max steps (10) when executor returns status="failed" every time.

**How to do it:**
1. Create AlwaysFailingExecutor
2. Run graph with memory
3. Assert step_count <= max_steps

**Depends on:** none