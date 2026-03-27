# Spec C2 — Match Editor (Match page enrichment)

**Feature:** `src/features/job-pipeline/`
**Page:** `src/pages/job/Match.tsx`
**Libraries:** `@xyflow/react` · `@tanstack/react-query` · `react-router-dom`
**Phase:** 2 (included in `phase_2_bring_back_migrations`)

---

## Migration Notes

**Legacy source:** `apps/review-workbench/src/pages/JobNodeEditorPage.tsx` in branch `dev`
**Legacy components:**
- `JobNodeEditorPage.tsx` — undo/redo history stack (lines ~65–200)
- `JobNodeEditorPage.tsx` — search handler + "/" shortcut (lines ~500–550)
- `JobNodeEditorPage.tsx` — Arrow key navigation + focusedNode (lines ~200–280)
- `JobNodeEditorPage.tsx` — SHORTCUTS array + showShortcuts modal (lines ~34–42, ~400–424)

**To migrate:**
1. Replace `manualEdges` useState in `Match.tsx` with history-aware stack (Array of snapshots + index pointer)
2. Add `searchQuery` state + `"/"` shortcut → filter/dim nodes in canvas
3. Add `focusedNodeId` + Arrow key navigation through visible nodes
4. Create `ShortcutsModal` atom → `"?"` key toggles it
5. Replace raw JSON dump in `MatchControlPanel` with structured field editor for selected node/edge
6. Pass `searchQuery` + `focusedNodeId` to `MatchGraphCanvas` as props → dim/highlight nodes

---

## 1. Operator Objective

- Use undo (Ctrl+Z) and redo (Ctrl+Y) for manual edge additions and removals
- Press "/" to focus a search bar; type to filter/highlight nodes by label
- Use Arrow Up/Down to cycle through nodes (canvas selection + right panel update)
- Press "?" to open a keyboard shortcuts reference overlay
- See structured fields (not raw JSON) when a requirement node is selected: priority select + text textarea
- See read-only summary when a profile node is selected: evidence title + category
- See score + reasoning when an edge is selected
- All existing features preserved: manual edge draw, Ctrl+S save, Ctrl+Enter commit, HITL modal

---

## 2. Data Contract (API I/O)

**Read:**
- `GET /api/v1/jobs/:source/:jobId/view/match` → `ViewPayload`
  ```ts
  {
    view: 'match';
    data: {
      nodes: GraphNode[];   // { id, label, kind: 'profile'|'requirement', score?, priority? }
      edges: GraphEdge[];   // { id, source, target, score, reasoning, edgeType }
    }
  }
  ```

**Write:**
- `POST /api/v1/jobs/:source/:jobId/editor-state/match` — save manual edges
- `POST /api/v1/jobs/:source/:jobId/gate/review_match` — gate decision (approve/regen/reject)

---

## 3. UI Composition and Layout

**Layout:** Left sidebar (w-64) + ReactFlow canvas (flex-1) + right control panel (w-80)

```
┌── w-64 ──────┬──────────── flex-1 ────────────────────────┬── w-80 ────────┐
│  ASSETS REPO  │  [Search: _______________] [?]              │  PHASE MATCH   │
│               │                                            │                │
│  P_EDU_001    │  [Profile] ──90%──> [Requirement]          │  Selected Node  │
│  P_EXP_005    │  [Profile] ──80%──> [Requirement]  (dim)   │  ─────────────  │
│  …            │  [Profile] ──30%──> [Requirement]  (dim)   │  Priority: MUST │
│               │                                            │  Text: [      ] │
│               │  MiniMap  Controls                         │                │
│               │                                            │  SAVE Ctrl+S   │
│               │                                            │  COMMIT ↵      │
└───────────────┴────────────────────────────────────────────┴────────────────┘
│  Undo (Ctrl+Z) active when manualEdges history length > 0                   │
```

**Core Components:**
- `MatchGraphCanvas` (extended) — accepts `searchQuery`, `focusedNodeId` → dims/highlights nodes
- `ProfileNode` (extended) — accepts `dimmed`, `highlighted` props
- `RequirementNode` (extended) — accepts `dimmed`, `highlighted` + editable priority/text in panel
- `MatchControlPanel` (extended) — structured field editor replacing raw JSON readout
- `ShortcutsModal` (NEW atom) — keyboard overlay with shortcuts table

---

## 4. Styles (Terran Command)

- Search bar: `bg-surface-container border border-outline/30 font-mono text-xs px-2 py-1`
- Dimmed node: `opacity-30`
- Highlighted node: `ring-1 ring-primary/60`
- Shortcuts modal: `fixed inset-0 bg-black/60 flex items-center justify-center z-50`
- Shortcuts table: `font-mono text-[10px]` rows, `kbd` tags for keys

**Interactions:**
- `"/"` key → focus search input
- `Arrow Up/Down` → cycle through matching nodes; update `selectedNode`
- `"?"` key → toggle `ShortcutsModal`
- `Ctrl+Z` → pop from manualEdges history
- `Ctrl+Y` / `Ctrl+Shift+Z` → push forward in history
- `Escape` → clear search / close modal / deselect

**Empty State:** "No match data available. Run the pipeline first."
**Error State:** `MATCH_DATA_NOT_FOUND` monospace error
**Loading State:** Spinner centered

---

## 5. Files to Create / Modify

```
src/features/job-pipeline/
  components/
    MatchControlPanel.tsx     EXTEND: replace JSON dump with structured field editor
    MatchGraphCanvas.tsx      EXTEND: accept searchQuery + focusedNodeId, pass to nodes
    ProfileNode.tsx           EXTEND: accept dimmed + highlighted props
    RequirementNode.tsx       EXTEND: accept dimmed + highlighted props
src/components/atoms/
  ShortcutsModal.tsx          NEW: generic keyboard shortcuts overlay
src/pages/job/
  Match.tsx                   EXTEND: manualEdgesHistory[], searchQuery, focusedNodeId,
                                       extended keyDown handler (?/Arrow/Ctrl+Z/Y)
```

---

## 6. Definition of Done

```
[ ] Match page renders without console errors or TS errors
[ ] Pressing Ctrl+Z undoes the last manually drawn edge
[ ] Pressing Ctrl+Y redoes it
[ ] Pressing "/" focuses the search input above the canvas
[ ] Typing in search dims non-matching nodes and highlights matching ones
[ ] Arrow Up/Down cycles selection through visible nodes; right panel updates
[ ] Pressing "?" opens ShortcutsModal with all 8 shortcuts listed
[ ] Pressing Escape closes the modal / clears search
[ ] Selecting a RequirementNode shows priority select + text textarea (not raw JSON)
[ ] Selecting a ProfileNode shows read-only evidence summary
[ ] Selecting an edge shows score + reasoning text
[ ] All existing features work: draw edge, Ctrl+S save, Ctrl+Enter commit, HITL modal
[ ] No hardcoded data — all from useViewMatch hook + mock
```

---

## 7. E2E (TestSprite)

**URL:** `/jobs/tu_berlin/201397/match`

1. Verify bipartite graph renders with at least 3 profile nodes and 3 requirement nodes
2. Press "/" → verify search input receives focus
3. Type "Python" → verify non-Python nodes dim and Python nodes highlight
4. Press Escape → verify all nodes return to normal opacity
5. Draw a manual edge → verify it appears in gold/amber color
6. Press Ctrl+Z → verify edge disappears
7. Click a requirement node → verify right panel shows priority select (not raw JSON)
8. Press "?" → verify ShortcutsModal appears with keyboard shortcuts table

---

## 8. Git Workflow

### Commit on phase close

```
feat(ui): implement C2 Match Editor enrichment

- Undo/redo for manual edges (history stack, Ctrl+Z/Y)
- Search/filter nodes with "/" shortcut and dim/highlight
- Arrow Up/Down keyboard navigation between nodes
- ShortcutsModal atom ("?" key) with all match shortcuts
- MatchControlPanel: structured field editor for nodes and edges
- ProfileNode/RequirementNode: dimmed + highlighted props
```

### Changelog entry

```markdown
## 2026-MM-DD

- Implemented C2 Match Editor: ported undo/redo, search/filter, keyboard navigation,
  shortcuts modal, and structured field editor from dev JobNodeEditorPage into
  ui-redesign Match page.
```

### Checklist update

- [x] C2 Match Editor — undo/redo, search/filter, keyboard nav, structured field editor
