# 🏛️ Refactor: Sensor & Motor Protocol Separation

## 1. Explanation:
The current implementation in `src/automation/ariadne/contracts/base.py` uses a combined `Executor` protocol that has both `execute()` and `take_snapshot()`. This violates the **Sense-Think-Act** architectural loop and the "Laws of Physics" as defined in our context pills, which mandate separate `Sensor` (read-only) and `Motor` (write-only) interfaces.

## 2. Reference:
- `src/automation/ariadne/contracts/base.py:101` (Executor protocol)
- `plan_docs/context/sensor-contract.md`
- `plan_docs/context/motor-contract.md`

## 3. Real fix:
- Split the `Executor` protocol into `Sensor` (with `perceive()`) and `Motor` (with `act()`).
- Update the `PeripheralAdapter` to implement both protocols separately.
- Update any existing code using the old `Executor` interface (e.g., `orchestrator.py`, `hinting.py`).
- Ensure all protocols comply with `STANDARDS.md` (ABCs must list all abstract methods in their class docstring).

## 4. Steps:
1.  Read `src/automation/ariadne/contracts/base.py`.
2.  Refactor `Executor` into `Sensor` and `Motor`.
3.  Ensure `SnapshotResult` and `ExecutionResult` are used as the return types respectively.
4.  Update class docstrings for the new protocols to list abstract methods.
5.  Update `src/automation/ariadne/graph/orchestrator.py` to use `sensor` and `motor` separately from config.
6.  Update `src/automation/ariadne/capabilities/hinting.py` to take a `sensor` instead of an `executor`.

## 5. Test command:
`python -m pytest tests/architecture/test_domain_isolation.py -v`

### 📦 Required Context Pills:
- `plan_docs/context/sensor-contract.md`
- `plan_docs/context/motor-contract.md`
- `plan_docs/context/peripheral-adapter-contract.md`
- `plan_docs/context/dip-enforcement.md`

### 🚫 Non-Negotiable Constraints:
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`.
- **DIP Enforcement:** Domain layers (`ariadne`) MUST NOT import from infrastructure layers (`motors`).
