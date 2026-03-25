# Step 3: Replace Node Editor Modal with Sheet

**Spec:** SPEC_UI_001
**Phase:** 2 (Core Migration)
**Priority:** HIGH — Core editing UX

---

## 1. Migration Notes

> Migration from KnowledgeGraph.tsx lines 2600-2700: custom node editor modal.

**Why migrate?**
- shadcn Sheet provides proper overlay, animation, accessibility
- Reuses NodeInspector from GRP-001-08 (parallel track)
- Simpler code, easier maintenance

---

## 2. Data Contract

Same as GRP-001-08 NodeInspector - uses `focusedNodeId` from ui-store.

---

## 3. Files to Modify

```
apps/review-workbench/src/
├── features/graph-editor/
│   └── L2-canvas/
│       └── GraphEditor.tsx  // Add NodeInspector import
```

---

## 4. Implementation

```tsx
// features/graph-editor/L2-canvas/GraphEditor.tsx
import { NodeInspector } from './panels/NodeInspector'

export function GraphEditor() {
  return (
    <div className="h-full w-full">
      <GraphCanvas />
      <CanvasSidebar />
      <NodeInspector />  {/* Already implemented in GRP-001-08 */}
    </div>
  )
}
```

---

## 5. Styles

Uses shadcn Sheet defaults + `w-[400px]` for wider panel.

---

## 6. Definition of Done

```
[ ] NodeInspector renders in GraphEditor
[ ] Sheet opens when node selected
[ ] Edit form shows all node fields
[ ] Save persists to store
[ ] Cancel/X closes without saving
[ ] No TypeScript errors
```

---

## 7. E2E (TestSprite)

```ts
// e2e/graph-editor/node-sheet.spec.ts
import { test, expect } from '@playwright/test';

test('node sheet opens on click', async ({ page }) => {
  await page.goto('/graph');
  
  // Click node
  await page.click('[data-testid="node-person-1"]');
  
  // Sheet opens
  await expect(page.locator('[role="dialog"]')).toBeVisible();
  await expect(page.locator('text=Edit Node')).toBeVisible();
  
  // Edit and save works
  await page.fill('#name', 'New Name');
  await page.click('button:has-text("Save")');
  
  await expect(page.locator('[role="dialog"]')).not.toBeVisible();
});
```

---

## 8. Git Workflow

### Commit

```
refactor(ui): replace node modal with shadcn Sheet (UI-001-03)

- Integrated NodeInspector from GRP-001-08
- Connected to ui-store for focusedNodeId
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented UI-001-03: Node edit sheet migration.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@/components/ui/sheet` | From UI-001-01 |
| `NodeInspector` | From GRP-001-08 |

---

## 10. Next Step

UI-001-04 — Replace edge edit modal with shadcn Sheet (EdgeSheet).