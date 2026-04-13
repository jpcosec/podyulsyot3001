---
type: pattern
domain: architecture
source: tests/architecture/test_single_browser.py:1
---

# Pill: Async Spy Pattern

## Pattern
When testing architectural invariants (like Law 2), use `unittest.mock.patch.object` combined with `nonlocal` counters to track how many times an async method is called across a graph run.

## Implementation
```python
@pytest.mark.asyncio
async def test_my_invariant():
    call_count = 0
    original_func = TargetClass.target_method

    async def tracked_func(self, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        return await original_func(self, *args, **kwargs)

    with patch.object(TargetClass, "target_method", tracked_func):
        # Run the graph
        async with create_ariadne_graph() as app:
            await app.ainvoke(...)

    assert call_count == 1 # Verify the invariant
```

## When to use
Use in Phase 0 fitness tests to verify Law 2 (Single Browser) and Law 1 (Sync I/O detection).

## Verify
Run the test and print `call_count` to ensure it increments as expected.
