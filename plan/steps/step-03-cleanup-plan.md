# Step 03: Clean Up Plan Directory

**Context:** After implementation, clean up temporary planning files that are no longer needed.

---

## 1. Purpose

- Remove obsolete planning files
- Keep only final documentation
- Archive legacy analysis

---

## 2. Files to Remove

```bash
# Obsolete analysis files (merged into implementation)
rm plan/00_component_map.md
rm plan/_legacy/refactor_knowledgegraph.md
rm plan/_legacy/session_reactflow_deep_dive.md

# Redundant meta files (archived)
mv plan/_meta/architecture_critique.md plan/_archive/ 2>/dev/null || true
mv plan/_meta/monolith_split_proposal.md plan/_archive/ 2>/dev/null || true
```

---

## 3. Files to Keep

```
plan/
├── README.md                 # Updated project README
├── ARCHITECTURE.md          # Current architecture
├── GUIDE.md                  # Implementation guide
├── steps/                    # Implementation steps (this is the spec)
├── _meta/
│   ├── blueprint_node_editor.md    # Source of truth
│   └── reactflow_patterns_catalog.md # Reference
└── _archive/                 # Old analysis (optional)
```

---

## 4. Action

```bash
# Create archive if needed
mkdir -p plan/_archive

# Move redundant files
mv plan/_meta/architecture_critique.md plan/_archive/ 2>/dev/null || true
mv plan/_meta/monolith_split_proposal.md plan/_archive/ 2>/dev/null || true

# Remove temp files
rm -f plan/00_component_map.md

# Commit cleanup
git add -A
git commit -m "docs: clean up planning files after refactor"
```

---

## 5. Verification

- [ ] plan/ directory is clean
- [ ] Only relevant files remain
- [ ] README still links to valid docs

---

## 6. Next Step

step-04-create-future — Create FUTURE.md with roadmap.