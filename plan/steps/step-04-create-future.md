# Step 04: Create FUTURE.md Roadmap

**Context:** Document future improvements and next steps after the refactor.

---

## 1. Purpose

- Document what was accomplished
- Set direction for future work
- Provide onboarding context for new developers

---

## 2. Content Template

Create `FUTURE.md` in project root:

```markdown
# Future Improvements

## Completed (v2.0.0)

- **Architecture:** L1/L2 split with Zustand stores
- **Rendering:** ReactFlow with custom nodes/edges
- **UI:** shadcn/ui component migration
- **Theming:** xy-theme.css with type-based colors

## Backlog

### High Priority
- [ ] Performance optimization for large graphs (>500 nodes)
- [ ] Implement group collapse/expand animations
- [ ] Add minimap customization
- [ ] Edge label editing

### Medium Priority
- [ ] Keyboard shortcuts for all actions
- [ ] Undo/redo persistence across sessions
- [ ] Graph export (JSON, PNG, SVG)
- [ ] Import from external formats

### Lower Priority
- [ ] Collaborative editing (real-time)
- [ ] Graph versioning/branching
- [ ] Custom node templates
- [ ] Plugin system for extensions

## Technical Debt

- [ ] E2E test coverage (TestSprite)
- [ ] Performance benchmarking
- [ ] Bundle size optimization
- [ ] Accessibility audit

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## Architecture Decisions

- **Why Zustand?** Atomic selectors prevent unnecessary re-renders
- **Why shadcn/ui?** Accessible, themeable, maintained
- **Why ELKjs?** Best-in-class layout algorithm for directed graphs
```

---

## 3. Action

```bash
# Create FUTURE.md
cat > FUTURE.md << 'EOF'
# Future Improvements

## Completed (v2.0.0)
...

## Backlog
...

## Contributing
See CONTRIBUTING.md
EOF

# Commit
git add FUTURE.md
git commit -m "docs: add FUTURE.md roadmap"
```

---

## 4. Verification

- [ ] FUTURE.md exists in root
- [ ] Lists completed work
- [ ] Has prioritized backlog
- [ ] Links to contributing guidelines

---

## 5. Next Step

All cleanup steps complete. Begin new development cycle.