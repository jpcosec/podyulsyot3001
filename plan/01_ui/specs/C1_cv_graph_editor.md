# Spec C1 — CV Graph Editor (BaseCvEditor enrichment)

**Feature:** `src/features/base-cv/`
**Page:** `src/pages/global/BaseCvEditor.tsx`
**Libraries:** `@xyflow/react` · `@dagrejs/dagre` · `@tanstack/react-query` · `react-router-dom`
**Phase:** 2 (included in `phase_2_bring_back_migrations`)

---

## Migration Notes

**Legacy source:** `apps/review-workbench/src/sandbox/` in branch `dev`
**Legacy components:**
- `sandbox/pages/CvGraphEditorPage.tsx` — full implementation (1515 lines)
- `sandbox/components/cv-graph/GroupNode.tsx` — collapsible category container
- `sandbox/components/cv-graph/SkillBallNode.tsx` — mastery-colored circle/diamond
- `sandbox/components/cv-graph/ProxyEdge.tsx` — proxy-aware dashed edge
- `sandbox/components/cv-graph/types.ts` — EntryNodeData, SkillNodeData, GroupNodeData
- `sandbox/lib/mastery-scale.ts` — MASTERY_SCALE, masteryColorForCategory, resolveMasteryLevel

**To migrate:**
1. Copy `sandbox/lib/mastery-scale.ts` → `features/base-cv/lib/mastery-scale.ts` verbatim
2. Copy `sandbox/components/cv-graph/ProxyEdge.tsx` → `features/base-cv/components/ProxyEdge.tsx` verbatim
3. Extract and adapt `GroupNode.tsx`, `SkillBallNode.tsx` → keep component shape, replace raw CSS with Tailwind/cn tokens
4. Extend `CvGraphCanvas.tsx` to use GroupNode-based layout + group expand/collapse state
5. Upgrade `EntryNode.tsx` to add inline expand panel (descriptions, essential toggle, connected skills list)
6. Add `SkillPalette.tsx` right-sidebar panel (related/unrelated split when entry focused)
7. Extend `NodeInspector.tsx`: skill mastery editor + group reorder (↑/↓) panel
8. Extend `BaseCvEditor.tsx`: 5 new state fields + 8 new mutation handlers

---

## 1. Operator Objective

- Expand/collapse category groups to manage visual complexity
- Click an entry node to open its inline editing panel (descriptions, essential toggle, category)
- Edit description bullets inline (text + weight H/P/S/F)
- Add new description bullets per entry
- See connected skill labels within an expanded entry card
- View mastery-colored skill balls (cyan=expert, amber=intermediate, red=beginner)
- Click a skill ball to inspect/edit it in the right sidebar (name, category, mastery, essential)
- When an entry is focused, skill panel splits into "Related" and "Unrelated" buckets
- Drag entry nodes within a group to reorder; or use ↑/↓ when group header is selected
- Draw a new "demonstrates" edge by dragging from an entry handle to a skill handle
- Add new entries via group "Add entry" button; add new skills via skill palette "+ Add skill"
- Save all changes (dirty state + Ctrl+S)

---

## 2. Data Contract (API I/O)

**Read:**
- `GET /api/v1/portfolio/cv-profile-graph` → `CvProfileGraphPayload`
  ```ts
  {
    entries: CvEntry[];          // { id, category, essential, fields, descriptions[] }
    skills: CvSkill[];           // { id, label, category, essential, level, meta }
    demonstrates: CvDemonstratesEdge[];  // { id, source, target, description_keys[] }
    snapshot_version: string;
    captured_on: string;
  }
  ```

**Write:**
- `PUT /api/v1/portfolio/cv-profile-graph` → `CvProfileGraphPayload` (full payload replace)
  - Triggered by Save button / Ctrl+S

---

## 3. UI Composition and Layout

**Layout:** Full-height split — ReactFlow canvas (flex-1) + right sidebar (w-80)

```
┌────────────────────────── flex-1 ──────────────────────┬── w-80 ──────────┐
│  [Group: Education ▶]  [Group: Experience ▼]  [Skills]  │  Skill Palette   │
│                         ┌─────────────┐                  │  ─────────────   │
│                         │ Entry card  │──80%──● Python   │  Unrelated:      │
│                         │ (expanded)  │                  │  ○ Docker        │
│                         └─────────────┘                  │  ○ FastAPI       │
│  MiniMap  Controls  Background                           │  + Add skill     │
│                                                          │  [Selected Skill]│
│                                                          │  ─────────────   │
│                                                          │  Mastery Scale   │
│                                                          │  Graph Meta      │
├──────────────────────────────────────────────────────────┤  ─────────────   │
│  [Dirty indicator]  [Saving…]  [Save changes]            │                  │
└──────────────────────────────────────────────────────────┴──────────────────┘
```

**Core Components:**
- `GroupNode` — collapsible container with header (label, count, ▼/▶), "Add entry" button, dropzone highlight
- `EntryNode` — card with left handle, right handle; expandable panel with fields
- `SkillBallNode` — colored circle (fillColor from mastery), abbreviation label, caption below
- `ProxyEdge` — dashed (proxy/collapsed) or solid (real) animated teal edge with "demonstrates" label
- `CvGraphCanvas` — ReactFlow + dagre LR layout using GroupNode containers
- `SkillPalette` — right sidebar: unrelated skill chips grouped by category + selected skill form
- `NodeInspector` (extended) — group reorder panel when group header selected

---

## 4. Styles (Terran Command)

- Group node header: `bg-surface-container border border-outline/30 font-mono text-[10px] uppercase`
- Group dropzone active: `border-primary/60 bg-primary/5`
- Entry card: `bg-surface-container border border-outline/30 border-l-4` (color by category)
- Entry expanded panel: `bg-white/95 backdrop-blur-sm` (absolute, zIndex 30)
- Skill ball: `rounded-full` (or `rotate-45` for diamond), `fillColor` as `backgroundColor`
- Essential skill ring: `ring-2 ring-primary`
- Proxy edge: `strokeDasharray: '6 4'`, `opacity: 0.72`
- Real edge: solid, `stroke: '#0f766e'`, `strokeWidth: 1.8`

**Interactions:**
- Click group header → toggle expand/collapse
- Click "Edit" in group header → select group (right panel shows reorder list)
- Click entry card → toggle inline expand panel
- Drag entry to different group → category update on drop
- Drag entry within group → reorder on drop
- Drag entry handle → skill handle → create demonstrates edge
- Click skill ball → select in right panel
- Click edge → focus connected entry + skill

**Empty State:** "Load your CV profile to start editing" (graph is empty)
**Error State:** `<p className="font-mono text-error text-sm">{error}</p>`
**Loading State:** Skeleton (3 skeleton group cards + skeleton skill column)

---

## 5. Files to Create / Modify

```
src/features/base-cv/
  lib/
    mastery-scale.ts          COPY verbatim from dev sandbox/lib/mastery-scale.ts
  components/
    GroupNode.tsx             NEW: collapsible category container node
    SkillBallNode.tsx         NEW: mastery-colored skill ball (replaces SkillNode.tsx)
    ProxyEdge.tsx             COPY verbatim from dev sandbox/components/cv-graph/ProxyEdge.tsx
    EntryNode.tsx             EXTEND: add inline expand panel, description bullets
    NodeInspector.tsx         EXTEND: add skill mastery editor + group reorder section
    SkillPalette.tsx          NEW: right sidebar — related/unrelated split + add skill
    CvGraphCanvas.tsx         REWRITE: GroupNode-based layout, proxy edges, drag handlers
    types.ts                  NEW: EntryNodeData, SkillNodeData, GroupNodeData (from dev)
src/pages/global/
  BaseCvEditor.tsx            EXTEND: 5 new state fields + 8 new handlers
```

---

## 6. Definition of Done

```
[ ] BaseCvEditor renders without console errors or TS errors
[ ] Entries are grouped in collapsible GroupNode containers by category
[ ] Clicking group header toggles expand/collapse; entry nodes appear/disappear
[ ] Clicking an entry card opens inline panel with category input, essential checkbox, descriptions
[ ] Description bullets show weight badge (H/P/S/F) and are editable inline
[ ] "+ Add description" button adds a new bullet to the expanded entry
[ ] Skill balls are colored by mastery level (teal=expert, amber=mid, red=beginner)
[ ] Clicking a skill ball selects it; right panel shows name/category/mastery/essential editor
[ ] When entry is focused, right panel splits skills into Related vs Unrelated
[ ] Dragging entry handle to skill handle creates a demonstrates edge
[ ] Dragging entry within group reorders it (position updates on drop)
[ ] "+ Add entry" on group node creates a new entry in that category
[ ] "+ Add skill" creates a new skill in the skill palette
[ ] Save button is enabled when dirty; disabled when clean or saving
[ ] Ctrl+S triggers save
[ ] No hardcoded data — all from useCvProfileGraph hook + mock
```

---

## 7. E2E (TestSprite)

**URL:** `/cv`

1. Verify at least 3 GroupNode containers render (Education, Experience, Skills)
2. Click a group header → verify entries appear/disappear
3. Click an entry card → verify inline panel opens with "Descriptions" section
4. Verify skill balls render with color (not white/grey default)
5. Click a skill ball → verify right panel shows mastery select dropdown
6. Verify "Save changes" button is disabled initially; edit something → verify it becomes enabled
7. Verify Ctrl+S triggers save (button shows "Saving...")

---

## 8. Git Workflow

### Commit on phase close

```
feat(ui): implement C1 CV Graph Editor enrichment

- GroupNode collapsible containers with expand/collapse and drag-drop
- SkillBallNode with mastery color coding (masteryColorForCategory)
- ProxyEdge for collapsed-group-aware edge rendering
- EntryNode inline expand panel (descriptions, essential, connected skills)
- SkillPalette sidebar (related/unrelated split, skill editor)
- CvGraphCanvas rebuilt with group-based dagre layout
- BaseCvEditor extended with 5 state fields and 8 mutation handlers
```

### Changelog entry

```markdown
## 2026-MM-DD

- Implemented C1 CV Graph Editor: ported collapsible groups, mastery-colored skill
  balls, inline entry editing, skill palette, and demonstrates edge management from
  dev sandbox into ui-redesign BaseCvEditor.
```

### Checklist update

- [x] C1 CV Graph Editor — collapsible groups, mastery skill balls, inline entry editing
