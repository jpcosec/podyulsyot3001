# Step 03: Clean Up Plan Directory

**Context:** After implementation and docs updates, clean planning files without breaking references.

---

## 1. Purpose

- Remove obsolete planning artifacts safely
- Keep active docs and historical references discoverable
- Avoid deleting files still referenced by README/GUIDE/docs

---

## 2. Safe cleanup policy

Perform cleanup in this order:

1. **Desreference**: remove links to files you want to retire
2. **Archive**: move deprecated docs to `plan/_archive/`
3. **Delete (optional)**: delete only files no longer referenced and no longer useful

Do not apply direct mass `rm` before step 1.

---

## 3. Legacy policy for monolith

- Keep `apps/review-workbench/src/pages/global/KnowledgeGraph.tsx` during migration.
- Optional rename to `KnowledgeGraph.legacy.tsx` while GRP/UI work is in progress.
- Delete only after Step 10 is stable and final validation passes.

---

## 4. Suggested actions

```bash
# 1) Archive bucket
mkdir -p plan/_archive

# 2) Move deprecated docs only after links are removed
mv plan/_meta/monolith_split_proposal.md plan/_archive/ 2>/dev/null || true

# 3) Optional delete for clearly obsolete files
rm -f plan/00_component_map.md
```

---

## 5. Verification

- [ ] `plan/README.md`, `plan/GUIDE.md`, and `docs/node-editor/README.md` have no broken links
- [ ] Archived files are no longer primary references
- [ ] `KnowledgeGraph` removal is deferred until final validation

---

## 6. Next step

`step-04-create-future.md` - Keep deferred specs aligned with current roadmap.
