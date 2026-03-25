# Step 11: Add Sonner Notifications

**Spec:** SPEC_UI_001
**Phase:** 4 (Enhanced Features)
**Priority:** LOW — User feedback enhancement

---

## 1. Migration Notes

> NEW feature - replaces no legacy code. Adds toast notifications.

**Why add?**
- Non-intrusive user feedback
- Success/error state visibility
- Modern app standard

---

## 2. Data Contract

N/A — Sonner is a drop-in toast provider.

---

## 3. Files to Modify

```
apps/review-workbench/src/
├── app/
│   └── layout.tsx  // Add Toaster
├── features/graph-editor/
    └── L2-canvas/
        └── components/  // Add toast calls
```

---

## 4. Implementation

```tsx
// In app/layout.tsx
import { Toaster } from "@/components/ui/sonner"

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Toaster />
      </body>
    </html>
  )
}

// In components - usage
import { toast } from "sonner"

toast.success("Graph saved successfully")
toast.error("Failed to save")
toast.info("Undo performed")
```

---

## 5. Styles

Uses shadcn Sonner defaults.

---

## 6. Definition of Done

```
[ ] Toaster component added to app root
[ ] toast.success on save
[ ] toast.success on delete
[ ] toast.error on failure
[ ] Toasts auto-dismiss
[ ] No TypeScript errors
```

---

## 7. E2E (TestSprite)

```ts
test('toast appears on save', async ({ page }) => {
  await page.goto('/graph');
  
  await page.click('button:has-text("Save")');
  await expect(page.locator('[role="status"]')).toContainText('saved');
});
```

---

## 8. Git Workflow

### Commit

```
feat(ui): add toast notifications with Sonner (UI-001-11)

- Toaster in app root
- Success/error toasts on actions
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented UI-001-11: Toast notifications.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@/components/ui/sonner` | From UI-001-01 |
| `sonner` | Toast library |

---

## 10. Next Step

Complete UI-001 — All shadcn migrations done. Ready for integration.