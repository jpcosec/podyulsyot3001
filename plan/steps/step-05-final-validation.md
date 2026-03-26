# Step 05: Final Validation (Consolidated E2E)

**Context:** Run this only after all GRP and UI steps are complete.

---

## 1. Purpose

- Validate integration end-to-end once
- Catch cross-step regressions that local checks cannot detect

---

## 2. Scope

- Schema load and dynamic registry population
- Graph render and interactions (drag, connect, delete)
- Undo/redo semantic behavior
- Sidebar, panels, and UI overlays
- Save roundtrip (`schemaToGraph` -> editor -> `graphToDomain`)
- ELK worker layout execution

---

## 3. Verification checklist

- [ ] Opening graph page renders nodes and edges
- [ ] Drag updates are smooth and do not flood semantic undo stack
- [ ] Deleting via ReactFlow callbacks syncs store history
- [ ] Save operation marks graph as clean
- [ ] Worker-based layout runs without runtime errors
- [ ] Command dialog/context menu/sonner work as expected

---

## 4. Output

Record final status summary in PR/commit notes:

- Passed checks
- Known deviations
- Follow-up items moved to `plan/future/`
