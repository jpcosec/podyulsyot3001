"""BrowserOS Adapter Implementation — MCP-based Periphery."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from typing import Any, Dict, Optional

import httpx
from src.automation.ariadne.contracts.base import (
    BrowserOSCommand,
    ExecutionResult,
    MotorCommand,
    SnapshotResult,
    ScriptCommand,
)
from src.automation.ariadne.core.periphery import BrowserAdapter


class BrowserOSAdapter(BrowserAdapter):
    """
    Implements Sensor and Motor via BrowserOS MCP tools.
    Handles the lifecycle of the BrowserOS AppImage and MCP connectivity.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:9000",
        appimage_path: Optional[str] = None,
    ):
        """Initialize the adapter."""
        self.base_url = base_url
        self.appimage_path = appimage_path or os.environ.get("BROWSEROS_APPIMAGE_PATH")
        self._process: Optional[subprocess.Popen] = None

    async def is_healthy(self) -> bool:
        """Checks if the BrowserOS MCP server is responding."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/mcp", timeout=2.0)
                return resp.status_code == 200
        except Exception:
            return False

    async def __aenter__(self) -> BrowserOSAdapter:
        """Ensure BrowserOS is running before entering the context."""
        if await self.is_healthy():
            return self

        if not self.appimage_path:
            raise RuntimeError(
                f"BrowserOS not running at {self.base_url} and no BROWSEROS_APPIMAGE_PATH set."
            )

        self._process = subprocess.Popen(
            [self.appimage_path, "--no-sandbox"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        for _ in range(30):
            await asyncio.sleep(1)
            if await self.is_healthy():
                return self

        self._kill_process()
        raise TimeoutError("BrowserOS failed to start within 30s")

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleans up the BrowserOS process."""
        self._kill_process()

    async def perceive(self) -> SnapshotResult:
        """Captures the current browser state via the MCP snapshot tool."""
        try:
            tools = await self._get_tools()
            tool = next((item for item in tools if item.name == "take_snapshot"), None)
            if tool is None:
                return SnapshotResult(url="error: tool not found", dom_elements=[], screenshot_b64=None)

            result = await tool.ainvoke({})
            data = self._parse_mcp_result(result)
            
            if not isinstance(data, dict):
                return SnapshotResult(url="error: invalid response", dom_elements=[], screenshot_b64=None)
                
            return SnapshotResult(
                url=data.get("url", "unknown"),
                dom_elements=data.get("dom_elements", []),
                screenshot_b64=data.get("screenshot_b64"),
            )
        except Exception as exc:
            return SnapshotResult(
                url=f"error: {exc}", dom_elements=[], screenshot_b64=None
            )

    async def act(self, command: MotorCommand) -> ExecutionResult:
        """Executes a motor command via BrowserOS MCP tools."""
        if isinstance(command, ScriptCommand):
            return await self._execute_script(command.script)
            
        if not isinstance(command, BrowserOSCommand):
            return ExecutionResult(
                status="failed",
                error=f"Unsupported command: {type(command)}",
            )

        try:
            tools = await self._get_tools()
            tool = next((item for item in tools if item.name == command.tool), None)
            if tool is None:
                return ExecutionResult(status="failed", error=f"Tool {command.tool} not found")
            
            inputs = self._map_command_to_inputs(command)
            result = await tool.ainvoke(inputs)
            
            # BrowserOS tools usually return a string report or JSON.
            # We assume success if no exception was raised by ainvoke.
            return ExecutionResult(
                status="success", extracted_data={"mcp_output": str(result)}
            )
        except Exception as exc:
            return ExecutionResult(status="failed", error=str(exc))

    async def _get_tools(self):
        from langchain_mcp_adapters.tools import load_mcp_tools
        return await load_mcp_tools(f"{self.base_url}/mcp")

    def _kill_process(self) -> None:
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    async def _execute_script(self, script: str) -> ExecutionResult:
        """Helper to execute arbitrary JS via the 'execute_script' MCP tool."""
        try:
            tools = await self._get_tools()
            tool = next((t for t in tools if t.name == "execute_script"), None)
            if not tool:
                return ExecutionResult(status="failed", error="execute_script tool not found")

            result = await tool.ainvoke({"script": script})
            data = self._parse_mcp_result(result)
            return ExecutionResult(
                status="success",
                extracted_data=data if isinstance(data, dict) else {"result": data},
            )
        except Exception as exc:
            return ExecutionResult(status="failed", error=str(exc))

    def _parse_mcp_result(self, result: Any) -> Any:
        """Parses the MCP tool output into a Python object."""
        content = str(result)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
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
