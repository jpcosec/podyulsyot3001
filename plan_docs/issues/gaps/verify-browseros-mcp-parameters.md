# Verify: BrowserOS MCP Parameters

**Explanation:** The `BrowserOSCliExecutor` in `src/automation/motors/browseros/executor.py` maps Ariadne intents to MCP tool calls (e.g., `click`, `fill`). We must ensure that the arguments passed to these tools (like `selector_text`, `text`, `file_path`) match the actual schema expected by the BrowserOS MCP server at port 9000.

**Reference:** 
- `src/automation/motors/browseros/executor.py`
- BrowserOS MCP Documentation (if available) or live discovery.

**What to fix:** Perfect alignment between the executor's `ainvoke` calls and the MCP tool definitions.

**How to do it:**
1.  Perform a live discovery of MCP tools using `load_mcp_tools`.
2.  Inspect the arguments for `click`, `fill`, `type_text`, `upload_file`, etc.
3.  Update the mapping logic in `BrowserOSCliExecutor.execute` to use the correct parameter names.
4.  Implement `take_snapshot` using the MCP `take_snapshot` tool and map the results to `SnapshotResult`.

**Depends on:** none
