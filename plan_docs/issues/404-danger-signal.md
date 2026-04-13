# 404 / Error Page Danger Signal in Theseus.perceive

**Umbrella:** depends on `ariadne-oop-skeleton.md`.

### 1. Explanation
 HTTP error pages (404, 403, 500) must be detected as named danger signals inside `Theseus.__call__` right after `Sensor.perceive()` and short-circuit to `Delphi`/HITL — not silently treated as `current_state_id = "unknown"` and fed through `Labyrinth`/`AriadneThread`.

### 2. Reference
 `src/automation/ariadne/danger_contracts.py` (`ApplyDangerSignals`), `src/automation/ariadne/core/actors.py` (`Theseus`), `src/automation/ariadne/core/periphery.py` (`Sensor`)

**Status:** Not started. Existing danger routing only checks CAPTCHA/block patterns. 404 pages currently fall through deterministic execution, waste cascade cycles, and burn agent tokens before hitting HITL.

**Why it's wrong:** A 404 means the target resource is gone. Sending it through `execute_deterministic → heuristics → agent (3 retries)` wastes tokens and time before the inevitable HITL escalation.

### 3. Real fix

1. In `Theseus.__call__`, after `Sensor.perceive()`, check `SnapshotResult.metadata` or `SnapshotResult.page_title` for HTTP error signals (e.g., '404', 'Not Found', or status code if available in the adapter's perception): page title contains "404", "Not Found", "403 Forbidden", "500", etc., or the URL didn't resolve.
2. Add these patterns to `ApplyDangerSignals` (or a new `NavigationDangerSignals`).
3. Set `danger_detected = True` and `danger_type = "http_error"` in state.
4. Graph routing: if `danger_type == "http_error"` → route directly to `human_in_the_loop`, skipping `Labyrinth` lookups and `Delphi` retries.

**Don't:** Let HTTP error pages reach `AriadneThread.get_next_step()`. They have no valid transition.

### 4. Steps
1. Update `Theseus` to check `SnapshotResult` for 404 patterns.
2. Add `http_error` to `danger_type`.
3. Update graph routing to short-circuit 404s to HITL.

### 5. Test command
Run a mission against a known 404 URL and assert it hits HITL immediately.

### 📦 Required Context Pills
- [Danger Signal & Short-Circuit Pattern](../context/danger-signal-pattern.md)
- [Error Contract](../context/error-contract.md)
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Law 4 - Finite Routing](../context/law-4-finite-routing.md)
- [Ariadne State & Models](../context/ariadne-models.md)

### 🚫 Non-Negotiable Constraints
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
- **Law 4 (Finite Routing):** All loops must have finite circuit breakers. Escalation through counters (heuristic_retries >= 2, agent_failures >= 3) to HITL is mandatory.
