# Step 4: Replace Edge Editor Modal with Sheet

**Spec:** SPEC_UI_001
**Phase:** 2 (Core Migration)
**Priority:** HIGH — Core editing UX

---

## 1. Migration Notes

> Migration from KnowledgeGraph.tsx lines 2800-2850: custom edge editor modal.

**Why migrate?**
- shadcn Sheet provides proper overlay, animation, accessibility
- Reuses EdgeInspector from GRP-001-08 (parallel track)
- Simpler code, easier maintenance

---

## 2. Data Contract

Same as GRP-001-08 EdgeInspector - uses `focusedEdgeId` from ui-store.

---

## 3. Files to Modify

```
apps/review-workbench/src/
├── features/graph-editor/
│   └── L2-canvas/
│       └── GraphEditor.tsx  // Add EdgeInspector import
```

---

## 4. Implementation

```tsx
// features/graph-editor/L2-canvas/GraphEditor.tsx
import { EdgeInspector } from './panels/EdgeInspector'

export function GraphEditor() {
  return (
    <div className="h-full w-full">
      <GraphCanvas />
      <CanvasSidebar />
      <NodeInspector />
      <EdgeInspector />  {/* From GRP-001-08 */}
    </div>
  )
}
```

---

## 5. Styles

Uses shadcn Sheet defaults + `w-[400px]`.

---

## 6. Definition of Done

```
[ ] EdgeInspector renders in GraphEditor
[ ] Sheet opens when edge selected
[ ] Edit form shows relation type field
[ ] Save persists to store
[ ] Cancel/X closes without saving
[ ] No TypeScript errors
```

---

## 7. E2E (TestSprite)

```ts
test('edge sheet opens on click', async ({ page }) => {
  await page.goto('/graph');
  
  // Click edge
  await page.click('.react-flow__edge-path');
  
  // Sheet opens
  await expect(page.locator('[role="dialog"]')).toBeVisible();
  await expect(page.locator('text=Edit Edge')).toBeVisible();
});
```

---

## 8. Git Workflow

### Commit

```
refactor(ui): replace edge modal with shadcn Sheet (UI-001-04)

- Integrated EdgeInspector from GRP-001-08
- Connected to ui-store for focusedEdgeId
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented UI-001-04: Edge edit sheet migration.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@/components/ui/sheet` | From UI-001-01 |
| `EdgeInspector` | From GRP-001-08 |

---

## 10. Next Step

UI-001-05 — Replace property inputs with shadcn Input/Select/Textarea.