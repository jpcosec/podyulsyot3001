# Spec UI-001 — Shadcn UI Migration

**Feature:** Replace custom UI components with shadcn/ui
**Context:** Node Editor refactoring - custom UI outside ReactFlow canvas
**Phase:** Post-GRP integration/refinement track

---

## Objective

Replace custom-built UI components in `KnowledgeGraph.tsx` with shadcn/ui components for:
- Better accessibility (Radix primitives)
- Consistent styling
- Easier maintenance
- New features (Command palette, Context menu, Sonner)

---

## Scope

### Replace (Custom UI -> Shadcn)

| Current | Replacement | Step |
|---------|-------------|------|
| `SidebarSection` | `Accordion` | UI-001-02 |
| Node editor modal | `Sheet` | UI-001-03 |
| Edge editor modal | `Sheet` | UI-001-04 |
| `PropertyValueInput` | `Input/Select/Textarea/Checkbox` | UI-001-05 |
| Delete confirmation | `AlertDialog` | UI-001-06 |
| Filter buttons | `DropdownMenu + Popover` | UI-001-07 |
| Creation list | `Command + Popover` | UI-001-08 |

### Add (New Features)

| Feature | Component | Step |
|---------|-----------|------|
| Right-click menu | `ContextMenu` | UI-001-09 |
| Ctrl+K search | `CommandDialog` | UI-001-10 |
| Notifications | `Sonner` | UI-001-11 |

### NOT Replace (ReactFlow-native)

- Node components (`SimpleNodeCard`, `GroupNode`)
- Edge components (`FloatingEdge`)
- Canvas interactions

---

## Dependencies

- `UI-001-01` is blocking and must be completed first.
- `UI-001-02` depends on `GRP-001-07`.
- `UI-001-03` and `UI-001-04` depend on `GRP-001-08`.
- `UI-001-05` depends on `GRP-001-04` and `GRP-001-08`.
- `UI-001-06` and `UI-001-09` depend on `GRP-001-05`.
- `UI-001-07`, `UI-001-08`, and `UI-001-10` depend on `GRP-001-07`.
- `UI-001-11` depends on `GRP-001-10`.

This track is not fully parallel by default. Parallelize only when dependencies are already met.

---

## Files Created

```
apps/review-workbench/src/components/ui/
  accordion.tsx
  sheet.tsx
  alert-dialog.tsx
  input.tsx
  select.tsx
  textarea.tsx
  dropdown-menu.tsx
  popover.tsx
  command.tsx
  context-menu.tsx
  sonner.tsx
  skeleton.tsx
  tabs.tsx
  scroll-area.tsx
```

---

## Verification strategy

- Per-step local checks are mandatory (render smoke + typecheck on touched module).
- End-to-end checks run in `step-05-final-validation.md` after all GRP/UI steps are complete.

---

## Reference

- Shadcn docs: https://ui.shadcn.com
- Current code: `apps/review-workbench/src/pages/global/KnowledgeGraph.tsx`
