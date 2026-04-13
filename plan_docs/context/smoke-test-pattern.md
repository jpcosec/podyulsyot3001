---
type: pattern
domain: scraping
source: src/automation/main.py:1
---

# Pill: Smoke Test Pattern (Corneta)

## Pattern
Integration test that deliberately breaks the full cascade (deterministc, heuristics, agent) to verify the HITL circuit breaker works.

## Implementation
```python
@pytest.mark.asyncio
async def test_corneta_cascade_to_hitl():
    # 1. Use an executor that always fails
    executor = FailingExecutor() 
    
    # 2. Use a portal with non-existent targets
    initial_state = {"portal_name": "fitness_test", ...}
    
    # 3. Assert graph reaches human_in_the_loop
    async with executor:
        async with create_ariadne_graph() as app:
            async for chunk in app.astream(initial_state, config):
                # steps tracked here
    
    assert final_node == "human_in_the_loop"
```

## When to use
Use in Phase 2 `Task 2.1 — The Corneta Test`.

## Verify
Verify that the test fails if the circuit breaker (agent failures counter) is removed.
