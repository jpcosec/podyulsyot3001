"""BrowserOS Adapter Implementation — MCP-based Periphery."""

import json
import os
import subprocess
import asyncio
from typing import Any, Dict, Optional

import httpx
from src.automation.ariadne.core.periphery import BrowserAdapter
from src.automation.ariadne.contracts.base import (
    BrowserOSCommand,
    ExecutionResult,
    MotorCommand,
    SnapshotResult,
    ScriptCommand,
)


class BrowserOSAdapter(BrowserAdapter):
    """
    Implements Sensor, Motor and PeripheralAdapter for BrowserOS via MCP.
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

    async def __aenter__(self) -> "BrowserOSAdapter":
        """Ensure BrowserOS is running before entering the context."""
        if await self.is_healthy():
            return self

        if not self.appimage_path:
            raise RuntimeError(
                f"BrowserOS not running at {self.base_url} and no BROWSEROS_APPIMAGE_PATH set."
            )

        print(f"[⚡] Launching BrowserOS from {self.appimage_path}...")
        self._process = subprocess.Popen(
            [self.appimage_path, "--no-sandbox"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

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

    async def perceive(self) -> SnapshotResult:
        """Captures the current browser state via the MCP snapshot tool."""
        tools = await self._get_tools()
        tool = next((item for item in tools if item.name == "take_snapshot"), None)
        if tool is None:
            return SnapshotResult(url="error", dom_elements=[], screenshot_b64=None)

        try:
            result = await tool.ainvoke({})
            data = self._parse_mcp_result(result)
        except Exception as exc:
            return SnapshotResult(
                url=f"error: {exc}", dom_elements=[], screenshot_b64=None
            )

        if not isinstance(data, dict):
            data = {}
        return SnapshotResult(
            url=data.get("url", "unknown"),
            dom_elements=data.get("dom_elements", []),
            screenshot_b64=data.get("screenshot_b64"),
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
                return ExecutionResult(
                    status="failed",
                    error=f"Tool {command.tool} not found",
                )
            result = await tool.ainvoke(self._map_command_to_inputs(command))
        except Exception as exc:
            return ExecutionResult(status="failed", error=str(exc))

        return ExecutionResult(
            status="success", extracted_data={"mcp_output": str(result)}
        )

    async def take_snapshot(self) -> SnapshotResult:
        """Backward-compatible alias for the legacy graph interface."""
        return await self.perceive()

    async def execute(self, command: MotorCommand) -> ExecutionResult:
        """Backward-compatible alias for the legacy graph interface."""
        return await self.act(command)

    async def _get_tools(self):
        from langchain_mcp_adapters.tools import load_mcp_tools

        return await load_mcp_tools(f"{self.base_url}/mcp")

    def _kill_process(self) -> None:
        if self._process:
            print("[⚡] Terminating BrowserOS process...")
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
                return ExecutionResult(
                    status="failed", error="execute_script tool not found"
                )

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
