# LangGraph MCP Adapter Integration Is Not Evaluated

**Explanation:** BrowserOS `/chat` remains a best-effort surface, and the repository currently lacks a stronger graph/agent orchestration path that could use MCP directly instead of relying on BrowserOS chat semantics for higher-level agent workflows. LangGraph already has MCP adapter support via `langchain-mcp-adapters`, but this repository has not yet evaluated whether that adapter should be used as the canonical graph-side MCP integration path.

Reference provided by the user:
- `https://github.com/langchain-ai/langchain-mcp-adapters`

This matters because a LangGraph + MCP adapter path may be a more stable long-term answer for agent orchestration than treating BrowserOS `/chat` as a durable runtime contract.

**Reference:**
- `docs/automation/browseros_chat_runtime_support.md`
- `src/automation/motors/browseros/`
- `https://github.com/langchain-ai/langchain-mcp-adapters`

**What to fix:** Evaluate whether LangGraph MCP adapters should be adopted for agent orchestration in this repository and document the decision, scope, and migration implications.

**How to do it:**
1. Review the LangGraph/LangChain MCP adapter capabilities against current BrowserOS and Ariadne workflows.
2. Identify which current `/chat`-dependent or agent-style workflows could be replaced or strengthened by MCP adapter integration.
3. Document whether the adapter should be adopted, prototyped, or explicitly rejected.
4. If adoption is recommended, split follow-up implementation work into smaller child issues.

**Depends on:** none
