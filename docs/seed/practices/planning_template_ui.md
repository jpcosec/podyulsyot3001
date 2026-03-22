# Planning Template

Template for creating new feature specs in PhD 2.0. Follow this structure to ensure consistency and completeness.

---

## Template Structure

```markdown
# Spec <ID> — <View Name>

**Feature:** `src/features/<feature>/`
**Page:** `src/pages/<page>/<ViewName>.tsx`
**Libraries:** `@tanstack/react-query` · `lucide-react` · `react-router-dom`
**Phase:** <N> (included in `phase_N_name`)

---

## Migration Notes

**Legacy source:** `apps/review-workbench/src/` in branch `dev`
**Legacy components:** <list components to extract>
**To migrate:** <migration instructions>

---

## 1. Operator Objective

What the operator should be able to do with this view:
- <objective 1>
- <objective 2>
- <objective N>

---

## 2. Data Contract (API I/O)

**Read:**
- `GET <endpoint>` → `<Type>`
  ```ts
  {
    // response shape
  }
  ```

**Write:**
- <write operations if any, or "None. Read-only view.">

---

## 3. UI Composition and Layout

**Layout:** <12-col grid description>

```
┌──────────────── col-N ────────────────┬── col-N ──┐
│  <component>                           │ <sidebar> │
│  <component>                           │           │
└────────────────────────────────────────┴───────────┘
│  FAB: "<action>" (fixed bottom-right)              │
```

**Core Components:**
- `<ComponentName>` — <description>

---

## 4. Styles (Terran Command)

- Background: `bg-surface`
- Headers: `font-mono text-[11px] uppercase tracking-[0.2em] text-outline`
- <other style rules>

**Interactions:**
- Click → `navigate(<route>)`
- <other interactions>

**Empty State:** <what to show>
**Error State:** <what to show>
**Loading State:** <what to show>

---

## 5. Files to Create

```
src/features/<feature>/
  api/
    use<Data>.ts        useQuery(['<feature>','<data>'])
  components/
    <Component1>.tsx    <description>
    <Component2>.tsx    <description>
src/pages/<scope>/
  <ViewName>.tsx        DUMB: useParams + hook + layout
src/components/atoms/
  <Atom>.tsx           REQUIRED by <ComponentName>
```

---

## 6. Definition of Done

```
[ ] <ViewName> renders without console errors or TS errors
[ ] <component X> shows <expected behavior>
[ ] Click on <element> navigates to <route>
[ ] Empty state shows <message>
[ ] Loading state shows <spinner>
[ ] Error state shows <banner>
[ ] No hardcoded data — all data from mock/API
```

---

## 7. E2E (TestSprite)

**URL:** `<route>`

1. Verify `<Component>` renders with at least <N> items
2. Verify <specific element> has <expected state>
3. Click on <element> → verify navigation to <route>
4. <other test steps>

---

## 8. Git Workflow

### Commit on phase close

```
feat(ui): implement <view name> (<spec-id>)

- <component 1>
- <component 2>
- <component 3>
- Connected to <hook names>
```

### Changelog entry (changelog.md)

```markdown
## YYYY-MM-DD

- Implemented <spec-id> <view name>: <brief description>.
```

### Checklist update (index_checklist.md)

- [x] <spec-id> <View Name>
```

---

## Planning Workflow

```
1. Read the spec for the view to implement
2. Review Migration Notes to know what to extract from `dev`
3. Implement following the file structure in the spec
4. Verify Definition of Done
5. Run E2E tests
6. COMMIT with mandatory format (see above)
7. ADD entry to changelog.md
8. MARK [x] in index_checklist.md
```

---

## Completion Checklist

| Step | Description | Verified |
|------|-------------|----------|
| 1 | Read spec | ☐ |
| 2 | Review migration notes | ☐ |
| 3 | Implement components | ☐ |
| 4 | Verify DoD | ☐ |
| 5 | Run E2E tests | ☐ |
| 6 | Commit (format required) | ☐ |
| 7 | Changelog entry | ☐ |
| 8 | Checklist update | ☐ |
