# Step 8: Create L2 Panels (NodeInspector, EdgeInspector)

**Spec:** SPEC_GRP_001
**Phase:** 3 (L2 Canvas)
**Priority:** MEDIUM — Visual editing components

---

## 1. Migration Notes

> Not applicable — panels are new code replacing inline KnowledgeGraph.tsx logic.

**Why new?**
- Current `KnowledgeGraph.tsx` uses inline Sheet-like modals (lines 500-700)
- Blueprint mandates separate L2 components for each panel
- Sheet from shadcn/ui provides proper accessibility and animation

---

## 2. Data Contract

### NodeInspector Props

```ts
interface NodeInspectorProps {
  // No props - subscribes to ui-store via hooks
}
```

### EdgeInspector Props

```ts
interface EdgeInspectorProps {
  // No props - subscribes to ui-store via hooks
}
```

---

## 3. Files to Create

```
apps/review-workbench/src/
├── features/graph-editor/
│   └── L2-canvas/
│       └── panels/
│           ├── NodeInspector.tsx
│           └── EdgeInspector.tsx
```

---

## 4. Implementation

```tsx
// features/graph-editor/L2-canvas/panels/NodeInspector.tsx
import { useState, useEffect } from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { PropertyEditor } from "@/components/content/PropertyEditor"
import { useUIStore } from "@/stores/ui-store"
import { useGraphStore } from "@/stores/graph-store"
import { pairsFromRecord, recordFromPairs } from "@/lib/utils"

export function NodeInspector() {
  const focusedNodeId = useUIStore(s => s.focusedNodeId);
  const setFocusedNode = useUIStore(s => s.setFocusedNode);
  const setEditorState = useUIStore(s => s.setEditorState);
  const nodes = useGraphStore(s => s.nodes);
  const updateNode = useGraphStore(s => s.updateNode);
  
  const node = nodes.find(n => n.id === focusedNodeId);
  const open = focusedNodeId !== null;
  
  const [draft, setDraft] = useState<any>(null);
  
  useEffect(() => {
    if (node) {
      setDraft({ ...node.data });
    }
  }, [node]);
  
  if (!open || !node || !draft) return null;
  
  const handleSave = () => {
    updateNode(node.id, { data: { ...node.data, ...draft } });
    setFocusedNode(null);
    setEditorState('browse');
  };
  
  const handleClose = () => {
    setFocusedNode(null);
    setEditorState('browse');
  };
  
  return (
    <Sheet open={open} onOpenChange={(isOpen) => !isOpen && handleClose()}>
      <SheetContent side="right" className="w-[400px]">
        <SheetHeader>
          <SheetTitle>Edit Node</SheetTitle>
          <SheetDescription>
            {draft.name} ({draft.category})
          </SheetDescription>
        </SheetHeader>
        
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            />
          </div>
          
          <div className="space-y-2">
            <Label>Category</Label>
            <div className="text-sm text-muted-foreground">{draft.category}</div>
          </div>
          
          <div className="space-y-2">
            <Label>Properties</Label>
            <PropertyEditor
              pairs={pairsFromRecord(draft.properties || {})}
              onChange={(pairs) => setDraft({ ...draft, properties: recordFromPairs(pairs) })}
            />
          </div>
          
          <div className="flex gap-2 pt-4">
            <Button onClick={handleSave}>Save</Button>
            <Button variant="outline" onClick={handleClose}>Cancel</Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
```

```tsx
// features/graph-editor/L2-canvas/panels/EdgeInspector.tsx
import { useState, useEffect } from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useUIStore } from "@/stores/ui-store"
import { useGraphStore } from "@/stores/graph-store"

export function EdgeInspector() {
  const focusedEdgeId = useUIStore(s => s.focusedEdgeId);
  const setFocusedEdge = useUIStore(s => s.setFocusedEdge);
  const setEditorState = useUIStore(s => s.setEditorState);
  const edges = useGraphStore(s => s.edges);
  const updateEdge = useGraphStore(s => s.updateEdge);
  
  const edge = edges.find(e => e.id === focusedEdgeId);
  const open = focusedEdgeId !== null;
  
  const [draft, setDraft] = useState<any>(null);
  
  useEffect(() => {
    if (edge?.data) {
      setDraft({ ...edge.data });
    }
  }, [edge]);
  
  if (!open || !edge || !draft) return null;
  
  const handleSave = () => {
    updateEdge(edge.id, { data: { ...edge.data, ...draft } });
    setFocusedEdge(null);
    setEditorState('browse');
  };
  
  const handleClose = () => {
    setFocusedEdge(null);
    setEditorState('browse');
  };
  
  return (
    <Sheet open={open} onOpenChange={(isOpen) => !isOpen && handleClose()}>
      <SheetContent side="right" className="w-[400px]">
        <SheetHeader>
          <SheetTitle>Edit Edge</SheetTitle>
          <SheetDescription>
            Relation: {draft.relationType}
          </SheetDescription>
        </SheetHeader>
        
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="relationType">Relation Type</Label>
            <Input
              id="relationType"
              value={draft.relationType}
              onChange={(e) => setDraft({ ...draft, relationType: e.target.value })}
            />
          </div>
          
          <div className="flex gap-2 pt-4">
            <Button onClick={handleSave}>Save</Button>
            <Button variant="outline" onClick={handleClose}>Cancel</Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
```

---

## 5. Styles

Panels use shadcn Sheet component with Tailwind:
- `w-[400px]` for panel width
- `side="right"` for slide-in from right
- Scroll via `overflow-y-auto` on content area

---

## 6. Definition of Done

```
[ ] NodeInspector.tsx exists in panels/
[ ] EdgeInspector.tsx exists in panels/
[ ] NodeInspector opens when focusedNodeId !== null
[ ] EdgeInspector opens when focusedEdgeId !== null
[ ] Save button updates store and closes panel
[ ] Escape/X closes panel without saving
[ ] No TypeScript errors
[ ] No console errors on open/close
```

---

## 7. E2E (TestSprite)

```ts
// e2e/graph-editor/panels.spec.ts
import { test, expect } from '@playwright/test';

test('node inspector opens and saves', async ({ page }) => {
  await page.goto('/graph');
  
  // Click a node
  await page.click('[data-testid="node-person-1"]');
  
  // Sheet should open
  await expect(page.locator('[role="dialog"]')).toBeVisible();
  await expect(page.locator('text=Edit Node')).toBeVisible();
  
  // Edit name
  await page.fill('#name', 'Updated Person');
  
  // Save
  await page.click('button:has-text("Save")');
  
  // Sheet should close
  await expect(page.locator('[role="dialog"]')).not.toBeVisible();
});
```

---

## 8. Git Workflow

### Commit

```
feat(panels): implement NodeInspector and EdgeInspector (GRP-001-08)

- L2-canvas/panels/NodeInspector.tsx with Sheet
- L2-canvas/panels/EdgeInspector.tsx with Sheet
- Integrates with ui-store for focusedId state
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented GRP-001-08: Inspector panels with shadcn Sheet.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@/components/ui/sheet` | Panel overlay component |
| `@/components/ui/input` | Text editing |
| `@/components/ui/label` | Form labels |
| `@/components/ui/button` | Action buttons |
| `@/components/content/PropertyEditor` | From step 4 |

---

## 10. Next Step

GRP-001-09 — Hooks (useGraphLayout, useEdgeInheritance, useKeyboard) — enables layout automation and keyboard shortcuts.