# C1 — Graph Editor Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix KnowledgeGraph Terran dark theme, add sub-flow GroupNode, wire CV and Match pages to use KnowledgeGraph as their base editor.

**Architecture:** Three independent tasks sharing KnowledgeGraph.tsx as foundation. C1-A fixes visuals and adds GroupNode/sub-flow support. C1-B creates a CV→graph adapter and replaces BaseCvEditor with a thin KnowledgeGraph wrapper. C1-C creates a match→graph adapter and replaces Match with KnowledgeGraph + UnmappedSkillsPanel.

**Tech Stack:** React 18, TypeScript, @xyflow/react, Terran CSS tokens (`--panel`, `--accent`, `--line`, `--text-main`)

**Spec:** `plan/01_ui/specs/C1_graph_editor_redesign.md`

---

## File Map

| Status | Path | Change |
|--------|------|--------|
| Modify | `apps/review-workbench/src/styles.css` | Fix 5 hardcoded white/light backgrounds |
| Modify | `apps/review-workbench/src/pages/global/KnowledgeGraph.tsx` | New CATEGORY_COLORS, GroupNode, SubFlowEdge, Document template, initialNodes/initialEdges/onSave props |
| Modify | `apps/review-workbench/src/types/api.types.ts` | Add `category?: string` to `GraphNode` |
| Create | `apps/review-workbench/src/features/base-cv/lib/cvToGraph.ts` | Adapter: CvProfileGraphPayload ↔ SimpleNode[]/SimpleEdge[] |
| Modify | `apps/review-workbench/src/pages/global/BaseCvEditor.tsx` | Replace with thin KnowledgeGraph wrapper |
| Modify | `apps/review-workbench/src/mock/fixtures/view_match_201397.json` | Add `category` to nodes |
| Modify | `apps/review-workbench/src/mock/fixtures/view_match_999001.json` | Add `category` to nodes |
| Create | `apps/review-workbench/src/features/job-pipeline/lib/matchToGraph.ts` | Adapter: MatchViewData ↔ SimpleNode[]/SimpleEdge[], MatchEdits type |
| Create | `apps/review-workbench/src/features/job-pipeline/components/UnmappedSkillsPanel.tsx` | Right-rail panel for unmapped profile nodes |
| Modify | `apps/review-workbench/src/pages/job/Match.tsx` | Replace with KnowledgeGraph + UnmappedSkillsPanel + keep MatchDecisionModal |

---

## Task 1: Fix Terran Colors in styles.css

The `.ne-*` CSS classes hardcode light/white backgrounds that clash with the dark Terran theme.

**Files:**
- Modify: `apps/review-workbench/src/styles.css`

- [ ] **Step 1: Replace the 5 offending CSS rules**

In `styles.css`, find and replace these rules exactly:

```css
/* FIND → REPLACE */

/* 1. .ne-section background */
background: rgba(255, 255, 255, 0.72);
/* → */
background: rgba(0, 242, 255, 0.03);

/* 2. .ne-section-toggle background */
background: linear-gradient(180deg, #fff, #f6f3ed);
/* → */
background: var(--panel);

/* 3. .ne-template-chip background */
background: #f8fbff;
/* → */
background: var(--panel);

/* 4. .ne-node-child background */
background: #fff;
/* → */
background: var(--panel);
```

- [ ] **Step 2: Add ReactFlow node background override**

At the end of `styles.css` (after all `.ne-*` rules), add:

```css
/* Suppress ReactFlow's white node background injection */
.react-flow__node { background: transparent !important; }
.ne-node-free     { background: transparent; }
```

- [ ] **Step 3: Verify build**

```bash
cd apps/review-workbench && npm run build 2>&1 | tail -5
```
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add apps/review-workbench/src/styles.css
git commit -m "fix(ui): fix .ne-* light backgrounds for Terran dark theme"
```

---

## Task 2: Fix CATEGORY_COLORS in KnowledgeGraph.tsx

Replace the flat pastel string map with dark border+bg pairs and update SimpleNodeCard rendering.

**Files:**
- Modify: `apps/review-workbench/src/pages/global/KnowledgeGraph.tsx`

- [ ] **Step 1: Replace CATEGORY_COLORS constant**

Find:
```ts
const CATEGORY_COLORS: Record<string, string> = {
  person: "#e8d5b7",
  skill: "#d5e8b7",
  project: "#b7d5e8",
  publication: "#e8b7d5",
  concept: "#d9d6f8",
};
```

Replace with:
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

- [ ] **Step 2: Update SimpleNodeCard to use color.border and color.bg**

Find the `SimpleNodeCard` component (currently around line 445). It currently does:
```ts
const bg = CATEGORY_COLORS[nodeData.category] ?? "#e5e7eb";
```
and renders:
```tsx
style={{ backgroundColor: bg }}
```

Replace those two with:
```ts
const color = CATEGORY_COLORS[nodeData.category] ?? { border: 'rgba(116,117,120,0.4)', bg: 'rgba(30,32,34,0.9)' };
```
and update the `<div>` style:
```tsx
style={{
  borderLeft: `4px solid ${color.border}`,
  background: color.bg,
  color: 'var(--text-main)',
}}
```

- [ ] **Step 3: Extend CATEGORY_OPTIONS and NODE_TEMPLATES**

Find:
```ts
const CATEGORY_OPTIONS = ["person", "skill", "project", "publication", "concept"];
```
Replace with:
```ts
const CATEGORY_OPTIONS = ["person", "skill", "project", "publication", "concept", "document", "section", "entry"];
```

Find `NODE_TEMPLATES` array and add at the end:
```ts
  { name: 'Document', category: 'document', defaults: { title: 'Untitled', type: 'cv' } },
  { name: 'Section',  category: 'section',  defaults: { title: 'New Section' } },
  { name: 'Entry',    category: 'entry',    defaults: { title: '', date: '' } },
```

- [ ] **Step 4: Extend SimpleNodeData with meta passthrough**

Find:
```ts
interface SimpleNodeData extends Record<string, unknown> {
  name: string;
  category: string;
  properties: Record<string, string>;
  nodeId?: string;
  onEditNode?: (nodeId: string) => void;
}
```
Add `meta?: unknown;` as the last field before the closing brace.

- [ ] **Step 5: Verify build**

```bash
cd apps/review-workbench && npm run build 2>&1 | tail -5
```

- [ ] **Step 6: Commit**

```bash
git add apps/review-workbench/src/pages/global/KnowledgeGraph.tsx
git commit -m "fix(ui): replace CATEGORY_COLORS with Terran dark pairs in KnowledgeGraph"
```

---

## Task 3: Add GroupNode + SubFlowEdge + initialNodes/onSave props

Add the `GroupNode` type (resizable parent container), `SubFlowEdge` (resolves absolute child positions), and wire up `initialNodes`/`initialEdges`/`onSave` props so KnowledgeGraph can be used as an embedded editor.

**Files:**
- Modify: `apps/review-workbench/src/pages/global/KnowledgeGraph.tsx`

- [ ] **Step 1: Add GroupNode component**

After the `SimpleNodeCard` component definition and before `const nodeTypes`, add:

```tsx
const GroupNode = memo(function GroupNode({ data, selected }: NodeProps<SimpleNode>) {
  const nodeData = data as unknown as SimpleNodeData;
  const color = CATEGORY_COLORS[nodeData.category] ?? { border: 'rgba(116,117,120,0.4)', bg: 'rgba(30,32,34,0.9)' };
  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        border: `2px dashed ${color.border}`,
        background: color.bg,
        borderRadius: 8,
        position: 'relative',
      }}
    >
      <Handle id="top" type="source" position={Position.Top} className="ne-node-handle" />
      <Handle id="right" type="source" position={Position.Right} className="ne-node-handle" />
      <Handle id="bottom" type="source" position={Position.Bottom} className="ne-node-handle" />
      <Handle id="left" type="source" position={Position.Left} className="ne-node-handle" />
      <div
        style={{
          position: 'absolute',
          top: -20,
          left: 0,
          fontSize: '0.72rem',
          fontWeight: 600,
          color: color.border,
          fontFamily: 'JetBrains Mono, monospace',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          whiteSpace: 'nowrap',
        }}
      >
        {nodeData.name}
      </div>
    </div>
  );
});
```

- [ ] **Step 2: Add SubFlowEdge component**

After `GroupNode`, before `const nodeTypes`:

```tsx
const SubFlowEdge = memo(function SubFlowEdge({ id, source, target, style, markerEnd }: EdgeProps) {
  const sourceNode = useStore((store) => store.nodeLookup.get(source));
  const targetNode = useStore((store) => store.nodeLookup.get(target));

  if (!sourceNode || !targetNode) return null;

  // Resolve absolute positions (child nodes store position relative to parent)
  const getAbsPos = (node: InternalNode) => {
    if (node.parentId) {
      const parent = useStore.getState?.().nodeLookup.get(node.parentId);
      if (parent) {
        return {
          x: (parent.internals?.positionAbsolute?.x ?? 0) + node.position.x,
          y: (parent.internals?.positionAbsolute?.y ?? 0) + node.position.y,
        };
      }
    }
    return node.internals.positionAbsolute;
  };

  const srcAbs = getAbsPos(sourceNode);
  const tgtAbs = getAbsPos(targetNode);

  // Use same floating edge math as FloatingEdge
  const params = getFloatingEdgeParams(
    { ...sourceNode, internals: { ...sourceNode.internals, positionAbsolute: srcAbs } } as InternalNode,
    { ...targetNode, internals: { ...targetNode.internals, positionAbsolute: tgtAbs } } as InternalNode,
  );
  const [path] = getBezierPath({
    sourceX: params.sx,
    sourceY: params.sy,
    sourcePosition: params.sourcePosition,
    targetX: params.tx,
    targetY: params.ty,
    targetPosition: params.targetPosition,
  });

  return (
    <BaseEdge
      id={id}
      path={path}
      style={{ stroke: 'var(--line)', strokeWidth: 1.5, ...style }}
      markerEnd={markerEnd}
    />
  );
});
```

**Note:** `useStore.getState` is not part of the ReactFlow hook API. Use the store hook pattern from `FloatingEdge` instead — both `sourceNode` and `targetNode` already carry `internals.positionAbsolute` which ReactFlow resolves to canvas-absolute for all nodes (including children). So the simpler approach is:

```tsx
const SubFlowEdge = memo(function SubFlowEdge({ id, source, target, style, markerEnd }: EdgeProps) {
  const sourceNode = useStore((store) => store.nodeLookup.get(source));
  const targetNode = useStore((store) => store.nodeLookup.get(target));

  if (!sourceNode || !targetNode) return null;

  // ReactFlow stores positionAbsolute (canvas coords) for all nodes including children
  const params = getFloatingEdgeParams(sourceNode, targetNode);
  const [path] = getBezierPath({
    sourceX: params.sx,
    sourceY: params.sy,
    sourcePosition: params.sourcePosition,
    targetX: params.tx,
    targetY: params.ty,
    targetPosition: params.targetPosition,
  });

  return (
    <BaseEdge
      id={id}
      path={path}
      style={{ stroke: 'var(--line)', strokeWidth: 1.5, ...style }}
      markerEnd={markerEnd}
    />
  );
});
```

- [ ] **Step 3: Register GroupNode in nodeTypes and SubFlowEdge in edgeTypes**

Find:
```ts
const nodeTypes: NodeTypes = {
  simple: SimpleNodeCard,
};
```
Replace with:
```ts
const nodeTypes: NodeTypes = {
  simple: SimpleNodeCard,
  group: GroupNode,
};
```

Find the `edgeTypes` definition (search for `edgeTypes`) and add `subflow: SubFlowEdge`. If it doesn't exist yet, add after `nodeTypes`:
```ts
const edgeTypes = {
  floating: FloatingEdge,
  subflow: SubFlowEdge,
};
```
Then pass `edgeTypes={edgeTypes}` to the `<ReactFlow>` component (look for where `FloatingEdge` is passed).

- [ ] **Step 4: Add initialNodes/initialEdges/onSave props to KnowledgeGraph**

Find the `KnowledgeGraph` function signature (search for `export function KnowledgeGraph` or `function KnowledgeGraph`). Add props:

```tsx
interface KnowledgeGraphProps {
  initialNodes?: SimpleNode[];
  initialEdges?: SimpleEdge[];
  onSave?: (nodes: SimpleNode[], edges: SimpleEdge[]) => void;
}

function KnowledgeGraphInner({ initialNodes, initialEdges, onSave }: KnowledgeGraphProps) {
```

Inside the component, find where `buildInitialGraph()` is called (typically in a `useState` initializer). Change it to use the prop when provided:

```ts
const [nodes, setNodes, onNodesChange] = useNodesState(
  initialNodes ?? buildInitialGraph().nodes
);
const [edges, setEdges, onEdgesChange] = useEdgesState(
  initialEdges ?? buildInitialGraph().edges
);
```

- [ ] **Step 5: Wire onSave to sidebar Save button**

Find the sidebar in KnowledgeGraph. Search for a Save button or Ctrl+S handler. In the Actions section, add a Save button that calls `onSave?.(nodes, edges)` when `onSave` is present:

In the keyboard shortcut handler (search for `ctrlKey && key === 's'`), after the existing logic, add:
```ts
if (e.ctrlKey && e.key === 's' && onSave) {
  e.preventDefault();
  onSave(nodes, edges);
}
```

In the sidebar Actions section, conditionally render:
```tsx
{onSave && (
  <button className="ne-btn ne-btn-primary" onClick={() => onSave(nodes, edges)}>
    Save
  </button>
)}
```

- [ ] **Step 6: Add Document template expansion logic**

Find where template nodes are created (search for `NODE_TEMPLATES` usage in the drop handler — likely `onDrop` or a drag-from-template handler). When the dropped template has `category === 'document'`, instead of creating one node, create the 3-level structure:

```ts
if (template.category === 'document') {
  const docId = createEntityId('doc');
  const sec1Id = createEntityId('sec');
  const sec2Id = createEntityId('sec');
  const ent1Id = createEntityId('entry');
  const ent2Id = createEntityId('entry');

  const newNodes: SimpleNode[] = [
    {
      id: docId,
      type: 'group',
      position: dropPosition,
      style: { width: 600, height: 400 },
      data: { name: 'Untitled CV', category: 'document', properties: { type: 'cv' } },
    },
    {
      id: sec1Id,
      type: 'group',
      parentId: docId,
      extent: 'parent',
      position: { x: 20, y: 60 },
      style: { width: 560, height: 160 },
      data: { name: 'Introduction', category: 'section', properties: {} },
    },
    {
      id: sec2Id,
      type: 'group',
      parentId: docId,
      extent: 'parent',
      position: { x: 20, y: 240 },
      style: { width: 560, height: 140 },
      data: { name: 'Body', category: 'section', properties: {} },
    },
    {
      id: ent1Id,
      type: 'simple',
      parentId: sec1Id,
      extent: 'parent',
      position: { x: 20, y: 50 },
      data: { name: 'Entry 1', category: 'entry', properties: { date: '' } },
    },
    {
      id: ent2Id,
      type: 'simple',
      parentId: sec2Id,
      extent: 'parent',
      position: { x: 20, y: 50 },
      data: { name: 'Entry 2', category: 'entry', properties: { date: '' } },
    },
  ];
  setNodes(prev => [...prev, ...newNodes]);
  return;
}
```

- [ ] **Step 7: Verify build**

```bash
cd apps/review-workbench && npm run build 2>&1 | tail -5
```

- [ ] **Step 8: Commit**

```bash
git add apps/review-workbench/src/pages/global/KnowledgeGraph.tsx
git commit -m "feat(ui): add GroupNode, SubFlowEdge, Document template, initialNodes/onSave props to KnowledgeGraph"
```

---

## Task 4: C1-B — Create cvToGraph adapter

Create the adapter that converts `CvProfileGraphPayload` ↔ `SimpleNode[]`/`SimpleEdge[]`. The `meta` passthrough preserves structured `CvEntry` fields and descriptions across the round-trip.

**Files:**
- Create: `apps/review-workbench/src/features/base-cv/lib/cvToGraph.ts`

Import paths to use:
- `type { SimpleNode, SimpleEdge }` from the KnowledgeGraph file need to be exported first (see Step 0 below)

- [ ] **Step 0: Export SimpleNode, SimpleEdge, SimpleNodeData, SimpleEdgeData from KnowledgeGraph.tsx**

Add `export` before these four type/interface declarations in KnowledgeGraph.tsx:
- `export interface SimpleNodeData`
- `export interface SimpleEdgeData`
- `export type SimpleNode`
- `export type SimpleEdge`

- [ ] **Step 1: Create the adapter file**

```ts
// apps/review-workbench/src/features/base-cv/lib/cvToGraph.ts
import type { CvProfileGraphPayload, CvEntry, CvSkill } from '../../../types/api.types';
import type { SimpleNode, SimpleEdge } from '../../../pages/global/KnowledgeGraph';

function entryId(id: string) { return `entry:${id}`; }
function skillId(id: string) { return `skill:${id}`; }
function sectionId(cat: string) { return `section:${cat}`; }

export function cvProfileToGraph(data: CvProfileGraphPayload): { nodes: SimpleNode[]; edges: SimpleEdge[] } {
  const nodes: SimpleNode[] = [];
  const edges: SimpleEdge[] = [];

  // Document root group
  const docId = 'doc:root';
  nodes.push({
    id: docId,
    type: 'group',
    position: { x: 0, y: 0 },
    style: { width: 440, height: 60 },  // height expanded dynamically by content
    data: { name: 'My CV', category: 'document', properties: {} },
  });

  // Group entries by category
  const byCategory = new Map<string, CvEntry[]>();
  for (const entry of data.entries) {
    const arr = byCategory.get(entry.category) ?? [];
    arr.push(entry);
    byCategory.set(entry.category, arr);
  }

  let sectionY = 0;
  let skillY = 0;
  const categoryList = Array.from(byCategory.keys());

  for (let ci = 0; ci < categoryList.length; ci++) {
    const cat = categoryList[ci]!;
    const catEntries = byCategory.get(cat)!;
    const secId = sectionId(cat);

    const sectionHeight = 60 + catEntries.length * 80;

    nodes.push({
      id: secId,
      type: 'group',
      parentId: docId,
      extent: 'parent',
      position: { x: 20, y: 60 + sectionY },
      style: { width: 400, height: sectionHeight },
      data: { name: cat, category: 'section', properties: {} },
    });

    sectionY += sectionHeight + 16;

    for (let ei = 0; ei < catEntries.length; ei++) {
      const entry = catEntries[ei]!;
      const eId = entryId(entry.id);
      const title = String(entry.fields['title'] ?? entry.id);
      const date = String(entry.fields['date'] ?? entry.fields['start_date'] ?? '');

      nodes.push({
        id: eId,
        type: 'simple',
        parentId: secId,
        extent: 'parent',
        position: { x: 20, y: 50 + ei * 80 },
        data: {
          name: title,
          category: 'entry',
          properties: { date },
          meta: {
            originalId: entry.id,
            fields: entry.fields,
            descriptions: entry.descriptions,
            essential: entry.essential,
          },
        },
      });
    }
  }

  // Update docId height to fit all sections
  const docNode = nodes.find(n => n.id === docId)!;
  (docNode.style as Record<string, unknown>)['height'] = 80 + sectionY;

  // Skill nodes (right column)
  for (let si = 0; si < data.skills.length; si++) {
    const skill = data.skills[si]!;
    const sId = skillId(skill.id);
    nodes.push({
      id: sId,
      type: 'simple',
      position: { x: 600, y: skillY },
      data: {
        name: skill.label,
        category: 'skill',
        properties: { level: skill.level ?? '', category: skill.category },
        meta: { originalId: skill.id, essential: skill.essential, skillMeta: skill.meta },
      },
    });
    skillY += 70;
  }

  // Demonstrates edges
  for (const d of data.demonstrates) {
    edges.push({
      id: `demonstrates:${d.id}`,
      source: entryId(d.source),
      target: skillId(d.target),
      type: 'subflow',
      data: { relationType: 'demonstrates', properties: {} },
    });
  }

  return { nodes, edges };
}

export function graphToCvProfile(
  nodes: SimpleNode[],
  edges: SimpleEdge[],
  original: CvProfileGraphPayload,
): CvProfileGraphPayload {
  const entries: CvEntry[] = nodes
    .filter(n => n.data.category === 'entry')
    .map(n => {
      const meta = n.data.meta as { originalId?: string; fields?: Record<string, unknown>; descriptions?: CvEntry['descriptions']; essential?: boolean } | undefined;
      return {
        id: meta?.originalId ?? n.id.replace('entry:', ''),
        category: n.parentId
          ? nodes.find(p => p.id === n.parentId)?.data.name ?? 'general'
          : 'general',
        essential: meta?.essential ?? false,
        fields: meta?.fields ?? { title: n.data.name },
        descriptions: meta?.descriptions ?? [],
      };
    });

  const skills: CvSkill[] = nodes
    .filter(n => n.data.category === 'skill')
    .map(n => {
      const meta = n.data.meta as { originalId?: string; essential?: boolean; skillMeta?: Record<string, unknown> } | undefined;
      return {
        id: meta?.originalId ?? n.id.replace('skill:', ''),
        label: n.data.name,
        category: n.data.properties['category'] ?? 'general',
        essential: meta?.essential ?? false,
        level: n.data.properties['level'] || null,
        meta: meta?.skillMeta ?? {},
      };
    });

  const demonstrates = edges
    .filter(e => e.data?.relationType === 'demonstrates')
    .map(e => ({
      id: e.id.replace('demonstrates:', ''),
      source: e.source.replace('entry:', ''),
      target: e.target.replace('skill:', ''),
      description_keys: [],
    }));

  return {
    ...original,
    entries,
    skills,
    demonstrates,
  };
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd apps/review-workbench && npm run build 2>&1 | grep -E "error|warning" | head -20
```
Expected: no type errors.

- [ ] **Step 3: Commit**

```bash
git add apps/review-workbench/src/features/base-cv/lib/cvToGraph.ts apps/review-workbench/src/pages/global/KnowledgeGraph.tsx
git commit -m "feat(ui): add cvToGraph adapter with meta passthrough"
```

---

## Task 5: C1-B — Refactor BaseCvEditor as thin KnowledgeGraph wrapper

Replace the complex 376-line `BaseCvEditor.tsx` with a thin wrapper that uses `KnowledgeGraph` with the CV adapter.

**Files:**
- Modify: `apps/review-workbench/src/pages/global/BaseCvEditor.tsx`

- [ ] **Step 1: Replace BaseCvEditor.tsx entirely**

```tsx
// apps/review-workbench/src/pages/global/BaseCvEditor.tsx
import { useMemo } from 'react';
import { useCvProfileGraph, useSaveCvGraph } from '../../features/base-cv/api/useCvProfileGraph';
import { cvProfileToGraph, graphToCvProfile } from '../../features/base-cv/lib/cvToGraph';
import { KnowledgeGraph } from './KnowledgeGraph';
import { Spinner } from '../../components/atoms/Spinner';
import type { SimpleNode, SimpleEdge } from './KnowledgeGraph';

export function BaseCvEditor() {
  const query = useCvProfileGraph();
  const saveMutation = useSaveCvGraph();

  const { nodes, edges } = useMemo(
    () => query.data ? cvProfileToGraph(query.data) : { nodes: [], edges: [] },
    [query.data],
  );

  const handleSave = (savedNodes: SimpleNode[], savedEdges: SimpleEdge[]) => {
    if (!query.data) return;
    saveMutation.mutate(graphToCvProfile(savedNodes, savedEdges, query.data));
  };

  if (query.isLoading) {
    return <div className="flex items-center justify-center h-full"><Spinner size="md" /></div>;
  }

  if (query.isError || !query.data) {
    return (
      <div className="p-6">
        <p className="font-mono text-error text-sm">CV_PROFILE_GRAPH_NOT_FOUND</p>
      </div>
    );
  }

  return (
    <KnowledgeGraph
      initialNodes={nodes}
      initialEdges={edges}
      onSave={handleSave}
    />
  );
}
```

- [ ] **Step 2: Check that KnowledgeGraph is exported**

In `KnowledgeGraph.tsx`, verify the main function is exported. If it's wrapped in `ReactFlowProvider` and the outer function is named `KnowledgeGraph`, ensure it's exported with `export`.

- [ ] **Step 3: Verify build**

```bash
cd apps/review-workbench && npm run build 2>&1 | tail -10
```
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add apps/review-workbench/src/pages/global/BaseCvEditor.tsx
git commit -m "feat(ui): replace BaseCvEditor with thin KnowledgeGraph wrapper (C1-B)"
```

---

## Task 6: C1-C — Add category to GraphNode and match fixtures

The match view requires grouping nodes by category. `GraphNode` currently has no `category` field.

**Files:**
- Modify: `apps/review-workbench/src/types/api.types.ts`
- Modify: `apps/review-workbench/src/mock/fixtures/view_match_201397.json`
- Modify: `apps/review-workbench/src/mock/fixtures/view_match_999001.json`

- [ ] **Step 1: Add category field to GraphNode**

In `api.types.ts`, find:
```ts
export interface GraphNode {
  id: string;
  label: string;
  kind: string;
  score?: number;
  priority?: string;
}
```
Add `category?: string;` after `kind`:
```ts
export interface GraphNode {
  id: string;
  label: string;
  kind: string;
  category?: string;
  score?: number;
  priority?: string;
}
```

- [ ] **Step 2: Update view_match_201397.json — add category to requirement nodes**

Open the file. Add `"category"` field to each requirement node. Use these category assignments:

```
degree_psychology_neuroscience      → "qualifications"
exp_programming_experiments         → "technical"
exp_statistical_analysis_R          → "technical"
exp_eeg_data                        → "technical"
ability_independent_scientific_work → "soft_skills"
exp_eye_tracking_data               → "technical"
skills_scientific_writing_presentation → "communication"
knowledge_english                   → "languages"
willingness_teamwork_international  → "soft_skills"
exp_ethics_approval                 → "qualifications"
motivation_empirical_research       → "soft_skills"
ability_teamworking                 → "soft_skills"
readiness_open_science              → "qualifications"
interest_human_machine_interaction  → "technical"
```

For profile nodes:
```
P_EDU_001  → "education"
P_EXP_005  → "experience"
P_EXP_006  → "experience"
P_EXP_007  → "experience"
P_EXP_012  → "experience"
P_SKL_021  → "skills"
P_SKL_022  → "skills"
P_PUB_019  → "publications"
P_PUB_020  → "publications"
P_LNG_026  → "languages"
```

- [ ] **Step 3: Update view_match_999001.json similarly**

Read the file and add matching `"category"` fields to all nodes. Use the same category vocabulary (`"technical"`, `"soft_skills"`, `"qualifications"`, `"languages"`, `"education"`, `"experience"`, `"skills"`, `"publications"`, `"communication"`).

- [ ] **Step 4: Verify build**

```bash
cd apps/review-workbench && npm run build 2>&1 | tail -5
```

- [ ] **Step 5: Commit**

```bash
git add apps/review-workbench/src/types/api.types.ts \
        apps/review-workbench/src/mock/fixtures/view_match_201397.json \
        apps/review-workbench/src/mock/fixtures/view_match_999001.json
git commit -m "feat(ui): add category field to GraphNode and match fixtures (C1-C)"
```

---

## Task 7: C1-C — Create matchToGraph adapter

Convert `MatchViewData` to the 2-column grouped KnowledgeGraph layout.

**Files:**
- Create: `apps/review-workbench/src/features/job-pipeline/lib/matchToGraph.ts`

- [ ] **Step 1: Create the adapter**

```ts
// apps/review-workbench/src/features/job-pipeline/lib/matchToGraph.ts
import type { MatchViewData, GraphNode as ApiGraphNode, GraphEdge as ApiGraphEdge } from '../../../types/api.types';
import type { SimpleNode, SimpleEdge } from '../../../pages/global/KnowledgeGraph';

export interface MatchEdits {
  addedEdges:   Array<{ source: string; target: string }>;
  removedEdges: Array<{ id: string }>;
  addedNodes:   Array<{ id: string; label: string; kind: 'profile'; category: string }>;
}

const LEFT_X = 0;
const RIGHT_X = 700;
const GROUP_WIDTH = 380;
const GROUP_HEADER = 40;
const ITEM_HEIGHT = 56;
const GROUP_GAP = 20;
const ITEM_PADDING = 8;

function groupByCategory(nodes: ApiGraphNode[]): Map<string, ApiGraphNode[]> {
  const map = new Map<string, ApiGraphNode[]>();
  for (const node of nodes) {
    const cat = node.category ?? 'general';
    const arr = map.get(cat) ?? [];
    arr.push(node);
    map.set(cat, arr);
  }
  return map;
}

export function matchPayloadToGraph(data: MatchViewData): { nodes: SimpleNode[]; edges: SimpleEdge[] } {
  const nodes: SimpleNode[] = [];
  const edges: SimpleEdge[] = [];

  const reqNodes = data.nodes.filter(n => n.kind === 'requirement');
  const profNodes = data.nodes.filter(n => n.kind === 'profile');

  const reqByCategory = groupByCategory(reqNodes);
  const profByCategory = groupByCategory(profNodes);

  // Build requirement groups (left column)
  let leftY = 0;
  for (const [cat, items] of reqByCategory) {
    const groupId = `req-group:${cat}`;
    const groupHeight = GROUP_HEADER + items.length * ITEM_HEIGHT + ITEM_PADDING;

    nodes.push({
      id: groupId,
      type: 'group',
      position: { x: LEFT_X, y: leftY },
      style: { width: GROUP_WIDTH, height: groupHeight },
      data: { name: cat, category: 'section', properties: { side: 'requirement' } },
    });

    for (let i = 0; i < items.length; i++) {
      const item = items[i]!;
      nodes.push({
        id: item.id,
        type: 'simple',
        parentId: groupId,
        extent: 'parent',
        position: { x: ITEM_PADDING, y: GROUP_HEADER + i * ITEM_HEIGHT },
        data: {
          name: item.label,
          category: 'entry',
          properties: { priority: item.priority ?? '', kind: 'requirement' },
          meta: { originalId: item.id, kind: 'requirement', category: cat },
        },
      });
    }

    leftY += groupHeight + GROUP_GAP;
  }

  // Build profile groups (right column)
  let rightY = 0;
  for (const [cat, items] of profByCategory) {
    const groupId = `prof-group:${cat}`;
    const groupHeight = GROUP_HEADER + items.length * ITEM_HEIGHT + ITEM_PADDING;

    nodes.push({
      id: groupId,
      type: 'group',
      position: { x: RIGHT_X, y: rightY },
      style: { width: GROUP_WIDTH, height: groupHeight },
      data: { name: cat, category: 'section', properties: { side: 'profile' } },
    });

    for (let i = 0; i < items.length; i++) {
      const item = items[i]!;
      nodes.push({
        id: item.id,
        type: 'simple',
        parentId: groupId,
        extent: 'parent',
        position: { x: ITEM_PADDING, y: GROUP_HEADER + i * ITEM_HEIGHT },
        data: {
          name: item.label,
          category: 'skill',
          properties: { score: String(item.score ?? ''), kind: 'profile' },
          meta: { originalId: item.id, kind: 'profile', category: cat },
        },
      });
    }

    rightY += groupHeight + GROUP_GAP;
  }

  // Edges
  for (const edge of data.edges) {
    edges.push({
      id: `match:${edge.source}->${edge.target}`,
      source: edge.source,
      target: edge.target,
      type: 'subflow',
      label: edge.score != null ? String(Math.round(edge.score * 100)) + '%' : undefined,
      data: {
        relationType: 'matched_by',
        properties: {
          score: String(edge.score ?? ''),
          reasoning: edge.reasoning ?? '',
        },
      },
    });
  }

  return { nodes, edges };
}

export function graphToMatchEdits(
  original: MatchViewData,
  nodes: SimpleNode[],
  edges: SimpleEdge[],
): MatchEdits {
  const originalEdgeIds = new Set(
    original.edges.map(e => `${e.source}->${e.target}`)
  );
  const currentEdgeIds = new Set(
    edges
      .filter(e => e.data?.relationType === 'matched_by')
      .map(e => `${e.source}->${e.target}`)
  );
  const originalNodeIds = new Set(original.nodes.map(n => n.id));

  const addedEdges = edges
    .filter(e => e.data?.relationType === 'matched_by' && !originalEdgeIds.has(`${e.source}->${e.target}`))
    .map(e => ({ source: e.source, target: e.target }));

  const removedEdges = original.edges
    .filter(e => !currentEdgeIds.has(`${e.source}->${e.target}`))
    .map(e => ({ id: `match:${e.source}->${e.target}` }));

  const addedNodes = nodes
    .filter(n => n.data.properties['kind'] === 'profile' && !originalNodeIds.has(n.id))
    .map(n => ({
      id: n.id,
      label: n.data.name,
      kind: 'profile' as const,
      category: n.data.meta
        ? (n.data.meta as { category: string }).category
        : 'general',
    }));

  return { addedEdges, removedEdges, addedNodes };
}
```

- [ ] **Step 2: Verify build**

```bash
cd apps/review-workbench && npm run build 2>&1 | grep -E "error" | head -20
```

- [ ] **Step 3: Commit**

```bash
git add apps/review-workbench/src/features/job-pipeline/lib/matchToGraph.ts
git commit -m "feat(ui): add matchToGraph adapter with MatchEdits type (C1-C)"
```

---

## Task 8: C1-C — Create UnmappedSkillsPanel

A collapsible right-rail panel that lists profile nodes with no edges.

**Files:**
- Create: `apps/review-workbench/src/features/job-pipeline/components/UnmappedSkillsPanel.tsx`

- [ ] **Step 1: Create the component**

```tsx
// apps/review-workbench/src/features/job-pipeline/components/UnmappedSkillsPanel.tsx
import { useState } from 'react';
import { cn } from '../../../utils/cn';
import type { SimpleNode } from '../../../pages/global/KnowledgeGraph';

interface Props {
  unmappedNodes: SimpleNode[];
  onSelectNode: (nodeId: string) => void;
}

export function UnmappedSkillsPanel({ unmappedNodes, onSelectNode }: Props) {
  const [collapsed, setCollapsed] = useState(false);

  if (collapsed) {
    return (
      <div className="w-8 border-l border-outline/20 bg-surface flex flex-col items-center pt-3 cursor-pointer"
           onClick={() => setCollapsed(false)}>
        <span className="font-mono text-[9px] text-on-muted rotate-90 whitespace-nowrap mt-4">
          UNMAPPED ({unmappedNodes.length})
        </span>
      </div>
    );
  }

  return (
    <aside className="w-64 border-l border-outline/20 bg-surface flex flex-col overflow-hidden shrink-0">
      <div className="flex items-center justify-between px-3 py-2 border-b border-outline/20">
        <span className="font-mono text-[10px] text-on-muted uppercase tracking-widest">
          Unmapped ({unmappedNodes.length})
        </span>
        <button
          onClick={() => setCollapsed(true)}
          className="font-mono text-[10px] text-on-muted/60 hover:text-on-muted"
        >
          ›
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-1">
        {unmappedNodes.length === 0 ? (
          <p className="font-mono text-[10px] text-on-muted/60 p-2">All skills mapped</p>
        ) : (
          unmappedNodes.map(node => (
            <button
              key={node.id}
              onClick={() => onSelectNode(node.id)}
              className={cn(
                'text-left px-2 py-1.5 border border-outline/20',
                'font-mono text-[11px] text-on-surface hover:border-primary/40',
                'hover:bg-primary/5 transition-colors',
              )}
            >
              {node.data.name}
              {node.data.properties['score'] && (
                <span className="ml-1 text-on-muted/60">{node.data.properties['score']}</span>
              )}
            </button>
          ))
        )}
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/review-workbench/src/features/job-pipeline/components/UnmappedSkillsPanel.tsx
git commit -m "feat(ui): add UnmappedSkillsPanel component (C1-C)"
```

---

## Task 9: C1-C — Refactor Match.tsx to use KnowledgeGraph

Replace `MatchGraphCanvas` + search toolbar with `KnowledgeGraph` seeded from `matchPayloadToGraph`. Keep `MatchDecisionModal`.

**Files:**
- Modify: `apps/review-workbench/src/pages/job/Match.tsx`

- [ ] **Step 1: Replace Match.tsx**

```tsx
// apps/review-workbench/src/pages/job/Match.tsx
import { useState, useMemo, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useViewMatch } from '../../features/job-pipeline/api/useViewMatch';
import { useGateDecide } from '../../features/job-pipeline/api/useGateDecide';
import { KnowledgeGraph } from '../global/KnowledgeGraph';
import { UnmappedSkillsPanel } from '../../features/job-pipeline/components/UnmappedSkillsPanel';
import { MatchDecisionModal } from '../../features/job-pipeline/components/MatchDecisionModal';
import { Spinner } from '../../components/atoms/Spinner';
import { matchPayloadToGraph, graphToMatchEdits } from '../../features/job-pipeline/lib/matchToGraph';
import type { GateDecisionPayload } from '../../types/api.types';
import type { SimpleNode, SimpleEdge } from '../global/KnowledgeGraph';

export function Match() {
  const { source, jobId } = useParams<{ source: string; jobId: string }>();
  const matchQuery = useViewMatch(source!, jobId!);
  const gateDecide = useGateDecide(source!, jobId!, 'review_match');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentNodes, setCurrentNodes] = useState<SimpleNode[]>([]);
  const [currentEdges, setCurrentEdges] = useState<SimpleEdge[]>([]);

  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (matchQuery.data?.view === 'match') {
      return matchPayloadToGraph(matchQuery.data.data);
    }
    return { nodes: [], edges: [] };
  }, [matchQuery.data]);

  const unmappedNodes = useMemo(() => {
    const mappedTargets = new Set(currentEdges.map(e => e.target));
    return currentNodes.filter(
      n => n.data.properties['kind'] === 'profile' &&
           n.type === 'simple' &&
           !mappedTargets.has(n.id)
    );
  }, [currentNodes, currentEdges]);

  const handleGraphChange = useCallback((nodes: SimpleNode[], edges: SimpleEdge[]) => {
    setCurrentNodes(nodes);
    setCurrentEdges(edges);
  }, []);

  const handleSelectUnmapped = useCallback((_nodeId: string) => {
    // KnowledgeGraph doesn't expose a programmatic select yet — no-op for now
  }, []);

  const handleDecide = (payload: GateDecisionPayload) => {
    gateDecide.mutate(payload, {
      onSuccess: () => setIsModalOpen(false),
    });
  };

  if (matchQuery.isLoading) {
    return <div className="flex items-center justify-center h-full"><Spinner size="md" /></div>;
  }

  if (matchQuery.isError || !matchQuery.data || matchQuery.data.view !== 'match') {
    return <div className="p-6"><p className="font-mono text-error text-sm">MATCH_DATA_NOT_FOUND</p></div>;
  }

  return (
    <div className="flex h-full overflow-hidden">
      <div className="flex-1 min-w-0">
        <KnowledgeGraph
          initialNodes={initialNodes}
          initialEdges={initialEdges}
          onSave={handleGraphChange}
        />
      </div>

      <UnmappedSkillsPanel
        unmappedNodes={unmappedNodes}
        onSelectNode={handleSelectUnmapped}
      />

      <MatchDecisionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onDecide={handleDecide}
        isLoading={gateDecide.isPending}
      />
    </div>
  );
}
```

**Note:** The "DECIDE" button to open the modal needs to be accessible. Since KnowledgeGraph has its own sidebar, add a floating DECIDE button at the bottom of the left edge of the Match layout as a temporary measure:

```tsx
{/* Floating DECIDE button */}
<button
  onClick={() => setIsModalOpen(true)}
  className="absolute bottom-6 left-6 z-50 font-mono text-[11px] tracking-widest border border-primary/60 text-primary bg-surface px-4 py-2 hover:bg-primary/10 transition-colors"
>
  DECIDE
</button>
```

Wrap the outer `<div>` with `className="relative flex h-full overflow-hidden"` for positioning.

- [ ] **Step 2: Add KnowledgeGraph onChange callback**

`KnowledgeGraph` doesn't have an `onChange` prop yet. For the unmapped panel to work, we need live node/edge state. Add an `onChange?: (nodes: SimpleNode[], edges: SimpleEdge[]) => void` prop to `KnowledgeGraph`:

In KnowledgeGraph.tsx, add `onChange?` to `KnowledgeGraphProps`:
```ts
interface KnowledgeGraphProps {
  initialNodes?: SimpleNode[];
  initialEdges?: SimpleEdge[];
  onSave?: (nodes: SimpleNode[], edges: SimpleEdge[]) => void;
  onChange?: (nodes: SimpleNode[], edges: SimpleEdge[]) => void;
}
```

Then in the `onNodesChange`/`onEdgesChange` handlers, call `onChange?.(nodes, edges)` after each change. The simplest approach: add a `useEffect` that fires whenever `nodes` or `edges` changes:

```ts
useEffect(() => {
  onChange?.(nodes, edges);
}, [nodes, edges, onChange]);
```

- [ ] **Step 3: Verify build**

```bash
cd apps/review-workbench && npm run build 2>&1 | tail -10
```
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add apps/review-workbench/src/pages/job/Match.tsx \
        apps/review-workbench/src/pages/global/KnowledgeGraph.tsx
git commit -m "feat(ui): replace Match page with KnowledgeGraph + UnmappedSkillsPanel (C1-C)"
```

---

## Task 10: Final verification + changelog

- [ ] **Step 1: Production build check**

```bash
cd apps/review-workbench && npm run build && npm run preview -- --port 5175
```
Open http://localhost:5175/graph — verify dark theme (no white nodes).
Open http://localhost:5175/cv — verify CV loads as KnowledgeGraph with nested groups.
Open http://localhost:5175/jobs/tu_berlin/201397/match — verify 2-column layout.

- [ ] **Step 2: Update index_checklist.md**

Add a new phase entry for C1:

```markdown
### Fase C1 — Graph Editor Redesign ✅
- [x] `styles.css` — fix 5 hardcoded light `.ne-*` values + `.react-flow__node` override
- [x] `KnowledgeGraph.tsx` — new CATEGORY_COLORS dark pairs, GroupNode, SubFlowEdge, Document template, initialNodes/initialEdges/onSave/onChange props
- [x] `features/base-cv/lib/cvToGraph.ts` — adapter functions with meta passthrough
- [x] `pages/global/BaseCvEditor.tsx` — thin KnowledgeGraph wrapper
- [x] `types/api.types.ts` — add `category?: string` to `GraphNode`
- [x] `mock/fixtures/view_match_*.json` — add `category` to nodes
- [x] `features/job-pipeline/lib/matchToGraph.ts` — adapter + MatchEdits type
- [x] `features/job-pipeline/components/UnmappedSkillsPanel.tsx` — collapsible right rail
- [x] `pages/job/Match.tsx` — KnowledgeGraph-based with UnmappedSkillsPanel + MatchDecisionModal
```

- [ ] **Step 3: Update changelog.md**

Add entry at top of changelog:

```markdown
## C1 — Graph Editor Redesign (2026-03-23)

### C1-A: KnowledgeGraph Terran Theme Fix + Sub-flows + Document Template
- Replaced light pastel CATEGORY_COLORS with Terran dark border+bg pairs
- Fixed 5 hardcoded white/light `.ne-*` CSS classes + ReactFlow node background override
- Added `GroupNode` (resizable titled frame, dashed border, category colors)
- Added `SubFlowEdge` (resolves absolute positions from ReactFlow store)
- Added `document`, `section`, `entry` to CATEGORY_OPTIONS and NODE_TEMPLATES
- Document template creates 3-level Document→Section(×2)→Entry nested structure on canvas drop
- Added `meta?: unknown` passthrough to `SimpleNodeData` for round-trip preservation
- Added `initialNodes`, `initialEdges`, `onSave`, `onChange` props to `KnowledgeGraph`

### C1-B: CV Editor → KnowledgeGraph
- Created `features/base-cv/lib/cvToGraph.ts` adapter (cvProfileToGraph / graphToCvProfile)
- `BaseCvEditor` replaced with thin wrapper using KnowledgeGraph + adapter

### C1-C: Match View → KnowledgeGraph
- Added `category?: string` to `GraphNode` in api.types.ts
- Updated match fixtures to include category on all nodes
- Created `features/job-pipeline/lib/matchToGraph.ts` (matchPayloadToGraph / graphToMatchEdits / MatchEdits)
- Created `UnmappedSkillsPanel` — collapsible list of unconnected profile nodes
- `Match.tsx` replaced with KnowledgeGraph in 2-column grouped layout + UnmappedSkillsPanel + MatchDecisionModal
```

- [ ] **Step 4: Final commit**

```bash
git add plan/index_checklist.md changelog.md
git commit -m "docs: update changelog and checklist for C1 graph editor redesign"
```
