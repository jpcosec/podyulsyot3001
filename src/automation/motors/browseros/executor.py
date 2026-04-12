from typing import Any, Dict, Optional, cast
import json
from langchain_mcp_adapters.tools import load_mcp_tools
from src.automation.ariadne.contracts.base import (
    BrowserOSCommand,
    ExecutionResult,
    Executor,
    MotorCommand,
    SnapshotResult,
)


class BrowserOSCliExecutor(Executor):
    """
    Executor for BrowserOS via MCP.
    Dumb slave that runs one tool call at a time.
    """

    def __init__(self, mcp_url: str = "http://127.0.0.1:9000/mcp"):
        self.mcp_url = mcp_url
        self._tools_cache = None

    async def _get_tools(self):
        if self._tools_cache is None:
            self._tools_cache = await load_mcp_tools(self.mcp_url)
        return self._tools_cache

    async def take_snapshot(self) -> SnapshotResult:
        """Fetch the current page URL, accessibility tree (DOM), and a base64 screenshot via MCP."""
        try:
            tools = await self._get_tools()
            tool = next((t for t in tools if t.name == "take_snapshot"), None)
            
            if not tool:
                # Fallback or error if tool is missing
                return SnapshotResult(url="error", dom_elements=[], screenshot_b64=None)
            
            result = await tool.ainvoke({})
            
            # MCP results from langchain-mcp-adapters are usually strings or list of content blocks
            # We assume the tool returns a JSON string or we can parse it.
            # If result is a list of content blocks (common in MCP), we extract the text.
            data = {}
            if isinstance(result, list):
                # result is likely List[ToolMessage] or similar, but with load_mcp_tools it might be simpler
                # Actually tool.ainvoke(tool_inputs) returns the tool output.
                # In langchain_mcp_adapters, it's usually the 'content' of the ToolMessage.
                content = str(result)
                try:
                    data = json.loads(content)
                except:
                    # If not JSON, it's probably raw output. 
                    # This depends on how BrowserOS take_snapshot tool is implemented.
                    # For now, let's assume it returns a dict or JSON string.
                    pass
            elif isinstance(result, str):
                try:
                    data = json.loads(result)
                except:
                    pass
            elif isinstance(result, dict):
                data = result

            return SnapshotResult(
                url=data.get("url", "unknown"),
                dom_elements=data.get("dom_elements", []),
                screenshot_b64=data.get("screenshot_b64")
            )
        except Exception as e:
            print(f"Error taking snapshot: {e}")
            return SnapshotResult(url=f"error: {str(e)}", dom_elements=[], screenshot_b64=None)

    async def execute(self, command: MotorCommand) -> ExecutionResult:
        if not isinstance(command, BrowserOSCommand):
            return ExecutionResult(
                status="failed",
                error=f"BrowserOSCliExecutor only handles BrowserOSCommand, got {type(command)}"
            )

        try:
            tools = await self._get_tools()
            tool_name = command.tool
            
            # Find the requested tool
            tool = next((t for t in tools if t.name == tool_name), None)
            
            if not tool:
                return ExecutionResult(
                    status="failed",
                    error=f"MCP tool '{tool_name}' not found at {self.mcp_url}"
                )
            
            # Prepare tool inputs
            # Map BrowserOSCommand fields to MCP tool parameters
            tool_inputs = {}
            if tool_name == "click":
                tool_inputs = {"selector_text": command.selector_text}
            elif tool_name == "fill":
                tool_inputs = {"selector_text": command.selector_text, "text": command.value}
            elif tool_name == "press":
                tool_inputs = {"key": command.value}
            elif tool_name == "upload":
                tool_inputs = {"selector_text": command.selector_text, "file_path": command.value}
            else:
                # Fallback for unknown tools: try to pass both if they exist
                tool_inputs = {"selector_text": command.selector_text}
                if command.value:
                    tool_inputs["text"] = command.value

            # Execute the tool
            result = await tool.ainvoke(tool_inputs)
            
            return ExecutionResult(
                status="success",
                extracted_data={"mcp_output": str(result)}
            )
            
        except Exception as e:
            return ExecutionResult(
                status="failed",
                error=f"BrowserOS MCP Execution Error: {str(e)}"
            )
