# Fitness Function 1: Synchronous I/O Detector

**Explanation:** Protect the Event Loop from synchronous blocking calls (open(), requests.get) inside async LangGraph nodes.

**Reference:** `tests/unit/automation/fitness/test_sync_io_detector.py`

**What to fix:** Fixture that monkeypatches builtins.open and tracks calls during graph execution. Fails if any sync I/O detected in hot loop.

**How to do it:**
1. Patch `builtins.open` in test fixture
2. Execute LangGraph flow
3. Assert no sync calls during execution (only at boot)

**Depends on:** none