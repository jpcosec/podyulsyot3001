# Future Specs

> Features deferred to future iterations. Not implemented in v2.0.0.

---

## Why a Separate Folder?

- Keep main `steps/` clean and focused
- Enable future implementation with ready specs
- Avoid "feature creep" in current refactor
- Each SPEC is a self-contained document

---

## Priority

### High (v2.1)
- Large graph performance (>500 nodes)
- Graph export (JSON, PNG, SVG)

### Medium (v2.2)
- Import from external formats
- Undo/redo persistence across sessions

### Lower (v3.0+)
- Collaborative editing (real-time)
- Graph versioning/branching
- Plugin system for extensions

---

## Current Specs

| File | Feature | Priority |
|------|---------|----------|
| `SPEC_FUTURE_001_performance.md` | Large graph optimization | High |
| `SPEC_FUTURE_002_export.md` | Graph export | High |

---

## Adding a Future Spec

1. Create `SPEC_FUTURE_XXX_name.md` in this folder
2. Use the template:

```markdown
# FUTURE-XXX: Feature Name

**Status:** Deferred  
**Priority:** High/Medium/Low  
**Estimated Effort:** X days

## Problem

What problem does this solve?

## Proposed Solution

How would it work?

## Dependencies

What needs to exist first?

## Risks

What could go wrong?
```

3. Update this README with the new spec

---

## Contributing

When you encounter a good idea that shouldn't block the current refactor:
1. Write a brief description in the appropriate priority section
2. Create a detailed SPEC file when you have time
3. Link it from here
