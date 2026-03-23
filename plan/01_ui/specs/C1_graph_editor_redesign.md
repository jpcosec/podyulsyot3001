# C1 — Graph Editor Redesign

Three tightly coupled sub-tasks sharing the KnowledgeGraph foundation at `/graph`.

---

## C1-A: Fix `/graph` — Terran theme + sub-flows + Document template

### Problem

`KnowledgeGraph.tsx` uses light pastel `CATEGORY_COLORS` (`#e8d5b7`, `#d5e8b7`, …) as inline `backgroundColor` on node cards. Several `.ne-*` CSS classes also hardcode white/light values:

- `.ne-node-child { background: #fff }`
- `.ne-node-free` — no explicit background, inherits ReactFlow's white injection
- `.ne-section { background: rgba(255,255,255,0.72) }`
- `.ne-section-toggle { background: linear-gradient(180deg,#fff,#f6f3ed) }`
- `.ne-template-chip { background: #f8fbff }`
- ReactFlow's own stylesheet injects `.react-flow__node { background: #fff }` wrapping every custom node

### Color fix

Replace `CATEGORY_COLORS` map in `KnowledgeGraph.tsx` with dark border+bg pairs:

```ts
const CATEGORY_COLORS: Record<string, { border: string; bg: string }> = {
  person:      { border: 'rgba(0,242,255,0.5)',   bg: 'rgba(0,242,255,0.07)' },
  skill:       { border: 'rgba(255,170,0,0.5)',   bg: 'rgba(255,170,0,0.07)' },
  project:     { border: 'rgba(0,242,255,0.25)',  bg: 'rgba(0,242,255,0.04)' },
  publication: { border: 'rgba(255,180,171,0.5)', bg: 'rgba(255,180,171,0.07)' },
  concept:     { border: 'rgba(116,117,120,0.5)', bg: 'rgba(116,117,120,0.07)' },
  document:    { border: 'rgba(0,242,255,0.6)',   bg: 'rgba(0,242,255,0.06)' },
  section:     { border: 'rgba(255,170,0,0.4)',   bg: 'rgba(255,170,0,0.05)' },
  entry:       { border: 'rgba(116,117,120,0.4)', bg: 'rgba(30,32,34,0.9)' },
};
```

`SimpleNodeCard` renders with:
```tsx
style={{
  borderLeft: `4px solid ${color.border}`,
  background: color.bg,
  color: 'var(--text-main)',
}}
```

Fix `styles.css` — replace all hardcoded light backgrounds:
```css
/* Remove white backgrounds */
.react-flow__node              { background: transparent !important; }  /* suppress RF injection */
.ne-node-child                 { background: var(--panel); }
.ne-node-free                  { background: transparent; }  /* let category bg show through */
.ne-section                    { background: rgba(0,242,255,0.03); }
.ne-section-toggle             { background: var(--panel); }
.ne-template-chip              { background: var(--panel); }
```

### Sub-flow support — two new node types

**`GroupNode`** (type `group`): a resizable parent container rendered as a titled frame.
- Header bar: category icon + label + child-count badge + collapse toggle
- Body: transparent fill, dashed border using category border color
- Handles on all 4 sides for external connections
- Nodes with category `document` or `section` automatically get `type: 'group'`

**Drag-onto-group (parentId assignment):** ReactFlow does NOT auto-assign `parentId` on drop. The implementer must:
1. On `onNodeDragStop`, hit-test the dragged node's bounding box against all `GroupNode` bounding boxes
2. If the dragged node center falls inside a group, set `parentId = group.id`, `extent = 'parent'`
3. **Recalculate child position to parent-relative coords**: `child.position = { x: child.absX - group.absX, y: child.absY - group.absY }`
4. On "detach" (drag out of group), reverse: convert back to absolute coords and remove `parentId`

**`SubFlowEdge`**: edges whose source or target is a child node inside a group.
- ReactFlow reports child node positions relative to their parent, not the canvas
- When rendering edge paths, resolve absolute position: `absPos = child.position + parent.position`
- Reuse the existing `FloatingEdge` bezier calculation once absolute positions are resolved
- Register as `edgeTypes: { subflow: SubFlowEdge }` and use it for all edges once sub-flows are enabled

### Document node template

Add to `NODE_TEMPLATES`:
```ts
{ name: 'Document', category: 'document', defaults: { title: 'Untitled', type: 'cv' } },
{ name: 'Section',  category: 'section',  defaults: { title: 'New Section' } },
{ name: 'Entry',    category: 'entry',    defaults: { title: '', date: '' } },
```

When `Document` template is dropped onto canvas, create:
1. A `GroupNode` (type=`document`, size 600×400)
2. Two child `GroupNode`s (type=`section`, parentId=doc) labelled "Introduction" + "Body"
3. One placeholder `Entry` leaf inside each section

Entry nodes have a right-side Handle only — for connecting out to skill/requirement external nodes.

---

## C1-B: CV Editor (`/cv`) — KnowledgeGraph-based

### Goal

Replace `BaseCvEditor` + `CvGraphCanvas` with a seeded KnowledgeGraph. The CV is a Document sub-flow; skills are external nodes connected via edges.

### Data mapping

```
CvProfileGraph              →  KnowledgeGraph
──────────────────────────────────────────────────────────
CV root                     →  GroupNode (type=document, label="My CV")
CvEntry.category            →  GroupNode (type=section, parentId=CV doc)
CvEntry[]                   →  SimpleNode (type=entry, parentId=section)
CvSkill[]                   →  SimpleNode (type=skill, positioned right col)
CvDemonstratesEdge[]        →  SimpleEdge (source=entry.id, target=skill.id)
```

### Round-trip: structured fields

`SimpleNodeData.properties: Record<string, string>` holds only flat strings. `CvEntry.fields` is `Record<string, unknown>` and `CvEntry.descriptions` is a structured `CvDescription[]`.

**Pattern: `meta` passthrough blob**. Extend `SimpleNodeData` with:
```ts
meta?: unknown;  // opaque, not shown in UI, preserved in round-trip
```

`cvProfileToGraph`: store `{ fields: entry.fields, descriptions: entry.descriptions, essential: entry.essential }` in `node.data.meta`. `properties` holds only display-ready flat strings (title/date for the node label).

`graphToCvProfile`: restore `CvEntry.fields` and `CvEntry.descriptions` from `node.data.meta`. If meta is missing (newly created node), initialise with empty defaults.

### Adapter location

```ts
// apps/review-workbench/src/features/base-cv/lib/cvToGraph.ts
export function cvProfileToGraph(data: CvProfileGraphPayload): { nodes: SimpleNode[]; edges: SimpleEdge[] }
export function graphToCvProfile(nodes: SimpleNode[], edges: SimpleEdge[]): CvProfileGraphPayload
```

### BaseCvEditor becomes thin

```tsx
export function BaseCvEditor() {
  const query = useCvProfileGraph();
  const save = useSaveCvGraph();
  const { nodes, edges } = useMemo(() => cvProfileToGraph(query.data!), [query.data]);
  return (
    <KnowledgeGraph
      initialNodes={nodes}
      initialEdges={edges}
      onSave={(n, e) => save.mutate(graphToCvProfile(n, e))}
    />
  );
}
```

`KnowledgeGraph` gets an `onSave?: (nodes: SimpleNode[], edges: SimpleEdge[]) => void` prop. When present, a "Save" button appears in the sidebar.

### Layout on load

- Document group: `x=0, y=0`, width=400
- Section groups: stacked vertically inside, `y = 60 + i*200`
- Entry nodes: inside sections, `y = 50 + j*80`
- Skill nodes: `x = 600`, stacked vertically

---

## C1-C: Match View (`/jobs/.../match`) — KnowledgeGraph-based

### Goal

Replace `MatchGraphCanvas` + the three-panel layout with a seeded KnowledgeGraph in LR 2-column layout.

### Existing data shape (current `GraphNode`)

The current `MatchViewData.nodes: GraphNode[]` has `kind: 'requirement' | 'profile'` but no `category` field. To enable category-based grouping, the mock fixture and API type need a `category` field on both requirement and profile nodes:

```ts
// Extend GraphNode in api.types.ts:
interface GraphNode {
  id: string;
  label: string;
  kind: string;
  category?: string;   // NEW — e.g. "technical", "soft_skills", "languages"
  score?: number;
  data?: Record<string, unknown>;
}
```

Update `mock/fixtures/artifacts_match_*.json` to add `category` to nodes. Existing nodes without a category fall into a default `"general"` group.

### KnowledgeGraph data mapping

```
MatchViewData               →  KnowledgeGraph
────────────────────────────────────────────────────────
GraphNode (kind=requirement)  →  GroupNode (section) per category, left col (x=0)
                                 + SimpleNode (entry) inside section
GraphNode (kind=profile)      →  GroupNode (section) per category, right col (x=600)
                                 + SimpleNode (skill) inside section
GraphEdge[]                   →  SimpleEdge with score label
Unmapped profile nodes        →  SimpleNode floating in UnmappedPanel (x=1000)
```

### Adapters

```ts
// apps/review-workbench/src/features/job-pipeline/lib/matchToGraph.ts
export function matchPayloadToGraph(data: MatchViewData): { nodes: SimpleNode[]; edges: SimpleEdge[] }

// MatchEdits — what the gate receives after review
export interface MatchEdits {
  addedEdges:   Array<{ source: string; target: string }>;
  removedEdges: Array<{ id: string }>;
  addedNodes:   Array<{ id: string; label: string; kind: 'profile'; category: string }>;
}
export function graphToMatchEdits(
  original: MatchViewData,
  nodes: SimpleNode[],
  edges: SimpleEdge[]
): MatchEdits
```

### Unmapped panel

A `<UnmappedSkillsPanel>` component (right rail, collapsible):
- Lists `SimpleNode`s of kind=`profile` that have no edges
- Click → selects node and scrolls canvas to it
- Drag from panel to a requirement node → creates edge, moves skill into mapped column

### Gate

Keep `MatchDecisionModal` — triggered by "DECIDE" button added to the KnowledgeGraph sidebar Actions section. Gate payload stays `GateDecisionPayload`.

---

## Component Map Changes

| File | Change |
|------|--------|
| `styles.css` | Fix 5 hardcoded light `.ne-*` values + `.react-flow__node` override |
| `KnowledgeGraph.tsx` | New `CATEGORY_COLORS`, add `GroupNode`, `SubFlowEdge`, Document template, `onSave` prop |
| `features/base-cv/lib/cvToGraph.ts` | New — adapter functions |
| `pages/global/BaseCvEditor.tsx` | Replaced — thin wrapper |
| `types/api.types.ts` | Add `category?: string` to `GraphNode` |
| `mock/fixtures/artifacts_match_*.json` | Add `category` to requirement/profile nodes |
| `features/job-pipeline/lib/matchToGraph.ts` | New — adapter + `MatchEdits` type |
| `pages/job/Match.tsx` | Use KnowledgeGraph + `UnmappedSkillsPanel` + keep `MatchDecisionModal` |

## Definition of Done

- `/graph` uses only Terran dark tokens — no white/light backgrounds visible
- Sub-flow nodes contain and move with children; drag-in assigns parentId with correct coord transform
- Document template creates 3-level nested structure on canvas drop
- `/cv` loads CV data as nested groups; saves back to `CvProfileGraphPayload` faithfully
- `/match` shows 2-column group layout with score-labeled edges and unmapped skills panel
