# Set-of-Mark: Hint Injection in Sensor.perceive

**Umbrella:** depends on `ariadne-oop-skeleton.md`.

**Explanation:** The `Sensor` (or a `HintingCapability` injected into `Theseus`) must inject hint labels (`[AA]`, `[AB]`) into the UI before capturing the final screenshot that `Delphi` will consume.

**Reference:** `src/automation/ariadne/core/periphery.py` (`Sensor`), `src/automation/ariadne/core/actors.py` (`Theseus`), `src/automation/ariadne/capabilities/hinting.js`

**Status:** Not started.

### 📦 Required Context Pills
- [Set-of-Mark (SoM) Pattern](../context/som-pattern.md)
- [Law 3 — DOM Hostility](../context/law-3-dom-hostility.md)
- [Node Implementation Pattern](../context/node-pattern.md)
- [Ariadne State & Models](../context/ariadne-models.md)

### 🚫 Non-Negotiable Constraints (Laws of Physics)

1. **Law 1 (No Blocking I/O):** `HintingTool.inject_hints()` and `take_snapshot()` MUST be `async`.
2. **Law 3 (DOM Hostility):** `hinting.js` must NEVER use `appendChild` or `innerHTML` on existing page elements. It must attach to a single root overlay anchored to `document.body`.

**Real fix:**
1. `Theseus.__call__` calls `self.sensor.perceive()`, then invokes an injected `HintingCapability` that overlays hint labels, then re-captures the snapshot.
2. Store the hints dictionary in `state["session_memory"]["hints"]`.
3. Store the annotated screenshot in `state["screenshot_b64"]` so `Delphi` consumes it.

**Steps:**
1. Update `observe_node`.
2. Ensure `session_memory` is updated with the hint map.
3. Test: assert `session_memory["hints"]` is populated after an observation.

**Test command:**
`python -m pytest tests/unit/automation/ariadne/test_observe_node.py -v`
