# Docstring Alignment After OOP Skeleton

**Umbrella:** depends on `ariadne-oop-skeleton.md`, `oop-08b-package-locality.md`, `oop-08-cleanup.md`. Run after the structural refactor is complete.

### 1. Explanation
During Phase 0.5, symbols are being moved, absorbed, split, or turned into compatibility shims. That makes docstrings drift quickly: many will still describe legacy module ownership, executor-first language, or node-based behavior after the code has moved into actors, cognition, adapters, and storage.

### 2. Reference
`src/automation/ariadne/core/`, `src/automation/main.py`, `src/automation/ariadne/graph/orchestrator.py`, `src/automation/ariadne/contracts/`, `src/automation/ariadne/models.py`, any compatibility shims that survive OOP 08

### 3. Real fix
Do a post-refactor docstring alignment pass once ownership is stable. Keep docstrings minimal and truthful during refactor work, then rewrite module/class/function docstrings to match the final package layout and responsibilities.

### 4. Steps
1. Defer broad docstring rewriting until after Phase 0.5 structure is stable.
2. During refactor atoms, only fix docstrings that become clearly false or misleading.
3. After `oop-08-cleanup.md`, audit:
   - module docstrings
   - class docstrings
   - public method/function docstrings
   - compatibility shim warnings
4. Remove stale terminology.
   - replace legacy executor/node/repository language where ownership has changed
   - ensure adapters, actors, cognition, storage, and strategies use the final terminology consistently
5. Keep docstrings short and ownership-oriented.
   - explain responsibility and boundary
   - avoid restating obvious implementation details
6. Update any docs that quote outdated docstrings if needed.

### 4.1 Serena AST refactor operations
- Use `get_symbols_overview` on refactored files to identify public symbols that need docstring review.
- Use `find_symbol(include_body=True)` for classes/functions whose behavior changed substantially during the refactor.
- Use `replace_symbol_body` when a symbol rewrite naturally includes a docstring rewrite.
- Use targeted file edits for module docstrings and for compatibility shims that need explicit deprecation notes.

### 5. Test command
No separate runtime validation required beyond the final post-refactor test pass.

Suggested verification:
1. `python -m pytest tests/unit/automation/ -q`
2. `python -m pytest tests/architecture/ -q`
3. manual spot-check of key modules for terminology consistency

### 📦 Required Context Pills
- `plan_docs/context/actor-pattern.md`
- `plan_docs/context/labyrinth-pattern.md`
- `plan_docs/context/peripheral-adapter-pattern.md`
- `plan_docs/context/ariadne-models.md`

### 🚫 Non-Negotiable Constraints
- **Docstrings Follow Ownership:** docstrings must describe final ownership boundaries, not temporary migration states.
- **No Premature Rewrites:** avoid broad docstring regeneration before the refactor settles.
- **Keep It Tight:** docstrings should clarify boundary and intent, not duplicate the code line-by-line.
