# EPIC 5: LangGraph MCP Rescue Agent (The Planner)

**Explanation:** Implement the Level 3 intelligence layer that talks directly to BrowserOS MCP via `langchain-mcp-adapters`.

**Tasks:**
1.  **MCP Tool Adapter**: Configure `langchain-mcp-adapters` to expose BrowserOS tools (click, type, upload) to the LangChain agent.
2.  **Rescue Node**: Implement the `LLMRescueAgent` node that receives the screenshot + DOM and decides the next action.
3.  **Trace Generation**: Ensure the agent's actions are recorded in a format that can be promoted to the canonical graph.
4.  **Circuit Breaker**: Implement the routing logic to HITL after N consecutive agent failures.

**Success Criteria:**
- The agent can autonomously find and click a moved "Apply" button.
- Agent sessions are persisted and ready for map promotion.

**Depends on:** `epic-4-jit-graph.md`
