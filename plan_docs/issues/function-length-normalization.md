# Function Length Normalization

**Umbrella:** can run after `ariadne-oop-skeleton.md` or incrementally on active refactor surfaces. Prefer after Phase 0.5 settles if broad repo churn becomes too high.

### 1. Explanation
Large functions make symbolic refactoring harder, blur ownership, and hide natural class extraction seams. Normalizing function size before or after structural refactors improves Serena-based moves and reduces brittle edits.

### 2. Reference
`AGENTS.md`, `src/automation/`, especially `src/automation/ariadne/graph/orchestrator.py`, `src/automation/main.py`, `src/automation/ariadne/repository.py`, `src/automation/ariadne/promotion.py`, `src/automation/ariadne/capabilities/recording.py`

### 3. Real fix
Refactor oversized functions into small owner-revealing helpers. When the extracted helpers naturally cluster around a responsibility, extract a class or move them next to the owning class.

### 4. Steps
1. Inventory functions over 10 lines in the active refactor surface.
2. Split them into small helpers with single-purpose names.
3. Where helper groups clearly belong to one responsibility, extract a class.
4. Keep public orchestration functions thin; push detail into private helpers.
5. After normalization, resume symbolic ownership moves with Serena.

### 4.1 Serena AST refactor operations
- Use `get_symbols_overview` and file-length scans to identify long functions.
- Use `replace_symbol_body` to slim orchestration functions.
- Use `insert_before_symbol` / `insert_after_symbol` to add helper functions or classes near the owning symbol.
- Use `find_referencing_symbols` before extracting helpers into new classes or modules.

### 5. Test command
Deferred until the relevant refactor slice is complete.

### 🚫 Non-Negotiable Constraints
- **Function Budget:** functions over 10 lines should be treated as refactor candidates.
- **Ownership First:** helper extraction should reveal ownership, not create generic utility dumping grounds.
