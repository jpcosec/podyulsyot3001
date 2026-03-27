# CV Graph Editor — Feature Merge Plan

## Goal

Port the richer interaction model from `dev` branch `CvGraphEditorPage` into the
`ui-redesign` branch `BaseCvEditor` (`/cv`), while keeping the cleaner
architecture of `ui-redesign` (persistent nav, React Query hooks, feature-sliced
structure, `cn()` design system).

---

## What to keep (ui-redesign is canonical)

| What | File | Why keep |
|---|---|---|
| Persistent global nav | shell layout in `ui-redesign` App.tsx | Cleaner UX than sandbox breadcrumbs |
| React Query hooks | `features/base-cv/api/useCvProfileGraph.ts` | Correct cache/mutation pattern |
| `apiClient` CQRS calls | `api/client.ts` query/commands shape | Aligned with API v2 contract |
| `BaseCvEditor` as page root | `pages/global/BaseCvEditor.tsx` | Correct route: `/cv` |
| Design system (`cn`, Tailwind tokens) | throughout | Consistent with ui-redesign theme |

---

## What to port from `dev` CvGraphEditorPage

### 1. Collapsible Group Nodes

**Source:** `apps/review-workbench/src/sandbox/components/cv-graph/GroupNode.tsx`
**Source:** logic inside `CvGraphEditorPage.tsx` — `buildGraphView()` group section (lines 338–409)

**Target:** New file `features/base-cv/components/GroupNode.tsx`

**What it does:**
- Groups entries by category into a collapsible container node
- Shows count badge, expand/collapse chevron, "Add entry" button
- Highlights as dropzone when an entry is dragged over it

**State to add to `BaseCvEditor`:**
- `expandedGroups: Set<string>` — which categories are open
- `activeDropzoneCategory: string | null` — drag-over highlight

---

### 2. Skill Ball Nodes (mastery-colored)

**Source:** `apps/review-workbench/src/sandbox/components/cv-graph/SkillBallNode.tsx`
**Source:** `apps/review-workbench/src/sandbox/lib/mastery-scale.ts`

**Target:** Replace `features/base-cv/components/SkillNode.tsx` with richer version
**Target:** New file `features/base-cv/lib/mastery-scale.ts` (copy as-is)

**What it does:**
- Circular/diamond/square shape depending on skill shape setting
- `fillColor` computed from `masteryColorForCategory(category, masteryTag)`
- Shows 2-letter abbreviation, label, and mastery score below the ball
- Essential skills get a highlighted ring

---

### 3. Proxy Edge (collapsed-group-aware)

**Source:** `apps/review-workbench/src/sandbox/components/cv-graph/ProxyEdge.tsx`
**Source:** edge rendering logic in `CvGraphEditorPage.tsx` — `buildGraphView()` edge section (lines 478–505)

**Target:** New file `features/base-cv/components/ProxyEdge.tsx`

**What it does:**
- Renders "demonstrates" edges with solid line (real) or dashed line (proxy, when group is collapsed)
- Deduplicates edges that collapse to the same group-level connection
- Animated edges for related skills

---

### 4. Entry Inline Expand Panel

**Source:** `apps/review-workbench/src/sandbox/components/cv-graph/EntryNode.tsx` (lines 59–122)

**Target:** Extend `features/base-cv/components/EntryNode.tsx`

**What it adds:**
- Click to expand a floating panel on the node (`.cv-entry-expand-panel`)
- Category text input
- Essential checkbox
- Description bullets list with weight badges (H/P/S/F)
- "Add description" button
- Connected skill labels list

**State to add to `BaseCvEditor`:**
- `focusedEntryId: string` — which entry has its panel open

---

### 5. Skill Palette Sidebar (replaces `ProfileStats` when entry focused)

**Source:** `CvGraphEditorPage.tsx` lines 1332–1435 (right sidebar when `focusedEntry` is set)

**Target:** New file `features/base-cv/components/SkillPalette.tsx`

**What it does:**
- When an entry is focused: splits skills into "Related" (has demonstrates edge) and "Unrelated"
- Unrelated skills shown as clickable chips grouped by category
- "Add skill" button
- Shows mastery level badge on each chip

**`ProfileStats` becomes conditional:** shown when nothing selected; `SkillPalette` shown when entry focused.

---

### 6. Selected Skill Editor (inline in sidebar)

**Source:** `CvGraphEditorPage.tsx` lines 1381–1435

**Target:** Extend `NodeInspector.tsx` or new `SkillEditor.tsx` within `features/base-cv/components/`

**What it adds:**
- Skill name input
- Skill category input
- Mastery select (dropdown from `MASTERY_SCALE`)
- Essential checkbox

---

### 7. Drag-to-Reorder Entries within Group

**Source:** `CvGraphEditorPage.tsx` functions `reorderCategoryEntries()`, `onNodeDrag`, `onNodeDragStop` (lines 171–202, 1030–1096)
**Source:** `findContainerAtPoint()`, `resolveNodeAbsolutePosition()`, `nodeCenterPoint()` helpers

**Target:** Logic in `features/base-cv/components/CvGraphCanvas.tsx` (add to canvas handler props)

**What it does:**
- On drag: computes which group container the entry center is over → highlights dropzone
- On drag stop: reorders entries within their category by computing target index from Y position

---

### 8. Container Order Panel (sidebar: ↑/↓ for selected group)

**Source:** `CvGraphEditorPage.tsx` lines 1438–1471

**Target:** Section in `features/base-cv/components/NodeInspector.tsx` when `selectedGroupCategory` is set

**What it does:**
- When a group header is selected ("Edit" button): shows list of its entries with ↑/↓ reorder buttons

---

### 9. Demonstrates Edge Management (draw connections)

**Source:** `CvGraphEditorPage.tsx` — `onConnect`, `resolveConnectionPair()` (lines 665–1144)

**Target:** `features/base-cv/components/CvGraphCanvas.tsx` — add `onConnect` handler

**What it does:**
- Drag from entry right-handle to skill left-handle (or vice versa) creates a demonstrates edge
- Validates: both nodes must exist, edge must not already exist
- Sets `focusedEntryId` and `selectedSkillId` after connect

---

### 10. Add Entry / Add Skill

**Source:** `CvGraphEditorPage.tsx` — `onAddEntry` (lines 783–809), `onAddSkill` (lines 895–918)

**Target:** Inline in `BaseCvEditor.tsx` mutation handlers

**What it does:**
- "Add entry" button on group node → appends new `CvEntry` with placeholder fields
- "Add skill" button → appends new `CvSkill` with default mastery
- Both mark graph as dirty and trigger re-render

---

### 11. Add Description Bullet to Entry

**Source:** `CvGraphEditorPage.tsx` — `onAddDescription`, `nextDescriptionWeight()`, `ensureUniqueDescriptionKey()` (lines 256–267, 865–889)
**Source:** `apps/review-workbench/src/sandbox/lib/mastery-scale.ts` — `nextDescriptionWeight()`

**Target:** Handler in `BaseCvEditor.tsx`, helper in `features/base-cv/lib/`

---

## Files to copy verbatim (no changes needed)

| Source (dev branch) | Target (ui-redesign, features/base-cv/) |
|---|---|
| `sandbox/components/cv-graph/types.ts` | `features/base-cv/components/types.ts` — may need to merge with existing types |
| `sandbox/lib/mastery-scale.ts` | `features/base-cv/lib/mastery-scale.ts` |
| `sandbox/components/cv-graph/ProxyEdge.tsx` | `features/base-cv/components/ProxyEdge.tsx` |

---

## State delta for `BaseCvEditor`

The following state fields need to be added to `BaseCvEditor.tsx` (currently only has `editedEntries`, `editedSkills`, `selectedNodeId`, `selectedNodeType`):

```ts
const [expandedGroups, setExpandedGroups] = useState<Set<string>>(() => new Set());
const [focusedEntryId, setFocusedEntryId] = useState('');
const [selectedSkillId, setSelectedSkillId] = useState('');
const [selectedGroupCategory, setSelectedGroupCategory] = useState<string | null>(null);
const [activeDropzoneCategory, setActiveDropzoneCategory] = useState<string | null>(null);
```

And the mutation handlers currently in `BaseCvEditor` (`handleEntryChange`, `handleSkillChange`) need to be extended with:
- `onAddEntry(category)`
- `onAddSkill()`
- `onAddDescription(entryId)`
- `onUpdateDescription(entryId, key, text)`
- `onToggleEssential(id, type)`
- `onConnect` (demonstrates edge)
- `onNodeDrag` / `onNodeDragStop` (reorder)
- `moveEntryInsideSelectedGroup(entryId, direction)`

---

## What NOT to port

| Feature | Reason |
|---|---|
| `CvGraphEditorPage` breadcrumb nav | ui-redesign has better persistent sidebar nav |
| Inline `getCvProfileGraphPayload()` fetch | ui-redesign uses React Query (better) |
| Raw `fetch()` save | ui-redesign uses `useSaveCvGraph` mutation (better) |
| Sandbox-path component locations | Move everything to `features/base-cv/` |
| `dagre` top-level group layout from dev | ui-redesign dagre layout is simpler and sufficient; keep it, just add group nodes as top-level |

---

## Suggested implementation order

1. Copy `mastery-scale.ts` → `features/base-cv/lib/`
2. Add `GroupNode.tsx` with collapsible logic
3. Upgrade `SkillNode.tsx` → mastery-colored ball with `SkillBallNode` shape
4. Add `ProxyEdge.tsx`
5. Upgrade `CvGraphCanvas.tsx` — group-based layout + proxy edges + drag reorder + `onConnect`
6. Upgrade `EntryNode.tsx` — inline expand panel with descriptions
7. Add `SkillPalette.tsx` — sidebar skill panel when entry focused
8. Extend `NodeInspector.tsx` — skill mastery editor + group reorder panel
9. Extend `BaseCvEditor.tsx` — add all new state + handlers
10. Wire "Add entry" / "Add skill" / "Add description" through group/entry node buttons
