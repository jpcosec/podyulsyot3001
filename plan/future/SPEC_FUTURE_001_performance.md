# FUTURE-001: Large Graph Performance Optimization

**Status:** Deferred  
**Priority:** High  
**Estimated Effort:** 3-5 days

---

## Problem

Current implementation freezes with graphs >100 nodes. ELK layout runs on main thread (mitigated by Web Worker). Other operations still slow:
- Dragging nodes is janky
- Pan/zoom lags
- Selection is slow

---

## Proposed Solution

### 1. Virtualization
Use `@xyflow/react` viewport virtualization to only render visible nodes.

```tsx
// Only render nodes in viewport
const visibleNodes = useMemo(() => {
  return nodes.filter(node => isInViewport(node.position, viewport));
}, [nodes, viewport]);
```

### 2. Node Batching
Batch position updates during drag:

```tsx
// Instead of updating on every mouse move
const batchedUpdates = useRef<NodeUpdate[]>([]);
useEffect(() => {
  const timer = setInterval(() => {
    if (batchedUpdates.current.length > 0) {
      updateNodesBatched(batchedUpdates.current);
      batchedUpdates.current = [];
    }
  }, 50);
  return () => clearInterval(timer);
}, []);
```

### 3. Debounced Filters
Debounce filter operations:

```ts
const debouncedFilter = useMemo(
  () => debounce((text) => applyFilter(text), 150),
  []
);
```

### 4. Memoization Strategy
- Wrap NodeShell in `memo()` with proper comparison
- Use `useMemo` for derived state
- Zustand selectors should be atomic

---

## Dependencies

- Current implementation (v2.0.0)
- Performance profiling tools

---

## Risks

- Virtualization may break edge rendering
- Batching could feel less responsive
- Need to measure before optimizing

---

## Acceptance Criteria

| Metric | Target |
|--------|--------|
| Nodes drag (>100) | 60fps |
| Initial load (>100 nodes) | <2s |
| Filter application | <100ms |
| Memory usage | <100MB for 500 nodes |

---

## References

- ReactFlow virtualization: https://reactflow.dev/learn/advanced-performance
- Zustand selectors: https://docs.pmnd.rs/zustand/guides/performance
