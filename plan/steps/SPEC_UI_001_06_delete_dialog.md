# Step 6: Replace Delete Confirmation with AlertDialog

**Spec:** SPEC_UI_001
**Phase:** 3 (Property Components)
**Priority:** MEDIUM — Safety-critical confirmation

---

## 1. Migration Notes

> Migration from KnowledgeGraph.tsx lines 2900-2939: inline delete confirmation dialog.

**Why migrate?**
- shadcn AlertDialog provides accessible modal pattern
- Focus trap and escape key handling
- Consistent destructive action styling

---

## 2. Data Contract

```ts
interface DeleteConfirmProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  target: {
    kind: "node" | "edge";
    title: string;
    description: string;
  } | null;
  onConfirm: () => void;
}
```

---

## 3. Files to Create

```
apps/review-workbench/src/
├── features/graph-editor/
│   └── L2-canvas/
│       └── components/
│           └── DeleteConfirm.tsx
```

---

## 4. Implementation

```tsx
// features/graph-editor/L2-canvas/components/DeleteConfirm.tsx
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog"

export function DeleteConfirm({ open, onOpenChange, target, onConfirm }: DeleteConfirmProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete {target?.title}?</AlertDialogTitle>
          <AlertDialogDescription>
            {target?.description}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction onClick={onConfirm} className="bg-destructive text-destructive-foreground">
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

---

## 5. Styles

Uses shadcn AlertDialog defaults + destructive color class.

---

## 6. Definition of Done

```
[ ] DeleteConfirm.tsx exists
[ ] Dialog opens on delete action
[ ] Shows correct target info
[ ] Confirm deletes and closes
[ ] Cancel closes without action
[ ] No TypeScript errors
```

---

## 7. E2E (TestSprite)

```ts
test('delete confirmation dialog', async ({ page }) => {
  await page.goto('/graph');
  await page.click('[data-testid="node-person-1"]');
  await page.click('button:has-text("Delete")');
  
  await expect(page.locator('text=Delete')).toBeVisible();
  await page.click('button:has-text("Cancel")');
  await expect(page.locator('[role="alertdialog"]')).not.toBeVisible();
});
```

---

## 8. Git Workflow

### Commit

```
refactor(ui): replace delete dialog with shadcn AlertDialog (UI-001-06)

- Added DeleteConfirm component
- Connected to delete action flow
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented UI-001-06: Delete confirmation migration.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@/components/ui/alert-dialog` | From UI-001-01 |

---

## 10. Next Step

UI-001-07 — Replace filter UI with shadcn DropdownMenu + Popover.