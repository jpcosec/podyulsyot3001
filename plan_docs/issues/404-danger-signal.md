# 404 / Error Page Danger Signal in observe_node

**Explanation:** HTTP error pages (404, 403, 500) must be detected as named danger signals in `observe_node` and short-circuit to HITL — not silently treated as `current_state_id = "unknown"` and fed into the deterministic cascade.

**Reference:** `src/automation/ariadne/danger_contracts.py` (`ApplyDangerSignals`), `src/automation/ariadne/graph/orchestrator.py` (`observe_node`, `route_after_observe`)

**Status:** Not started. `route_after_observe` only checks CAPTCHA/block patterns. 404 pages fall through to `execute_deterministic` which fires `NoTransitionError`, wastes cascade cycles, and burns agent tokens before hitting HITL.

**Why it's wrong:** A 404 means the target resource is gone. Sending it through `execute_deterministic → heuristics → agent (3 retries)` wastes tokens and time before the inevitable HITL escalation.

**Real fix:**
1. In `observe_node`, after snapshot, check for HTTP error signals: page title contains "404", "Not Found", "403 Forbidden", "500", etc., or the URL didn't resolve.
2. Add these patterns to `ApplyDangerSignals` (or a new `NavigationDangerSignals`).
3. Set `danger_detected = True` and `danger_type = "http_error"` in state.
4. In `route_after_observe`: if `danger_type == "http_error"` → route directly to `human_in_the_loop`.

**Don't:** Let HTTP error pages reach `execute_deterministic`. They have no valid transition in any map.

### 📦 Required Context Pills
- [Danger Signal & Short-Circuit Pattern](../context/danger-signal-pattern.md)
- [Error Contract](../context/error-contract.md)
- [Ariadne State & Models](../context/ariadne-models.md)

### 🚫 Non-Negotiable Constraints
- **Law 4 (Finite Routing):** Danger signals MUST short-circuit to HITL or Rescue Agent immediately. Do not enter the deterministic cascade if a 404/500 is detected.
- **Law 1 (No Blocking I/O):** Danger detection logic must be `async`.
