---
type: decision
domain: scraping
source: docs/adrs/2026-04-09-browseros-mcp-is-the-canonical-rescue-contract.md
---

# Pill: BrowserOS MCP Contract

## Decision
The "Rescue" agent MUST interact with portals exclusively through the BrowserOS MCP (Model Context Protocol) toolset.

## Rationale
Standardizing on MCP tools (like `click_element`, `fill_form`) creates a clean interface that works across any VLM (Gemini, Claude, GPT). It prevents the agent from generating raw JS or Playwright code, which is brittle and hard to validate.

## Trade-offs
- Limited to the actions exposed by the MCP.
- Requires a running MCP server (`local-server` at `:9000`).

## Do not reverse unless
A more universal, vendor-neutral protocol for browser manipulation replaces MCP.
