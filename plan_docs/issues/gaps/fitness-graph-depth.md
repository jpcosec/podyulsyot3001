# Fitness Function 4: Graph Depth Limit

**Explanation:** Protect against infinite loops - graph must reach HITL or success within X steps when executor always fails.

**Reference:** `tests/unit/automation/fitness/test_graph_depth.py`

**Status:** Test exists but needs fixing.

**Why it fails:**
1. Test uses AlwaysFailingExecutor but graph exits early (map found → goal_achieved)
2. LLM node requires API key (needs mocking)
3. Event handling assumes dict but gets tuples

**What to fix:**
1. Add LLM node mock fixture (patches `llm_rescue_agent_node`)
2. Update test to use portal with failing map (`fitness_test` exists)
3. Fix event handling for both dict/tuple types

**Steps:**
1. Mock `llm_rescue_agent_node` to increment `agent_failures` counter
2. Use `fitness_test` portal map that has no valid targets
3. Assert step_count <= 10 when executor always fails

**Test standard:** Must pass without GOOGLE_API_KEY