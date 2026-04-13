# OOP 08b — Package Locality + Contract Split

**Umbrella:** `ariadne-oop-skeleton.md`. Depends on `oop-07-graph-wiring.md`. Must land before `oop-08-cleanup.md`.

### 1. Explanation
Phase 0.5 currently maps behavior into the right classes, but several support files still sit in overly central locations (`contracts/base.py`, `models.py`, `io.py`, `config.py`, `capabilities/hinting.py`). That leaves ownership blurry and keeps the old flat package shape alive.

### 2. Reference
`plan_docs/issues/ariadne-oop-skeleton.md`, `src/automation/ariadne/contracts/base.py`, `src/automation/ariadne/models.py`, `src/automation/ariadne/io.py`, `src/automation/ariadne/config.py`, `src/automation/ariadne/capabilities/hinting.py`, `src/automation/ariadne/danger_contracts.py`

### 3. Real fix
Apply a two-tier placement rule: owner-local by default, with a tiny central contract layer only for DTOs that truly cross multiple owner boundaries.

### 4. Steps
1. Split `contracts/base.py` by ownership.
   - Periphery-facing contracts (`Sensor`, `Motor`, `PeripheralAdapter`, `SnapshotResult`, `ExecutionResult`, `MotorCommand`, transport command DTOs) move next to `core/periphery.py` or a tightly related periphery contract module.
   - Hint/planner contracts move near `Delphi` or the rescue subsystem if still needed.
   - Keep a central contract module only for DTOs that are demonstrably shared across multiple owner boundaries.
2. Split `models.py` by ownership.
   - Labyrinth/map structures move near `Labyrinth`.
   - Thread/mission/state structures move near `AriadneThread` or graph state if they are true runtime state DTOs.
   - Keep only genuinely cross-cutting models in a small shared location.
3. Relocate `io.py` out of the Ariadne root.
   - Persistence helpers move under owner-specific or shared storage modules, not a generic top-level utility file.
   - `Recorder`, `Labyrinth`, and `AriadneThread` should depend on storage APIs with clear ownership.
4. Relocate `config.py` to runtime infrastructure.
   - Construction/bootstrap code may read config directly.
   - Actor call paths should consume injected values, not pull config ad hoc.
5. Relocate `capabilities/hinting.py` under the `Delphi`/rescue ownership boundary unless a narrower shared abstraction is justified.
6. Audit orphan or quasi-orphan files while relocating.
   - If a file has only test references or a single transitional caller, either fold it into its owner or mark it for OOP 08 deletion.

### 4.1 Serena AST refactor operations
- Use `get_symbols_overview` on `contracts/base.py`, `models.py`, `io.py`, `config.py`, and `capabilities/hinting.py` to partition symbols by owner before editing.
- Use `find_referencing_symbols` for `AriadneIntent`, `SnapshotResult`, `ExecutionResult`, `MotorCommand`, `HintingToolImpl`, and any moved model class to decide whether it belongs in an owner-local module or the tiny central contract layer.
- Use `insert_before_symbol` / `insert_after_symbol` to create owner-local contract/model modules near `core/periphery.py`, `core/cognition.py`, and `core/actors.py`.
- Use `replace_symbol_body` or `serena_replace_content` to convert old modules into temporary compatibility shims only when multiple downstream references still exist.
- Before deleting a source file, use `find_referencing_symbols` on its exported symbols; zero-runtime-use files become OOP 08 cleanup targets.

### 5. Test command
1. No new top-level Ariadne root helper module is introduced as a dumping ground.
2. Core actors do not read runtime config ad hoc during `__call__`.
3. Shared contract modules are smaller and contain only genuinely cross-boundary DTOs.
4. `python -m pytest tests/unit/automation/ tests/architecture/ -q` green.

### 📦 Required Context Pills
- `plan_docs/context/ariadne-models.md`
- `plan_docs/context/dip-enforcement.md`
- `plan_docs/context/law-1-async.md`

### 🚫 Non-Negotiable Constraints
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
- **DIP Enforcement:** `ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config` or resolved through `MotorRegistry`.
- **Package Locality Rule:** owner-local by default; central contracts only for true cross-boundary DTOs.
