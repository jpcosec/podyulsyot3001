# Set-of-Mark: Agent Prompt and Hint Consumption

**Explanation:** The rescue agent must be updated to use the hints dictionary and the annotated screenshot provided by the `observe_node`.

**Reference:** `src/automation/ariadne/graph/nodes/agent.py`

**Depends on:** `som-hint-injection.md`

**Status:** Not started.

### 📦 Required Context Pills
- [Set-of-Mark (SoM) Pattern](../context/som-pattern.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Node Implementation Pattern](../context/node-pattern.md)

### 🚫 Non-Negotiable Constraints (Laws of Physics)

1. **Law 1 (No Blocking I/O):** Agent reasoning logic must be `async`.
2. **MCP Only:** Agent MUST only use the BrowserOS MCP toolset to interact with hints.

**Real fix:**
1. Update `agent.py` to check for `state["session_memory"]["hints"]`.
2. If hints exist, add the hint dictionary to the agent's prompt.
3. Instruct the agent to reference elements using their `[AA]` labels and the `click_hint` / `fill_hint` MCP tools.

**Steps:**
1. Update the agent prompt builder.
2. Ensure the annotated `screenshot_b64` is passed to the VLM.
3. Test: assert the agent's prompt contains hint labels when available in `session_memory`.

**Test command:**
`python -m pytest tests/unit/automation/ariadne/test_hinting.py -v`
