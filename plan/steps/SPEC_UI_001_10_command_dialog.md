# Step 10: Add CommandDialog (Ctrl+K)

**Spec:** SPEC_UI_001
**Phase:** 4 (Enhanced Features)
**Priority:** MEDIUM — Global command palette

---

## 1. Migration Notes

> NEW feature - not replacing legacy code. Adds power-user keyboard access.

**Why add?**
- Standard modern app pattern (like Spotlight/Command Palette)
- Quick node navigation
- Quick action access

---

## 2. Data Contract

```ts
interface CommandMenuProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  nodes: SimpleNode[];
  onSelectNode: (nodeId: string) => void;
  onSave: () => void;
  onUndo: () => void;
  onRedo: () => void;
}
```

---

## 3. Files to Create

```
apps/review-workbench/src/
├── features/graph-editor/
│   └── L2-canvas/
│       └── components/
│           └── CommandMenu.tsx
```

---

## 4. Implementation

```tsx
// features/graph-editor/L2-canvas/components/CommandMenu.tsx
// (Implementation verified)
```

Ctrl+K listener added in GraphEditor or parent.

---

## 5. Styles

Uses shadcn CommandDialog defaults.

---

## 6. Definition of Done

```
[ ] CommandMenu.tsx exists
[ ] Ctrl+K opens dialog
[ ] Search filters nodes and actions
[ ] Enter selects item
[ ] Escape closes
[ ] No TypeScript errors
```

---

## 7. E2E (TestSprite)

```ts
test('command palette opens with Ctrl+K', async ({ page }) => {
  await page.goto('/graph');
  
  await page.keyboard.press('Control+k');
  await expect(page.locator('[role="dialog"]')).toBeVisible();
});
```

---

## 8. Git Workflow

### Commit

```
feat(ui): add command palette (UI-001-10)

- CommandDialog with node search
- Ctrl+K keyboard shortcut
- Quick actions
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented UI-001-10: Command palette.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@/components/ui/command` | From UI-001-01 |

---

## 10. Next Step

UI-001-11 — Add Sonner for toast notifications.