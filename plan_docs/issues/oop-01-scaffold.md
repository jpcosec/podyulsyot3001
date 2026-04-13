# OOP 01 — Core Package Scaffold (pure skeleton)

**Umbrella:** `ariadne-oop-skeleton.md`. Blocks OOP 02–08.

### 1. What is wrong
Create the new `src/automation/ariadne/core/` package with empty protocols, ABCs, and class stubs so downstream atoms can be implemented in parallel. No behavior migration yet. Existing code keeps running untouched.

### 2. Reference
`plan_docs/design/ariadne-oop-architecture.md`, `plan_docs/design/design_spec.md`, `src/automation/ariadne/contracts/base.py`

### 3. Real fix
A new `src/automation/ariadne/core/` package with protocols and stubs.

### 4. Steps
1. `core/__init__.py` — re-exports.
2. `core/periphery.py`
   - `Sensor` (`Protocol`) — `async perceive() -> SnapshotResult`, `async is_healthy() -> bool`.
   - `Motor` (`Protocol`) — `async act(command: MotorCommand) -> ExecutionResult`.
   - `BrowserAdapter` (ABC) — implements both protocols, abstract `__aenter__`/`__aexit__` with concrete health poll helper.
3. `core/cognition.py`
   - `Labyrinth` class stub: `identify_room`, `expand`, `load_from_db`.
   - `AriadneThread` class stub: `get_next_step`, `add_step`, `available_missions`, `load_from_db`.
4. `core/actors.py`
   - `Theseus`, `Delphi`, `Recorder`, `Interpreter` stubs with `__init__(...)` accepting dependencies and `async def __call__(self, state) -> dict: raise NotImplementedError`.
5. `core/adapters/__init__.py` — empty.

**Constraints:**
- Pure skeleton. No logic. No imports from `motors/`.
- DTOs (`SnapshotResult`, `MotorCommand`, `ExecutionResult`) stay in `contracts/base.py`; `core/` imports from there.
- `grep -R "from src.automation.motors" src/automation/ariadne/core` must return nothing.

### 5. Test command
1. `python -c "from src.automation.ariadne.core import periphery, cognition, actors"` succeeds.
2. Unit test verifies `BrowserAdapter` is a `Sensor` and `Motor` via `isinstance` on a trivial subclass.
3. Existing tests stay green: `python -m pytest tests/unit/automation/ tests/architecture/ -q`.

### 📦 Required Context Pills
- `plan_docs/context/ariadne-models.md`
- `plan_docs/context/ariadne-thread-model.md`
- `plan_docs/context/dip-enforcement.md`
- `plan_docs/context/interpreter-node.md`
- `plan_docs/context/labyrinth-model.md`
- `plan_docs/context/law-1-async.md`
- `plan_docs/context/motor-contract.md`
- `plan_docs/context/peripheral-adapter-contract.md`
- `plan_docs/context/sensor-contract.md`

### 🚫 Non-Negotiable Constraints
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
- **DIP Enforcement:** `ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config` or resolved through `MotorRegistry`.
