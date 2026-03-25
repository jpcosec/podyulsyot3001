# Step 1: Install Shadcn Components

**Spec:** SPEC_UI_001
**Phase:** 1 (Setup)
**Priority:** HIGH — Foundation for all UI migrations

---

## 1. Migration Notes

> This is a setup step, not a migration from KnowledgeGraph.tsx.

**Why now?**
- All subsequent UI-001 steps depend on shadcn components
- Running installation once is more efficient than per-step

---

## 2. Data Contract

N/A — Installation step, no contracts.

---

## 3. Files to Create

N/A — Components installed to existing `components/ui/` directory.

---

## 4. Implementation

```bash
cd apps/review-workbench

# Core components for sidebar + panels
npx shadcn@latest add accordion
npx shadcn@latest add sheet
npx shadcn@latest add alert-dialog
npx shadcn@latest add input
npx shadcn@latest add select
npx shadcn@latest add textarea

# Components for enhanced features
npx shadcn@latest add dropdown-menu
npx shadcn@latest add popover
npx shadcn@latest add command
npx shadcn@latest add context-menu
npx shadcn@latest add sonner
npx shadcn@latest add skeleton
npx shadcn@latest add tabs
npx shadcn@latest add scroll-area
```

---

## 5. Styles

Components include their own Tailwind styles. No additional CSS needed.

---

## 6. Definition of Done

```
[ ] All 14 components installed without errors
[ ] components/ui/ has all component folders
[ ] lib/utils.ts has cn() function
[ ] No console errors on app load
[ ] Typescript compiles without errors
```

---

## 7. E2E (TestSprite)

Not applicable — installation verified via file existence.

---

## 8. Git Workflow

### Commit

```
chore(ui): install shadcn components (UI-001-01)

- Added accordion, sheet, alert-dialog, input, select, textarea
- Added dropdown-menu, popover, command, context-menu
- Added sonner, skeleton, tabs, scroll-area
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented UI-001-01: Shadcn component installation.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `shadcn@latest` | Component installation CLI |
| `tailwind-merge` | Via shadcn |
| `clsx` | Via shadcn |

---

## 10. Next Step

UI-001-02 — Replace SidebarSection with shadcn Accordion.