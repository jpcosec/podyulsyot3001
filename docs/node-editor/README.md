# Node Editor — Implementation Docs

> Reference documentation for reimplementing `KnowledgeGraph.tsx` (2,949 lines) into the 3-layer architecture.
>
> **Start here.** Then follow the section that matches what you're building.

---

## What we're building

A graph editor that replaces the God Component `src/pages/global/KnowledgeGraph.tsx` with a clean separation:

```
src/
├── features/graph-editor/
│   ├── L1-app/        ← GraphEditorPage: fetch + translate + mount
│   ├── L2-canvas/     ← The full editor: canvas, sidebar, inspectors, hooks
│   └── hooks/
├── components/content/ ← L3: reusable content components (no graph knowledge)
├── stores/             ← Zustand: graph-store, ui-store
└── schema/             ← Node Type Registry + Zod schemas
```

---

## Navigation by goal

| Goal | Read |
|------|------|
| Understand the 3-layer model | [`../plan/ARCHITECTURE.md`](../../plan/ARCHITECTURE.md) |
| See the complete implementation blueprint | [`../plan/_meta/blueprint_node_editor.md`](../../plan/_meta/blueprint_node_editor.md) |
| **Critical: Avoid architectural pitfalls** | [`architecture_pitfalls.md`](architecture_pitfalls.md) |
| Build L1 (data loading + schemaToGraph) | [`l1-app-layer.md`](l1-app-layer.md) |
| Product context | [`product.md`](product.md) |
| Build L2/L3 (planned docs) | Planned - tracked in `plan/steps/step-02-create-docs.md` |
| Find ReactFlow patterns with code | [`../plan/_meta/reactflow_patterns_catalog.md`](../../plan/_meta/reactflow_patterns_catalog.md) |
| See known problems and risks | [`../plan/_meta/architecture_critique.md`](../../plan/_meta/architecture_critique.md) |

### Available now

- `docs/node-editor/README.md`
- `docs/node-editor/architecture_pitfalls.md`
- `docs/node-editor/l1-app-layer.md`
- `docs/node-editor/product.md`

---

## Architecture in one sentence per layer

**L1 (App):** ~30 lines. Fetches data, calls `schemaToGraph()`, renders `<GraphEditor>`. Knows about the domain (Jobs, CVs). Knows nothing about ReactFlow.

**L2 (Canvas):** The entire editor. Self-contained — sidebar, inspectors, undo, filters, creation palette all live here. Uses Zustand stores. Knows about ReactFlow, elkjs, edges. Does not know about "Jobs" or "CVs".

**L3 (Content):** Pure React components in `components/content/`. Receive props, emit `onChange`. Work in a node, a Sheet, a table, or a modal. Know nothing about graphs.

---

## Critical decisions (non-negotiable)

These decisions are final. Do not reopen them.

| Decision | Status |
|----------|--------|
| Layout engine: **elkjs** (not dagre) | Decided — subflows require compound layouts |
| State: **Zustand** with atomic selectors (not React Context) | Decided — Context re-renders all consumers |
| Sidebar/filters/actions: **L2** (not L1) | Decided — editor owns its own controls |
| Payload validation: **Zod** in Node Type Registry | Decided — TypeScript disappears at runtime |
| HTML sanitization: **DOMPurify** default-deny | Decided — XSS risk from user data |
| Collapse behavior: **Edge Inheritance** (not ProxyEdge) | Decided — no create/destroy lifecycle |
| L3 location: `components/content/` (not inside feature) | Decided — reusable across features |
| Schema loading: **Dynamic JSON** (not hardcoded) | Decided — domain-agnostic editor |
| ELK layout: **Web Worker** (not main thread) | Decided — performance critical |
| Delete handling: **ReactFlow callbacks** (not manual keydown) | Decided — sync with Zustand |

---

## Canonical contract

Use this contract consistently across stores, schema translation, and registry:

- Node payload is domain-agnostic at the store boundary.
- Runtime validation and narrowing happen in the Node Type Registry (`payloadSchema` + sanitizer).
- Unknown/invalid payloads produce `ErrorNode`, never a runtime crash.

---

## What NOT to do

These anti-patterns appear in older docs and have been superseded:

| Anti-pattern | Where it appeared | Correct approach |
|--------------|-------------------|-----------------|
| Sidebar in L1 | `refactor_knowledgegraph.md`, `monolith_split_proposal.md` | Sidebar is in L2 |
| `contentType: 'markdown' \| 'json' \| ...` enum | `06_flow_contract.md`, `implementation_example.md` | Node Type Registry lookup |
| `payload: Record<string, any>` | `06_flow_contract.md` | Zod schemas in registry |
| `layoutEngine: 'dagre' \| 'manual'` | `ARCHITECTURE.md` (old), `layout_presets.md` | `'elk' \| 'manual'` |
| "Add zustand only when multiple surfaces need it" | `graph_foundations.md` | Zustand from day 1 |
| ProxyEdge for group collapse | Various | Edge Inheritance — reroute, don't create |
| L3 inside `features/graph-editor/content/` | `monolith_split_proposal.md` | L3 in `components/content/` |
| Filters modify AST before passing to canvas | `refactor_knowledgegraph.md` | Filters live in ui-store in L2 |
| Hardcoded domain (person, skill, etc.) | `register-defaults.ts` production | Dynamic schema JSON loading |
| `Record<string, unknown>` used directly in UI | Legacy docs | `NodePayload` envelope + registry validation |
| ELK in main thread | Legacy implementation | Web Worker |
| Manual Delete key handling | Legacy hooks | ReactFlow `onNodesDelete`/`onEdgesDelete` |
| Import EntityCard in Step 3 | `register-defaults.ts` | Use placeholders |

---

## Critical Patterns (Non-Negotiable)

These patterns were discovered through architectural review and MUST be followed:

### 1. Dynamic Schema Loading (No Hardcoded Domain)

The editor MUST be domain-agnostic. Never hardcode node types like `person`, `skill`, `project` in production code.

```ts
// ❌ WRONG: Hardcoded domain in registry
import '@/schema/register-defaults'; // person, skill, project, etc.

// ✅ CORRECT: L1 loads schema JSON and populates registry
const { data: schema } = useQuery({ queryKey: ['schema'], queryFn: fetchSchema });
useEffect(() => {
  schema.node_types.forEach(type => {
    registry.register({ typeId: type.id, ... });
  });
}, [schema]);
```

### 2. Registry-Validated Payload Contract

Keep store payload domain-agnostic and validate/narrow at registry boundaries:

```ts
// ✅ Store boundary: generic payload envelope
type NodePayload = {
  typeId: string;
  value: unknown;
};

// ✅ Registry boundary: runtime validation + sanitization
const parsed = def.payloadSchema.safeParse(payload.value);
if (!parsed.success) {
  // produce ErrorNode, never crash the editor
}
```

### 3. Visual-Only Flag for Undo/Redo

Collapsing/expanding groups is a visual operation, not a semantic action. Never pollute the undo stack with UI-only changes:

```ts
// ❌ WRONG: Collapse adds to undo stack
updateNode(nodeId, { hidden: true });

// ✅ CORRECT: Use isVisualOnly flag
updateNode(nodeId, { hidden: true }, { isVisualOnly: true });
```

### 4. Web Worker for ELK Layout

ELKjs is CPU-intensive. Never run it on the main React thread:

```ts
// ❌ WRONG: Blocks the main thread
const layoutedGraph = await elk.layout(graph);

// ✅ CORRECT: Run in Web Worker
const worker = new Worker(new URL('./elk.worker.ts', import.meta.url));
worker.postMessage({ type: 'layout', payload: graph });
```

### 5. ReactFlow Delete Handlers

Never implement manual Delete key handling. ReactFlow provides `onNodesDelete` and `onEdgesDelete` callbacks that handle deletion internally:

```ts
// ❌ WRONG: Manual keydown handling duplicates functionality
useEffect(() => {
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Delete') { /* manual delete */ }
  });
});

// ✅ CORRECT: Let ReactFlow handle it, sync to store
<ReactFlow
  onNodesDelete={(deleted) => removeElements(nodeIds, edgeIds)}
  onEdgesDelete={(deleted) => removeElements([], edgeIds)}
/>
```

### 6. Placeholder Components to Avoid Circular Dependencies

When creating the Registry (Step 3) before L3 Components (Step 4), use placeholders:

```ts
// ❌ WRONG: Imports EntityCard before it exists
import { EntityCard } from '@/components/content/EntityCard'; // Build error!

// ✅ CORRECT: Use placeholders in Step 3, update in Step 4
const PlaceholderDetail = (props) => <div>Placeholder</div>;
registry.register({ renderers: { detail: PlaceholderDetail } });
// After Step 4: update to use real EntityCard
```

---

## Implementation order

1. **Preflight** — define data provider, verify worker support, decide QA strategy
2. **UI foundation** — install shadcn base components (`UI-001-01`)
3. **Zustand stores** — `graph-store.ts` + `ui-store.ts`
4. **Schema translation** — `schemaToGraph` and `graphToDomain`
5. **Node Type Registry** — placeholders first to avoid circular imports
6. **L3 components** — implement real content components and replace placeholders
7. **GraphCanvas + edges** — controlled drag, semantic history, custom edges
8. **Sidebar + Panels + Hooks** — finish L2 behavior
9. **L1 orchestrator** — dynamic schema load + save integration
10. **Theming + UI refinements** — `xy-theme.css` and UI-001-02..11

---

## Dependencies

```json
{
  "add": {
    "elkjs": "compound layout engine",
    "zustand": "state management",
    "zod": "runtime payload validation",
    "dompurify": "HTML sanitization",
    "@radix-ui/react-*": "via shadcn (Sheet, Accordion, AlertDialog, ContextMenu)"
  },
  "keep": {
    "@xyflow/react": "^12.10.1",
    "@tanstack/react-query": "^5.94.5",
    "tailwindcss": "^3.4.17",
    "lucide-react": "^0.577.0"
  },
  "remove": {
    "dagre": "replaced by elkjs",
    "@dagrejs/dagre": "replaced by elkjs"
  }
}
```
