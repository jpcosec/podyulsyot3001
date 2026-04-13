# Test Suite Realignment For OOP Skeleton

**Umbrella:** depends on `ariadne-oop-skeleton.md`, `oop-08b-package-locality.md`, `oop-08-cleanup.md`. Run only after the refactor is structurally complete.

### 1. Explanation
The current test suite still targets transitional seams (`observe_node`, `ModeRegistry`, `MapRepository`, legacy executors, legacy hinting placement) rather than the target OOP ownership model. This makes the suite noisy during refactor work and encourages compatibility shims instead of clean package boundaries.

### 2. Reference
`plan_docs/issues/ariadne-oop-skeleton.md`, `tests/unit/automation/ariadne/test_orchestrator.py`, `tests/unit/automation/ariadne/test_state_identification.py`, `tests/unit/automation/ariadne/test_observe_node.py`, `tests/unit/automation/ariadne/test_heuristics.py`, `tests/unit/automation/motors/test_browseros_executor.py`, `tests/unit/automation/motors/test_crawl4ai_executor.py`

### 3. Real fix
Rebuild the suite around final ownership boundaries: adapters, cognition, actors, graph wiring, storage, and runtime infrastructure. Remove or merge legacy tests that only assert temporary compatibility seams.

### 4. Steps
1. Freeze broad test rewrites until Phase 0.5 refactor is complete.
   - During OOP atoms, only run narrow smoke validation needed to keep the current work moving.
   - Do not spend time preserving legacy test shape while ownership is still changing.
2. Replace legacy seam tests with owner-aligned tests.
   - `test_observe_node.py`, `test_state_identification.py`, `test_heuristics.py` -> split into actor/cognition tests.
   - `test_orchestrator.py` -> shrink to graph wiring and routing only.
   - `test_browseros_executor.py`, `test_crawl4ai_executor.py` -> migrate to adapter-focused tests.
   - `test_repository.py`, `test_recording_and_promotion.py`, hinting tests -> relocate to storage/recorder/delphi ownership.
3. Adopt target layout.
   - `tests/unit/automation/ariadne/core/test_adapters.py`
   - `tests/unit/automation/ariadne/core/test_cognition.py`
   - `tests/unit/automation/ariadne/core/test_actors.py`
   - `tests/unit/automation/ariadne/graph/test_wiring.py`
   - storage/runtime test modules once those packages exist
4. Merge or delete overlapping legacy files.
   - `test_state_identification.py` and `test_observe_node.py` should not both survive in their current form.
   - `test_modes.py` / `test_mode_registry.py` should survive only if mode strategies remain a real boundary after OOP 08.
   - `test_hinting.py` survives only if hinting remains a first-class owned module after package locality work.
5. Update fixtures/mocks.
   - Prefer fake adapters, fake cognition objects, and actor-level state fixtures over patching global registries and repository methods.
   - Minimize patching `ModeRegistry`, `MapRepository`, and root module functions.
6. Run the full suite only after the structural move is done.
   - Unit tests, then architecture tests, then any live/manual validation issues.

### 4.1 Serena AST refactor operations
- Use `get_symbols_overview` and file-length scan on `tests/unit/automation/ariadne/` and `tests/unit/automation/motors/` to identify oversized mixed-concern test files before editing.
- Use `search_for_pattern` / `find_referencing_symbols` to group tests by legacy seam (`observe_node`, `create_ariadne_graph`, `ModeRegistry`, `MapRepository`, `HintingToolImpl`, executor classes).
- Use file edits to split oversized test files into owner-aligned modules once the final code ownership is stable.
- Delete or merge legacy test files only after references and replacement coverage are clear.

### 5. Test command
Deferred until the refactor is complete.

Recommended final validation sequence:
1. `python -m pytest tests/unit/automation/ -q`
2. `python -m pytest tests/architecture/ -q`
3. targeted live/manual validation from downstream issues

### 📦 Required Context Pills
- `plan_docs/context/actor-pattern.md`
- `plan_docs/context/ariadne-models.md`
- `plan_docs/context/labyrinth-model.md`
- `plan_docs/context/ariadne-thread-model.md`
- `plan_docs/context/peripheral-adapter-pattern.md`

### 🚫 Non-Negotiable Constraints
- **Ownership First:** tests must mirror the final code ownership model, not temporary migration shims.
- **No Premature Suite Stabilization:** avoid broad test rewrites until the refactor settles; only do minimal targeted checks needed to keep implementation moving.
- **Test Structure Mirror:** final tests must mirror the `src/` structure per `STANDARDS.md`.
