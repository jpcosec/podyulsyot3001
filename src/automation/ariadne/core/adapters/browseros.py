"""BrowserOS Adapter Implementation — MCP-based Periphery."""

import asyncio
import os
import subprocess
import json
from typing import Optional, Dict, Any, List

import httpx
from src.automation.ariadne.core.periphery import BrowserAdapter
from src.automation.ariadne.contracts.base import (
    BrowserOSCommand,
    ExecutionResult,
    MotorCommand,
    SnapshotResult,
    ScriptCommand
)


class BrowserOSAdapter(BrowserAdapter):
    """
    Implements Sensor, Motor and PeripheralAdapter for BrowserOS via MCP.
    Handles the lifecycle of the BrowserOS AppImage and MCP connectivity.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:9000", appimage_path: Optional[str] = None):
        """
        Initialize the adapter.
        
        Args:
            base_url: The base URL for the BrowserOS MCP server.
            appimage_path: Path to the BrowserOS AppImage for auto-starting.
        """
        self.base_url = base_url
        self.appimage_path = appimage_path or os.environ.get("BROWSEROS_APPIMAGE_PATH")
        self._process: Optional[subprocess.Popen] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def is_healthy(self) -> bool:
        """Checks if the BrowserOS MCP server is responding."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/mcp", timeout=2.0)
                return resp.status_code == 200
        except Exception:
            return False

    async def __aenter__(self) -> "BrowserOSAdapter":
        """
        Ensures BrowserOS is running before entering the context.
        Auto-starts the AppImage if necessary and available.
        """
        if await self.is_healthy():
            return self

        if not self.appimage_path:
            raise RuntimeError(f"BrowserOS not running at {self.base_url} and no BROWSEROS_APPIMAGE_PATH set.")

        print(f"[⚡] Launching BrowserOS from {self.appimage_path}...")
        self._process = subprocess.Popen(
            [self.appimage_path, "--no-sandbox"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Poll for health
        for _ in range(30):
            await asyncio.sleep(1)
            if await self.is_healthy():
                print(f"[✅] BrowserOS ready at {self.base_url}")
                return self

        self._kill_process()
        raise TimeoutError("BrowserOS failed to start within 30s")

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleans up the BrowserOS process if it was started by this adapter."""
        self._kill_process()

    def _kill_process(self):
        if self._process:
            print("[⚡] Terminating BrowserOS process...")
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    async def perceive(self) -> SnapshotResult:
        """Captures the current browser state via BrowserOS take_snapshot MCP tool."""
        try:
            # We use direct HTTP calls to the MCP server for the adapter
            # or we could use load_mcp_tools if we want the abstraction.
            # For simplicity and to avoid circular deps with motors, we use direct calls
            # if the MCP server exposes them, OR we wrap the logic from BrowserOSCliExecutor.
            
            # Since we want to AVOID importing from motors, we reimplement the tool call here
            # using the MCP protocol directly over HTTP if possible, or via a helper.
            # BrowserOS MCP server usually exposes tools via its /mcp endpoint.
            
            # NOTE: For this exercise, we will assume a simplified direct call 
            # or use the pattern from the old executor but within the adapter.
            
            # For now, let's use the load_mcp_tools approach but locally.
            from langchain_mcp_adapters.tools import load_mcp_tools
            tools = await load_mcp_tools(self.base_url + "/mcp")
            tool = next((t for t in tools if t.name == "take_snapshot"), None)
            
            if not tool:
                return SnapshotResult(url="error", dom_elements=[], screenshot_b64=None)
            
            result = await tool.ainvoke({})
            data = self._parse_mcp_result(result)

            return SnapshotResult(
                url=data.get("url", "unknown"),
                dom_elements=data.get("dom_elements", []),
                screenshot_b64=data.get("screenshot_b64")
            )
        except Exception as e:
            return SnapshotResult(url=f"error: {str(e)}", dom_elements=[], screenshot_b64=None)

    async def act(self, command: MotorCommand) -> ExecutionResult:
        """Executes a motor command via BrowserOS MCP tools."""
        if isinstance(command, ScriptCommand):
            return await self._execute_script(command.script)
            
        if not isinstance(command, BrowserOSCommand):
            return ExecutionResult(status="failed", error=f"Unsupported command: {type(command)}")

        try:
            from langchain_mcp_adapters.tools import load_mcp_tools
            tools = await load_mcp_tools(self.base_url + "/mcp")
            tool = next((t for t in tools if t.name == command.tool), None)
            
            if not tool:
                return ExecutionResult(status="failed", error=f"Tool {command.tool} not found")

            tool_inputs = self._map_command_to_inputs(command)
            result = await tool.ainvoke(tool_inputs)
            
            return ExecutionResult(
                status="success",
                extracted_data={"mcp_output": str(result)}
            )
        except Exception as e:
            return ExecutionResult(status="failed", error=str(e))

    async def _execute_script(self, script: str) -> ExecutionResult:
        """Helper to execute arbitrary JS via the 'execute_script' MCP tool."""
        try:
            from langchain_mcp_adapters.tools import load_mcp_tools
            tools = await load_mcp_tools(self.base_url + "/mcp")
            tool = next((t for t in tools if t.name == "execute_script"), None)
            
            if not tool:
                return ExecutionResult(status="failed", error="execute_script tool not found")
                
            result = await tool.ainvoke({"script": script})
            data = self._parse_mcp_result(result)
            
            return ExecutionResult(
                status="success",
                extracted_data=data if isinstance(data, dict) else {"result": data}
            )
        except Exception as e:
            return ExecutionResult(status="failed", error=str(e))

    def _parse_mcp_result(self, result: Any) -> Any:
        """Parses the MCP tool output into a Python object."""
        content = str(result)
        try:
            return json.loads(content)
        except:
            return content

    def _map_command_to_inputs(self, command: BrowserOSCommand) -> Dict[str, Any]:
        """Maps a BrowserOSCommand to MCP tool arguments."""
        if command.tool == "click":
            return {"selector_text": command.selector_text}
        if command.tool == "fill":
            return {"selector_text": command.selector_text, "text": command.value}
        if command.tool == "press":
            return {"key": command.value}
        if command.tool == "upload":
            return {"selector_text": command.selector_text, "file_path": command.value}
        return {}
