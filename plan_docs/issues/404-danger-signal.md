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

**Steps:**
1. Add HTTP error text patterns to danger signals.
2. Update `observe_node` to check these patterns post-snapshot.
3. Update `route_after_observe` to handle `"http_error"` danger type.
4. Write test: mock a 404 page snapshot, assert graph routes to HITL without touching `execute_deterministic`.
