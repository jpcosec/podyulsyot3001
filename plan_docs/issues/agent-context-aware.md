# Agent Node: Context-Aware Prompt

**Explanation:** The rescue agent must know the user's original instruction and active mission. Currently its goal is hardcoded and context-blind.

**Reference:** `src/automation/ariadne/graph/nodes/agent.py:34-36`

**Status:** Partial — agent works but ignores user intent.

### 📦 Required Context Pills
- [Node Implementation Pattern](../context/node-pattern.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Log Tags & Observability](../context/log-tags.md)
- [BrowserOS MCP Contract](../context/browseros-mcp-contract.md)

### 🚫 Non-Negotiable Constraints (Laws of Physics)

1. **Law 1 (No Blocking I/O):** The agent node must be fully `async`. Do not use `time.sleep()` for LLM retries or synchronous file I/O for logs.
2. **Law 4 (Finite Routing):** The agent node must update `session_memory["agent_failures"]` on each failed attempt. If failures >= 3, the orchestrator MUST route to `human_in_the_loop`.
3. **DIP Enforcement:** `agent.py` must only import from `ariadne/` domain layers. It must NEVER import from `src/automation/motors/`.

**Why it's wrong:**
```python
prompt += "Goal: Continue the application process.\n"
```
This is hardcoded regardless of whether the user said "busca trabajos", "postula", or "extrae datos". When the agent is invoked for a discovery mission it will still try to "continue the application process", leading to wrong actions.

**Real fix:**
Replace lines 34–36 in `agent.py` with:
```python
prompt += f"Mission: {state.get('current_mission_id', 'unknown')}\n"
prompt += f"User Instruction: {state.get('instruction', 'Explore the page and decide the next action.')}\n"
prompt += "Analyze the screenshot with injected [AA] hints and decide the next action."
```

**Don't:** Hardcode any domain-specific goal string in the agent prompt.

**Steps:**
1. Edit `agent.py:34-36` with context-aware strings.
2. Verify `instruction` and `current_mission_id` are present in `AriadneState` (depends on `interpreter-node` issue).
3. Write a test that asserts the prompt contains the state's `instruction` field.
