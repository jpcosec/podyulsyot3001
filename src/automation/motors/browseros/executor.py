from typing import Any, Dict, Optional, cast
from langchain_mcp_adapters.tools import load_mcp_tools
from src.automation.ariadne.models import BrowserOSCommand, ExecutionResult, MotorCommand
from src.automation.ariadne.contracts.base import Executor


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
