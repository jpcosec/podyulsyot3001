# Match Page — Node Editor Feature Merge Plan

## Context

Two implementations exist:

| | `ui-redesign` `/jobs/:source/:jobId/match` | `dev` `JobNodeEditorPage` (`?stage=match`) |
|---|---|---|
| **Visual model** | Bipartite graph: profile nodes ← score edge → requirement nodes | JSON tree: Root → Requirements → Match nodes → Evidence nodes |
| **Layout** | Left sidebar + ReactFlow canvas + right control panel | Full-page ReactFlow + breadcrumb nav |
| **Data source** | `useViewMatch` hook (React Query) + `useEvidenceBank` | `getEditorState()` fetch (raw) |
| **HITL action** | `MatchDecisionModal` (approve / regenerate / reject) | None |
| **Edit capability** | Manual edge creation (drag profile → requirement) | Click node to edit JSON value inline |
| **History** | None | Undo/redo stack (50 items, Ctrl+Z / Ctrl+Y) |
| **Keyboard** | Ctrl+S (save), Ctrl+Enter (commit) | Ctrl+S, Ctrl+Z, Ctrl+Shift+Z, /, Arrow Up/Down |
| **Search** | None | Search bar + "/" shortcut to focus |
| **Focus mode** | None | Single node expanded view |
| **Shortcuts modal** | None | "?" key shows all shortcuts |
| **Edge colors** | Score-based (primary ≥70%, secondary ≥30%, error <30%) | Monochrome (arrow edges) |
| **Score display** | Badge on edge + progress bar on requirement node | Score shown as node label text |

## What to keep (ui-redesign is canonical)

| What | Why |
|---|---|
| Bipartite graph (profile ← edge → requirement) | Semantically correct for match visualization |
| `ProfileNode` + `RequirementNode` + `EdgeScoreBadge` | Well-designed components with score color coding |
| `EvidenceBankPanel` (Assets Repo sidebar) | Useful context; drag-to-connect future |
| `MatchControlPanel` right panel | Clean phase header + JSON readout + action buttons |
| `MatchDecisionModal` | HITL gate — approve / regenerate / reject |
| Manual edge creation via `onConnect` | Lets operator add missing match links |
| React Query hooks (`useViewMatch`, `useEditorState`, `useGateDecide`) | Correct cache/mutation patterns |
| Pipeline tab nav (Flow / Scrape / Extract / Match / Sculpt / Deployment) | Part of global shell |

---

## What to port from `dev` `JobNodeEditorPage`

### 1. Undo / Redo for Manual Edges

**Source:** `apps/review-workbench/src/pages/JobNodeEditorPage.tsx`
- `history: Record<string, unknown>[]` state (max 50 items)
- `historyIndex` pointer
- `pushToHistory()` helper called on every mutation
- Ctrl+Z → undo, Ctrl+Y / Ctrl+Shift+Z → redo

**Target:** `pages/job/Match.tsx` — replace `manualEdges` useState with a history-aware version

**What to adapt:** history only needs to track `manualEdges[]` (not the full JSON payload), so the stack is simpler — just `Array<{ source: string; target: string }[]>` with an index pointer.

---

### 2. Search / Filter Nodes

**Source:** `JobNodeEditorPage.tsx`
- `searchQuery: string` state
- `"/"` key shortcut focuses the search input (`searchRef.current?.focus()`)
- Arrow Up/Down navigates through filtered results
- Nodes matching query get highlighted; non-matching are dimmed

**Target:** Add a search bar above the `MatchGraphCanvas`

**Adaptation:** In the bipartite layout, search should filter/highlight both `ProfileNode` and `RequirementNode` by label text. Non-matching nodes get `opacity-30` style; matching nodes get a highlight ring.

---

### 3. Keyboard Navigation Between Nodes

**Source:** `JobNodeEditorPage.tsx` — `focusedNode` state + `ArrowUp`/`ArrowDown` handler

**Target:** `Match.tsx` — add `focusedNodeId` state; ArrowUp/Down cycles through visible nodes in the canvas (profile nodes first, then requirement nodes)

---

### 4. Focus Mode (Single Node Expanded)

**Source:** `JobNodeEditorPage.tsx` — `focusedNode` state + click to set

**Target:** When a node is clicked → `selectedNode` already tracks this. Extend `MatchControlPanel` to show a richer detail view (not just raw JSON) when a node is selected. The raw JSON readout in `MatchControlPanel` already does this partially — just improve the display (structured fields instead of raw JSON).

---

### 5. Keyboard Shortcuts Reference

**Source:** `JobNodeEditorPage.tsx` — `SHORTCUTS` array + `showShortcuts` modal

**Target:** New atom `ShortcutsModal.tsx` in `components/atoms/` or inline in `Match.tsx`

**Shortcuts for Match:**
| Key | Action |
|---|---|
| Ctrl+S | Save state |
| Ctrl+Enter | Open commit modal |
| Ctrl+Z | Undo last manual edge |
| Ctrl+Y / Ctrl+Shift+Z | Redo |
| / | Focus search bar |
| Arrow Up/Down | Navigate nodes |
| ? | Show this shortcuts reference |
| Escape | Deselect / close modal |

---

### 6. Inline Field Editor for Selected Node

**Source:** `JobNodeEditorPage.tsx` — `editorValue` + `selectedPath` + JSON inline textarea

**Target:** Extend `MatchControlPanel` right panel

**What to add:** When a `RequirementNode` is selected, show editable fields:
- `priority` (select: must / should / nice_to_have)
- `text` (textarea — the requirement text)
- Score display (read-only, computed by backend)

When a `ProfileNode` is selected, show read-only fields from the evidence item.

This replaces the raw `JSON.stringify` dump currently in `MatchControlPanel`.

---

## Files to look at (dev branch reference)

| File | What to extract |
|---|---|
| `src/pages/JobNodeEditorPage.tsx` | Undo/redo logic (lines ~65–200), search handler, Arrow key nav, shortcuts modal |

---

## Files to modify (ui-redesign)

| File | Change |
|---|---|
| `pages/job/Match.tsx` | Add `manualEdgesHistory`, search state, focusedNodeId, extended keyDown handler, shortcuts modal trigger |
| `features/job-pipeline/components/MatchControlPanel.tsx` | Replace raw JSON dump with structured field editor for selected node |
| `features/job-pipeline/components/MatchGraphCanvas.tsx` | Accept `searchQuery` + `focusedNodeId` props → pass as node data for highlight styling |
| `features/job-pipeline/components/ProfileNode.tsx` | Accept `dimmed` / `highlighted` props |
| `features/job-pipeline/components/RequirementNode.tsx` | Accept `dimmed` / `highlighted` + editable `priority` / `text` |

## New files to create (ui-redesign)

| File | What |
|---|---|
| `components/atoms/ShortcutsModal.tsx` | Generic keyboard shortcuts overlay (reusable) |

---

---

## Usage Guide

> This section describes the intended operator experience for the Match page.
> Use it as the source of truth when implementing UI copy, empty states, tooltips,
> and interaction behaviour.

### What is this page?

The Match page is the human review stage for the LLM-produced **match graph**.
The pipeline has already run: it scraped the job post, extracted requirements, and
matched each requirement to evidence from your profile. Your job here is to:

1. **Audit** what the model found — are the connections reasonable?
2. **Fix** any gaps — add edges the model missed, or note unmatched requirements.
3. **Commit** your decision: approve, ask for regeneration with feedback, or reject.

Nothing is written back to the pipeline until you hit **Commit Match**.
Save just preserves your in-progress edits locally.

---

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Portfolio > tu_berlin > 201399      FLOW SCRAPE EXTRACT MATCH  │  ← job nav
├──────────────┬──────────────────────────────────┬───────────────┤
│              │                                  │  PHASE        │
│  ASSETS REPO │        MATCH GRAPH               │  MATCH        │
│              │                                  │               │
│  P_EDU_001   │  [Profile] ──80%──> [Requirement]│  (click a     │
│  P_EXP_005   │  [Profile] ──90%──> [Requirement]│   node/edge   │
│  P_EXP_006   │  [Profile] ──30%──> [Requirement]│   to inspect) │
│  …           │                                  │               │
│              │                                  │  SAVE Ctrl+S  │
│              │                                  │  COMMIT ↵     │
└──────────────┴──────────────────────────────────┴───────────────┘
```

**Left — Assets Repo:** All profile evidence items (education, experience, publications,
language facts). Read-only reference. Future: drag an item onto the canvas to create
a new match edge manually.

**Center — Match Graph:** Bipartite ReactFlow canvas.
- Left column: **profile nodes** (your evidence — `P_EDU_001`, `P_EXP_005`, …)
- Right column: **requirement nodes** (job requirements — extracted by the LLM)
- Edges: dashed lines with a score badge. Edge colour signals quality:
  - **Cyan (primary)** ≥ 70% — strong match
  - **Amber (secondary)** 30–69% — partial match
  - **Red (error)** < 30% — weak / indirect match

**Right — Control Panel:** Contextual inspector.
- When nothing selected: "Click a node or edge"
- When a **profile node** is selected: shows evidence ID, category, and summary fields (read-only)
- When a **requirement node** is selected: shows priority, requirement text (editable), and current best score
- When an **edge** is selected: shows score, reasoning text from the LLM, and evidence ID
- Bottom: **Save** and **Commit Match** buttons

---

### Step-by-step workflow

#### 1. Read the graph
Open the page. The graph auto-fits to the viewport.
Scroll or pinch-zoom to inspect. Use the MiniMap (bottom-left) for overview.

Read each edge:
- **Cyan edges** — accepted as-is unless you spot an error
- **Amber edges** — read the reasoning (click the edge → right panel)
- **Red edges** — decide: is this too weak to count? Can you add a better evidence link?

#### 2. Inspect a node or edge
Click any node or edge → the right panel updates with details.

- **Profile node**: see which evidence item this is (e.g. "Research Associate – EEG Stress Detection")
- **Requirement node**: see the requirement text and priority level (must / should / nice_to_have)
- **Edge**: see the LLM's `score` (0–1), `reasoning` explanation, and the `evidence_id` used

#### 3. Add a missing edge
If you know a profile item matches a requirement but the model missed it:
1. Hover over the profile node until the right-side handle (dot) appears
2. Drag from that handle to the target requirement node
3. A new **manual edge** is created (shown in amber/gold instead of cyan — `edgeType: 'manual'`)

Manual edges have no LLM score. They signal to the next stage: "operator confirmed this link."

#### 4. Undo a mistake
`Ctrl+Z` undoes the last manual edge addition.
`Ctrl+Y` (or `Ctrl+Shift+Z`) redoes it.
Only manual edges are undo-able; the LLM-produced edges are read-only.

#### 5. Search for a node
Press `/` to focus the search bar (top of canvas area).
Type any part of a node label — non-matching nodes dim out, matching nodes highlight.
`Arrow Up` / `Arrow Down` cycles through matches and selects them (right panel updates).
`Escape` clears the search and deselects.

#### 6. Save work-in-progress
`Ctrl+S` saves your current manual edges to the backend without committing the gate.
Use this if you want to pause and return later. The graph will reload with your manual
edges intact.

#### 7. Commit the gate decision
When you are satisfied with the graph, press `Ctrl+Enter` or click **COMMIT MATCH**.

The **Gate Decision modal** opens with three options:

| Action | When to use |
|---|---|
| **✓ APPROVE** | The match is good enough. Pipeline continues to document generation. |
| **↻ REQUEST REGEN** | The match has gaps. Write feedback in the text box — the LLM reruns the match stage with your notes. |
| **✗ REJECT** | The job is not a fit. Pipeline terminates for this job. |

After approving, the pipeline advances automatically. You do not need to take further
action on this job until the next gate (Sculpt / document review).

---

### Keyboard shortcuts reference

| Key | Action |
|---|---|
| `Ctrl+S` | Save manual edges (no gate commit) |
| `Ctrl+Enter` | Open Commit Match modal |
| `Ctrl+Z` | Undo last manual edge |
| `Ctrl+Y` / `Ctrl+Shift+Z` | Redo |
| `/` | Focus search bar |
| `Arrow Up` / `Arrow Down` | Cycle through search results / all nodes |
| `Escape` | Clear search / close modal / deselect |
| `?` | Show this shortcuts reference |

---

### Empty and error states

| State | What the operator sees |
|---|---|
| Match not yet run | "No match data available. Run the pipeline first." |
| All requirements matched (cyan) | Normal graph — proceed to commit |
| Unmatched requirements | Requirement node has no incoming edge — red outline + "Unmatched" label |
| Save failed | Error toast: "Save failed — check connection" |
| Gate already committed | Read-only mode: graph visible but COMMIT button disabled, banner: "Decision already recorded" |

---

## Suggested implementation order

1. Add undo/redo for `manualEdges` in `Match.tsx`
2. Add `?` shortcut → `ShortcutsModal` (reusable atom)
3. Add search state + `"/"` shortcut → filter/highlight nodes in canvas
4. Add Arrow key navigation through nodes
5. Replace raw JSON dump in `MatchControlPanel` with structured field editor
6. Extend `RequirementNode` / `ProfileNode` with `dimmed` / `highlighted` props for search
