# OOP 08 — Absorption Cleanup + Docs

**Umbrella:** `ariadne-oop-skeleton.md`. Depends on `oop-08b-package-locality.md`. Final atom.

### 1. Explanation
Delete absorbed modules, update docs, and unblock downstream phases. No behavior changes.

### 2. Reference
N/A

### 3. Real fix
Removal of all legacy node modules and configuration-based mode switching.

### 4. Steps
1. Delete (no re-exports): `graph/nodes/` absorbed files, `capabilities/recording.py` shim (if empty), `promotion.py` shim (if empty), `repository.py` shim (if empty). Keep only files with active, non-`core/` consumers.
2. `modes/*` — convert each mode into a strategy object that `Theseus` / `Delphi` accept via constructor. No more `config` reads.
3. Update `src/automation/ariadne/README.md` with:
   - New package layout (`core/periphery`, `core/cognition`, `core/actors`, `core/adapters`).
   - DI wiring example from `plan_docs/design/ariadne-oop-architecture.md`.
4. Update `CHANGELOG.md`.
5. `plan_docs/issues/Index.md` — mark Phase 0.5 atoms as `{closed with commit id <sha>}` and drop any stale `OUTDATED` residue on downstream phases.

### 4.1 Serena AST refactor operations
- Use `find_referencing_symbols` on `MapRepository`, `GraphRecorder`, `AriadnePromoter`, `observe_node`, `execute_deterministic_node`, `apply_local_heuristics_node`, `llm_rescue_agent_node`, and `human_in_the_loop_node` before deleting their files.
- Any legacy file whose exported symbols have zero non-shim references gets deleted directly; any file with surviving consumers is reduced to an explicit compatibility shim or deferred with a new issue.
- For `modes/*`, use `get_symbols_overview` to identify behavior-heavy functions; if a mode file still mixes multiple concerns or holds methods/functions over ~200 lines, split it into strategy classes before injection.

### 5. Test command
1. `grep -R "from src.automation.motors" src/automation/ariadne/core` returns nothing.
2. `grep -R "graph.nodes" src/automation/ariadne` returns nothing.
3. `python -m pytest tests/unit/automation/ tests/architecture/ -q` green.
4. `src/automation/ariadne/README.md` reflects the new layout.

### 📦 Required Context Pills
- [DIP Enforcement](../context/dip-enforcement.md)
- [Law 1 - No Blocking I/O](../context/law-1-async.md)

### 🚫 Non-Negotiable Constraints
- **DIP Enforcement:** `ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config` or resolved through `MotorRegistry`.
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
