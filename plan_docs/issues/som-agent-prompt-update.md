# Set-of-Mark: Delphi Prompt and Hint Consumption

**Umbrella:** depends on `ariadne-oop-skeleton.md`, `som-hint-injection.md`.

**Explanation:** `Delphi` must consume the hints dictionary and the annotated screenshot produced by `Theseus`/`Sensor` and reference elements via their `[AA]` labels.

**Reference:** `src/automation/ariadne/core/actors.py` (`Delphi`)

**Status:** Not started.

### 📦 Required Context Pills
- [Set-of-Mark (SoM) Pattern](../context/som-pattern.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Node Implementation Pattern](../context/node-pattern.md)

### 🚫 Non-Negotiable Constraints (Laws of Physics)

1. **Law 1 (No Blocking I/O):** Agent reasoning logic must be `async`.
2. **MCP Only:** Agent MUST only use the BrowserOS MCP toolset to interact with hints.

**Real fix:**
1. `Delphi.__call__` checks `state["session_memory"]["hints"]`.
2. If hints exist, inject the hint dictionary into the LLM prompt.
3. Instruct the LLM to reference elements using their `[AA]` labels and to emit `click_hint` / `fill_hint` tool calls routed through `Motor.act()`.

**Steps:**
1. Update the agent prompt builder.
2. Ensure the annotated `screenshot_b64` is passed to the VLM.
3. Test: assert the agent's prompt contains hint labels when available in `session_memory`.

**Test command:**
`python -m pytest tests/unit/automation/ariadne/test_hinting.py -v`
