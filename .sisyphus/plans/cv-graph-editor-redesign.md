# CV Graph Editor Redesign (v2 — corrected)

## TL;DR

> **Quick Summary**: Redesign the CV graph editor UX while preserving the existing box-in-box group→entry layout. Add Tailwind CSS. Entry nodes gain a right-expanding edit panel with inline form fields, descriptions, and a "+" add button. Skills render as colored circles with category hue × mastery intensity and always-visible labels. Related skills connect to the focused entry; unrelated skills live in a repurposed side panel (skill palette). Skill linking via React Flow `onConnect` handles.
>
> **Deliverables**:
> - Tailwind CSS integration alongside existing CSS custom properties
> - Mastery scale database (5-level, name + numeric value + intensity)
> - Custom `EntryNode` component (compact card + right-expanding edit panel)
> - Custom `SkillBallNode` component (colored circle, polymorphic shape-ready)
> - Custom `GroupNode` component (preserve box-in-box, add "+" button)
> - Repurposed side panel as skill palette (unconnected skills pool)
> - `onConnect`-driven skill matching with `isValidConnection`
> - "+" add buttons on every container (groups, entries)
>
> **Estimated Effort**: Medium-Large
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Wave 1 (infra + components) → Wave 2 (integration) → Wave 3 (polish + verify)

---

## Context

### Original Request (with corrections)

User wants a better graph editing experience with these SPECIFIC constraints:

1. **DO NOT modify the box-in-box layout** — current group→entry nesting via `parentId` + `extent: "parent"` is correct. Entry positions `{ x: 14, y: 50 + idx * 78 }` relative to parent group must be preserved.
2. **Entry click expands TO THE RIGHT** — an adjacent edit panel appears beside the entry node, not an in-place height change. The card structure stays.
3. **Description is NOT a node** — it's a property inside EntryNode, visible only when the entry is expanded.
4. **Skills as colored circles**:
   - Related skills: connected to the focused entry via edges
   - Unrelated skills: shown in a separate box (repurposed side panel)
   - Category color on each ball
   - Mastery level = color intensity (darker = more proficient)
   - Mastery has BOTH a name tag AND numerical value
   - Need a "scale database" for mastery
   - Skill name ALWAYS visible (not hover-only)
5. **"+" button** at bottom of every box to add new contained items
6. **USE Tailwind** — add to the project (user: "wonderful addition")
7. **Side panel REPURPOSED** — not deleted; becomes skill palette / unconnected skill pool
8. **Polymorphic shapes** — skills are circles now but the component should support future shapes
9. **New dependencies allowed** — whatever helps readability and maintainability

### Box-in-Box Contract (MUST PRESERVE)

```
Group node: id="group:{category}", NO parentId, width=340, height=dynamic
  └─ Entry node: parentId="group:{category}", extent="parent"
       position: { x: 14, y: 50 + entryIndex * 78 }
       width: 300, height: 58
       draggable: true (constrained to parent)

Group node: id="group:skills", width=360
  └─ Skill node: parentId="group:skills", extent="parent"
       position: { x: 14, y: 50 + skillIndex * 58 }
       width: 320, height: 42
```

Groups are NOT draggable. Entries/skills ARE draggable but constrained by parent bounds.

### Mastery Scale Database

5-level unified scale (covers programming, languages, soft skills, domain knowledge):

| Value | Tag | Label | CEFR | Dreyfus | Intensity | Color Example (blue) |
|-------|-----|-------|------|---------|-----------|---------------------|
| 1 | novice | Novice | A1 | Novice | 0.17 | `#DBEAFE` (very light) |
| 2 | beginner | Beginner | A2 | Adv. Beginner | 0.33 | `#93C5FD` (light) |
| 3 | intermediate | Intermediate | B1-B2 | Competent | 0.50 | `#3B82F6` (medium) |
| 4 | advanced | Advanced | C1 | Proficient | 0.75 | `#1D4ED8` (dark) |
| 5 | expert | Expert | C2 | Expert | 1.0 | `#1E3A8A` (very dark) |

Formula: take category hue, apply lightness based on intensity. Skill name + mastery tag always visible.

---

## Work Objectives

### Core Objective
Enhance the CV graph editor with inline entry editing (right-expand), connection-based skill matching, mastery-intensity skill balls, and a repurposed skill palette side panel — while preserving the existing box-in-box layout.

### Concrete Deliverables
- `apps/review-workbench/src/components/cv-graph/EntryNode.tsx`
- `apps/review-workbench/src/components/cv-graph/SkillBallNode.tsx`
- `apps/review-workbench/src/components/cv-graph/GroupNode.tsx`
- `apps/review-workbench/src/lib/mastery-scale.ts` (scale database)
- `apps/review-workbench/src/pages/CvGraphEditorPage.tsx` (refactored)
- Tailwind CSS setup files (`tailwind.config.js`, `postcss.config.js`)
- `apps/review-workbench/src/styles.css` (updated, Tailwind integrated)

### Must Have
- Tailwind CSS installed and working alongside existing CSS variables
- Custom `nodeTypes` registered on `<ReactFlow>`
- Entry compact mode: category strip + title + description count + essential badge
- Entry expanded mode: right-expanding panel with editable fields, description list, connected skill pills
- Description as inline property (NOT a separate node), editable textareas
- "+" button at bottom of groups (add entry) and entries (add description)
- SkillBallNode: circle, category color × mastery intensity, always-visible label, level tag
- Related skills connected to focused entry; unrelated skills in side panel palette
- `onConnect` handler creating demonstrates edges
- `isValidConnection` rejecting invalid connection types
- Mastery scale lookup table with name + value + intensity
- `nodrag` on all interactive form elements inside nodes

### Must NOT Have (Guardrails)
- Must NOT modify box-in-box nesting (`parentId`, `extent`, entry positions)
- Must NOT delete the side panel `<aside>` element (repurpose it)
- Must NOT make Description a separate React Flow node
- Must NOT make skill names hover-only (always visible)
- No `as any` or `@ts-ignore`

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: NO
- **Automated tests**: NO
- **Framework**: N/A

### QA Policy
Every task MUST include agent-executed QA scenarios via Playwright.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Infrastructure + Components — MAX PARALLEL):
├── Task 1: Install Tailwind CSS + configure with Vite [quick]
├── Task 2: Create mastery scale database module [quick]
├── Task 3: Create EntryNode component (compact + right-expand edit) [visual-engineering]
├── Task 4: Create SkillBallNode component (circle, mastery intensity) [visual-engineering]
├── Task 5: Create GroupNode component (preserve nesting, add "+" button) [visual-engineering]
└── Task 6: Update CSS: Tailwind utilities + node component styles [visual-engineering]

Wave 2 (Integration — wire into page, depends on Wave 1):
├── Task 7: Refactor CvGraphEditorPage: nodeTypes, repurpose sidepanel [deep]
├── Task 8: Implement onConnect + isValidConnection [deep]
├── Task 9: Implement skill visibility logic (related connected, unrelated in palette) [deep]
└── Task 10: Implement expand/collapse with dagre re-layout [deep]

Wave 3 (Polish + Verify — depends on Wave 2):
├── Task 11: Visual polish + accessibility pass [visual-engineering]
├── Task 12: Build + type-check + Playwright validation [unspecified-high]
└── Task 13: Update docs/changelog [writing]

Wave FINAL (4 parallel reviews → user okay):
├── F1: Plan compliance audit [oracle]
├── F2: Code quality review [unspecified-high]
├── F3: Real Playwright QA [unspecified-high]
└── F4: Scope fidelity check [deep]
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|-----------|--------|
| 1    | —         | 3, 4, 5, 6, 7 |
| 2    | —         | 4, 7, 9 |
| 3    | 1         | 7 |
| 4    | 1, 2      | 7, 8, 9 |
| 5    | 1         | 7 |
| 6    | 1         | 7, 11 |
| 7    | 1-6       | 8, 9, 10, 11, 12 |
| 8    | 4, 7      | 12 |
| 9    | 2, 4, 7   | 12 |
| 10   | 3, 5, 7   | 12 |
| 11   | 7-10      | 12 |
| 12   | 7-11      | 13 |
| 13   | 12        | F1-F4 |

---

## TODOs

- [ ] 1. Install Tailwind CSS + Configure with Vite

  **What to do**:
  - Install: `npm install -D tailwindcss @tailwindcss/vite` (Tailwind v4 uses Vite plugin directly)
  - Add Tailwind Vite plugin to `vite.config.ts`
  - Add `@import "tailwindcss"` at the top of `src/styles.css`
  - Verify existing CSS custom properties (`:root` vars) still work alongside Tailwind
  - Verify `npm run build` passes with Tailwind active

  **Must NOT do**:
  - Do NOT delete or replace existing CSS custom properties
  - Do NOT convert existing styles to Tailwind (leave them as-is, Tailwind is for new code)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 3, 4, 5, 6, 7
  - **Blocked By**: None

  **References**:
  - Tailwind v4 Vite setup: `https://tailwindcss.com/docs/installation/vite`
  - Current Vite config: `apps/review-workbench/vite.config.ts`
  - Current styles: `apps/review-workbench/src/styles.css`

  **QA Scenarios:**
  ```
  Scenario: Tailwind classes render correctly alongside existing CSS
    Tool: Bash
    Steps:
      1. Run npm run build
      2. Verify exit code 0
      3. Check output CSS contains both Tailwind reset and existing :root variables
    Expected Result: Build succeeds, both CSS systems coexist
    Evidence: .sisyphus/evidence/task-1-tailwind-build.log
  ```

  **Commit**: YES
  - Message: `build(workbench): add Tailwind CSS v4 with Vite plugin`

---

- [ ] 2. Create Mastery Scale Database Module

  **What to do**:
  - Create `apps/review-workbench/src/lib/mastery-scale.ts`
  - Export `MASTERY_SCALE` array: `{ value: number, tag: string, label: string, cefrEquiv: string, dreyfus: string, intensity: number }`
  - Export `getMasteryLevel(tag: string): MasteryLevel | null`
  - Export `getMasteryByValue(value: number): MasteryLevel | null`
  - Export `masteryIntensity(tag: string | null): number` — returns 0.5 default for unknown/null
  - Export `masteryColorForCategory(categoryHue: number, masteryTag: string | null): string` — returns HSL string with lightness derived from intensity
  - Export category hue map: `CATEGORY_HUES: Record<string, number>` mapping `programming → 210, language → 270, soft_skill → 35, ...`

  **Must NOT do**:
  - No React components here (pure data + functions)
  - No side effects

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 4, 7, 9
  - **Blocked By**: None

  **References**:
  - Mastery scale research in draft: `.sisyphus/drafts/cv-graph-domain-model.md` (bottom section)
  - Skill type: `apps/review-workbench/src/types/models.ts:CvSkill`

  **QA Scenarios:**
  ```
  Scenario: Scale lookup returns correct values
    Tool: Bash
    Steps:
      1. npm run build (type-checks the module)
    Expected Result: Module exports compile, types are correct
    Evidence: .sisyphus/evidence/task-2-mastery-build.log
  ```

  **Commit**: YES
  - Message: `feat(cv-graph): add mastery scale database with category hue mapping`

---

- [ ] 3. Create EntryNode Custom Component

  **What to do**:
  - Create `apps/review-workbench/src/components/cv-graph/EntryNode.tsx`
  - **Compact mode** (default):
    - Category color strip on left edge (4px wide, full height)
    - Title text (role @ org, or degree @ institution, etc.)
    - Description count badge (e.g., "3 bullets") as small pill
    - Essential badge if `data.essential === true`
    - Click anywhere on node toggles `data.expanded`
  - **Expanded mode** (right-expanding panel):
    - Compact card STAYS the same on the left
    - Edit panel expands to the RIGHT of the card (adjacent, not below)
    - Edit panel contains:
      - Category input (text, `nodrag` class)
      - Essential checkbox (`nodrag`)
      - Description list: one textarea per description (`nodrag`), each showing key + text
      - "+" button at bottom of descriptions to add a new one
      - Connected skill pills (read-only, colored by category)
    - Edit panel width: ~280px, appearing to the right of the 300px entry card
  - `<Handle type="source" position={Position.Right}>` on the card body for connecting to skills
  - `isValidConnection`: only allow connecting to nodes with `data.kind === "skill"`
  - All form elements wrapped in `className="nodrag nopan"` containers

  **Must NOT do**:
  - Must NOT change the entry's position within its parent group
  - Must NOT create Description as a separate node
  - Must NOT use side panel for editing

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-design`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with 1, 2, 4, 5, 6)
  - **Blocks**: Tasks 7, 10
  - **Blocked By**: Task 1

  **References**:
  - `apps/review-workbench/src/pages/CvGraphEditorPage.tsx:60-100` — `entryLabel()`, `displayCategory()` helpers
  - `apps/review-workbench/src/pages/CvGraphEditorPage.tsx:133-178` — current `makeFlowNode`
  - `apps/review-workbench/src/types/models.ts:CvEntry` — entry shape
  - React Flow custom nodes: `https://reactflow.dev/learn/customization/custom-nodes`
  - `nodrag` class: `https://reactflow.dev/learn/customization/custom-nodes#preventing-drag-behavior`

  **QA Scenarios:**
  ```
  Scenario: Entry node renders compact with category strip and title
    Tool: Playwright
    Steps:
      1. Navigate to /sandbox/cv_graph, wait 3s
      2. Expand Job Experience group
      3. Verify entry nodes show title text and category color strip
      4. Verify NO inline form fields visible
    Expected Result: Compact entry cards with visual category indicator
    Evidence: .sisyphus/evidence/task-3-entry-compact.png

  Scenario: Entry click expands edit panel to the right
    Tool: Playwright
    Steps:
      1. Click "Machine Learning Consultant" entry
      2. Wait 1s
      3. Verify textareas appear (description editing) to the RIGHT of the card
      4. Verify "+" button visible at bottom of descriptions
    Expected Result: Right-expanding edit panel with form fields and add button
    Evidence: .sisyphus/evidence/task-3-entry-expanded.png
  ```

  **Commit**: YES
  - Message: `feat(cv-graph): add EntryNode with compact card and right-expanding edit panel`

---

- [ ] 4. Create SkillBallNode Custom Component

  **What to do**:
  - Create `apps/review-workbench/src/components/cv-graph/SkillBallNode.tsx`
  - Renders as a circle (44px diameter default)
  - **Always-visible label** below or inside the circle (skill name, not hover-only)
  - **Category color** determines the hue (from `CATEGORY_HUES`)
  - **Mastery intensity** determines the lightness (darker = more proficient)
    - Use `masteryColorForCategory(hue, tag)` from mastery-scale module
    - Show mastery level tag as small text below label (e.g., "Advanced" or "C1")
  - Essential skill: subtle glowing ring animation
  - `<Handle type="target" position={Position.Left}>` accepting connections from entry source handles
  - `isValidConnection`: only allow entry→skill connections
  - **Polymorphic shape-ready**: component accepts `data.shape?: "circle" | "diamond" | "square"` prop, defaults to `"circle"`. Only circle is styled now, but the prop exists for future shapes.
  - Tooltip on hover shows full detail: `{label} — {category} — {mastery.label} ({mastery.value}/5)`

  **Must NOT do**:
  - Must NOT hide the label (always visible)
  - Must NOT use the same color for all skills (category-colored)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-design`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 7, 8, 9
  - **Blocked By**: Tasks 1, 2

  **References**:
  - `apps/review-workbench/src/types/models.ts:CvSkill` — skill shape
  - Mastery scale: Task 2 output (`lib/mastery-scale.ts`)
  - React Flow Handle: `https://reactflow.dev/api-reference/components/handle`

  **QA Scenarios:**
  ```
  Scenario: Skill balls render as colored circles with visible names
    Tool: Playwright
    Steps:
      1. Navigate to /sandbox/cv_graph, expand a group, click an entry
      2. Wait 2s for skills to appear
      3. Verify circular skill nodes have visible text labels
      4. Verify different colors for different skill categories
    Expected Result: Colored circles with names and mastery indicators
    Evidence: .sisyphus/evidence/task-4-skill-balls.png
  ```

  **Commit**: YES
  - Message: `feat(cv-graph): add SkillBallNode with mastery intensity and always-visible labels`

---

- [ ] 5. Create GroupNode Custom Component

  **What to do**:
  - Create `apps/review-workbench/src/components/cv-graph/GroupNode.tsx`
  - **MUST preserve** box-in-box nesting: group is a parent container, children positioned relatively inside it
  - Header row: category label + entry count badge + chevron (▶ collapsed / ▼ expanded)
  - Background: category-tinted, slightly transparent
  - **"+" button at bottom**: when clicked, emits `onAddEntry(category)` callback
  - Click on header toggles expand/collapse via callback
  - Children are NOT rendered by GroupNode (React Flow handles child rendering via `parentId`)

  **Must NOT do**:
  - Must NOT change `parentId`, `extent`, or position calculation for children
  - Must NOT manage child layout (React Flow does this)
  - Must NOT make groups draggable

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 7, 10
  - **Blocked By**: Task 1

  **References**:
  - `apps/review-workbench/src/pages/CvGraphEditorPage.tsx:257-330` — current `buildDocumentView` group creation
  - React Flow sub-flows: `https://reactflow.dev/examples/grouping/sub-flows`

  **QA Scenarios:**
  ```
  Scenario: Group nodes show with category header, count, and "+" button
    Tool: Playwright
    Steps:
      1. Navigate to /sandbox/cv_graph
      2. Verify group headers visible (e.g., "Job Experience (6)")
      3. Verify "+" button visible at bottom of expanded groups
    Expected Result: Groups render with header, count badge, and add button
    Evidence: .sisyphus/evidence/task-5-group-nodes.png
  ```

  **Commit**: YES
  - Message: `feat(cv-graph): add GroupNode with "+" add button, preserve box-in-box`

---

- [ ] 6. Update CSS: Tailwind Utilities + Node Component Styles

  **What to do**:
  - Add Tailwind utility classes for node components (using `@apply` or direct classes in TSX)
  - Add CSS for:
    - `.cv-entry-node` — card with left color strip, compact layout
    - `.cv-entry-node__expand-panel` — right-expanding edit area (position: absolute, left: 100%)
    - `.cv-skill-ball` — circular, with mastery-intensity background
    - `.cv-skill-ball__label` — always visible below/inside circle
    - `.cv-group-header` — category header bar with chevron
    - `.cv-add-button` — "+" button at bottom of containers
    - `.cv-skill-palette` — repurposed side panel for unconnected skills
  - Keep existing `.cv-graph-layout`, `.cv-graph-canvas-wrap` styles
  - Remove old `.cv-node-form`, `.cv-link-grid` styles (replaced by inline editing)
  - CSS transitions: entry expand (width 300ms), skill ball hover (scale 150ms)

  **Must NOT do**:
  - Must NOT delete existing `:root` CSS variables
  - Must NOT remove `.cv-graph-canvas-wrap` or `.cv-graph-layout` styles

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-design`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 7, 11
  - **Blocked By**: Task 1

  **Commit**: YES
  - Message: `style(cv-graph): add Tailwind-based node component styles`

---

- [ ] 7. Refactor CvGraphEditorPage: nodeTypes + Repurpose Side Panel

  **What to do**:
  - Register `nodeTypes = { entry: EntryNode, skill: SkillBallNode, group: GroupNode }`
  - Pass to `<ReactFlow nodeTypes={nodeTypes}>`
  - **Repurpose side panel** (`<aside>`):
    - Remove old node editor form
    - Replace with **Skill Palette**: shows all skills NOT connected to the currently focused entry
    - Each skill in palette is a draggable item or small ball that can be dragged onto the canvas
    - Bottom section: graph metadata (entry/skill/demonstrates counts, snapshot, captured_on)
  - **State refactor**:
    - `expandedEntryId: string` — which entry is showing the right-expand edit panel
    - Toggle on entry click (same entry = collapse, different entry = switch)
    - On entry focus: show related skill balls connected via edges, show unrelated skills in side palette
  - Pass update callbacks to custom nodes via `data` props:
    - `data.onToggleExpand: (entryId: string) => void`
    - `data.onUpdateField: (entryId: string, field: string, value: any) => void`
    - `data.onAddDescription: (entryId: string) => void`
    - `data.onToggleGroup: (category: string) => void`
    - `data.onAddEntry: (category: string) => void`
  - `buildDocumentView`: emit nodes with `type: "entry"` / `type: "group"` instead of generic
  - PRESERVE all nesting logic (`parentId`, `extent`, position calculations) exactly as-is

  **Must NOT do**:
  - Must NOT delete the `<aside>` element (repurpose it)
  - Must NOT change group→entry nesting contract
  - Must NOT break existing view switching (document/entry/skill tabs)

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`playwright`, `frontend-design`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (sequential lead)
  - **Blocks**: Tasks 8, 9, 10, 11, 12
  - **Blocked By**: Tasks 1-6

  **QA Scenarios:**
  ```
  Scenario: Page loads with custom nodes and repurposed side panel
    Tool: Playwright
    Steps:
      1. Navigate to /sandbox/cv_graph, wait 3s
      2. Verify group nodes render with custom GroupNode component
      3. Verify side panel exists but shows "Skill Palette" header (not old "Node Editor")
      4. Verify graph metadata still shown (entry/skill/demonstrates counts)
    Expected Result: Custom nodes + skill palette sidebar, no old form editor
    Evidence: .sisyphus/evidence/task-7-custom-nodes.png
  ```

  **Commit**: YES
  - Message: `feat(cv-graph): rewrite editor with nodeTypes, repurpose sidepanel as skill palette`

---

- [ ] 8. Implement onConnect + isValidConnection Skill Matching

  **What to do**:
  - Add `onConnect` to `<ReactFlow>`: creates demonstrates edge when entry→skill connection made
  - Add `isValidConnection` to EntryNode source handle and SkillBallNode target handle
  - Valid: entry↔skill only (bidirectional drag)
  - Invalid: entry↔entry, skill↔skill — rejected
  - Visual feedback: handle glows on valid hover, dims on invalid
  - On new connection: update `graph.demonstrates` state, refresh canvas

  **Must NOT do**:
  - No checkbox-based linking
  - No side panel interaction for linking

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`playwright`]

  **Parallelization**:
  - **Can Run In Parallel**: YES (with 9, 10)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 12
  - **Blocked By**: Tasks 4, 7

  **QA Scenarios:**
  ```
  Scenario: Drag from entry to skill creates edge
    Tool: Playwright
    Steps:
      1. Expand an entry that shows skill balls
      2. Use JS to simulate onConnect event from entry source to skill target
      3. Verify new edge appears
    Expected Result: demonstrates edge created
    Evidence: .sisyphus/evidence/task-8-connect.png
  ```

  **Commit**: YES
  - Message: `feat(cv-graph): connection-based skill matching with type validation`

---

- [ ] 9. Implement Skill Visibility Logic

  **What to do**:
  - When an entry is focused (expanded):
    - **Related skills**: rendered as SkillBallNode circles CONNECTED to the entry via demonstrates edges
    - **Unrelated skills**: listed in the repurposed side panel (skill palette) as a scrollable grid
  - Skill palette in side panel:
    - Shows all skills that are NOT connected to the focused entry
    - Each skill shown as a small colored pill with name + mastery tag
    - Grouped by category with sub-headers
  - When NO entry is focused:
    - Skills are shown inside the "group:skills" box (current behavior, preserved)
  - Transition: when entry focus changes, related skills animate into position, unrelated ones move to palette

  **Must NOT do**:
  - Must NOT show unrelated skills floating on the canvas (they go in the side palette)

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with 8, 10)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 12
  - **Blocked By**: Tasks 2, 4, 7

  **QA Scenarios:**
  ```
  Scenario: Related skills connect to entry, unrelated go to palette
    Tool: Playwright
    Steps:
      1. Click an entry with known skills (Machine Learning Consultant has Airflow, Python, etc.)
      2. Verify skill balls connected to entry on canvas
      3. Verify side panel shows remaining unconnected skills
    Expected Result: Split view — related on canvas, unrelated in palette
    Evidence: .sisyphus/evidence/task-9-skill-split.png
  ```

  **Commit**: YES
  - Message: `feat(cv-graph): split skills between canvas and palette on entry focus`

---

- [ ] 10. Implement Expand/Collapse with Dagre Re-layout

  **What to do**:
  - On entry expand: re-run dagre with updated dimensions
  - Entry expanded width = original (300px) + edit panel (280px) = ~580px for dagre calculation
  - On group toggle: re-run dagre with updated group height (existing behavior, preserve)
  - `useUpdateNodeInternals(id)` after expand to fix handle positions
  - Smooth CSS transitions on position changes (300ms ease)

  **Must NOT do**:
  - Must NOT change entry position within parent group (only group-level repositioning)
  - Must NOT break existing group expand/collapse

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with 8, 9)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 12
  - **Blocked By**: Tasks 3, 5, 7

  **Commit**: YES
  - Message: `feat(cv-graph): dagre re-layout on entry expand/collapse`

---

- [ ] 11. Visual Polish + Accessibility Pass

  **What to do**:
  - Shadows on nodes (Tailwind `shadow-sm`, `shadow-md` on expanded)
  - Hover lift on entries (`hover:-translate-y-0.5 transition`)
  - Skill ball hover: scale up slightly + show full tooltip
  - Focus ring styles for keyboard navigation (Tailwind `ring-2 ring-offset-2`)
  - Edge styling: demonstrates edges use category color, supports edges dashed
  - Verify color contrast ratios on all node types (WCAG AA minimum)
  - Add skeleton loading state while graph fetches

  **Must NOT do**:
  - No gratuitous animations
  - No changing functional behavior

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-design`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 12
  - **Blocked By**: Tasks 7-10

  **Commit**: YES
  - Message: `style(cv-graph): polish shadows, transitions, hover states, accessibility`

---

- [ ] 12. Build + Type-Check + Playwright Validation

  **What to do**:
  - `npm run build` and fix all TypeScript errors
  - LSP diagnostics on all changed files
  - Start API + UI servers
  - Playwright validation of all scenarios from Tasks 3-9
  - Capture evidence screenshots to `.sisyphus/evidence/`
  - Verify zero browser console errors

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`playwright`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (after 11)
  - **Blocks**: Task 13
  - **Blocked By**: Tasks 7-11

  **Commit**: YES (fixes only)
  - Message: `fix(cv-graph): address build/type issues from redesign`

---

- [ ] 13. Update Docs and Changelog

  **What to do**:
  - Update `apps/review-workbench/README.md`: describe custom node architecture, Tailwind, mastery scale
  - Update `changelog.md`: redesign summary
  - Remove stale references to old side panel editing

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: []

  **Commit**: YES
  - Message: `docs(cv-graph): update for inline editing redesign`

---

## Final Verification Wave (MANDATORY)

- [ ] F1. **Plan Compliance Audit** — `oracle`
- [ ] F2. **Code Quality Review** — `unspecified-high`
- [ ] F3. **Real Playwright QA** — `unspecified-high` (+ `playwright` skill)
- [ ] F4. **Scope Fidelity Check** — `deep`

---

## Commit Strategy

| Wave | Message | Key Files |
|------|---------|-----------|
| 1 | `feat(cv-graph): infra + custom node components` | tailwind config, mastery-scale.ts, EntryNode, SkillBallNode, GroupNode, styles.css |
| 2 | `feat(cv-graph): editor integration + connections + skill palette` | CvGraphEditorPage.tsx |
| 3 | `style + docs` | styles.css, README.md, changelog.md |

---

## Success Criteria

### Verification Commands
```bash
npm run build    # Expected: success
pytest tests/ -q # Expected: 74 passed (no backend changes)
```

### Final Checklist
- [ ] Tailwind installed and coexisting with CSS custom properties
- [ ] Box-in-box nesting preserved exactly
- [ ] Custom nodeTypes registered (entry, skill, group)
- [ ] Entry compact mode shows category strip + title + counts
- [ ] Entry click expands edit panel to the RIGHT
- [ ] Descriptions editable inline (not separate nodes)
- [ ] "+" buttons on groups and entries
- [ ] Skill balls: category color × mastery intensity, name always visible
- [ ] Related skills connected on canvas, unrelated in side palette
- [ ] onConnect creates demonstrates edges
- [ ] isValidConnection rejects invalid types
- [ ] Side panel repurposed as skill palette (not deleted)
- [ ] Mastery scale database in lib/mastery-scale.ts
- [ ] Zero TypeScript errors, zero console errors
