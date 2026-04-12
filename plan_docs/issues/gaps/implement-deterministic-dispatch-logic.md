# Implement: Deterministic Dispatch Logic

**Explanation:** The `execute_deterministic_node` in `orchestrator.py` contains a TODO for the executor call. It currently mocks success without actually sending commands to the motors.

**Reference:** 
- `src/automation/ariadne/graph/orchestrator.py`
- `src/automation/motors/registry.py`

**What to fix:** Logic that selects the correct Executor from the registry, dispatches the JIT `MotorCommand`, and handles the `ExecutionResult`.

**How to do it:**
1.  Inject the `MotorRegistry` into the node (or use it statically).
2.  Based on the current edge intent and target, call the JIT Translator.
3.  Send the translated command to the chosen Executor.
4.  Capture the `ExecutionResult` and update the state's `errors` list if it fails.

**Depends on:** `plan_docs/issues/gaps/implement-observe-node-logic.md`
