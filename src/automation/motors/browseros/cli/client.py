"""BrowserOS MCP client used by the BrowserOS apply backend."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)

_SNAPSHOT_LINE_RE = re.compile(r'^\[(?P<id>\d+)\]\s+(?P<type>\w+)\s+"(?P<text>.*)"$')


class BrowserOSError(RuntimeError):
    """Raised when BrowserOS MCP returns an error."""


@dataclass(frozen=True)
class SnapshotElement:
    """One interactive element parsed from BrowserOS snapshot text output."""

    element_id: int
    element_type: str
    text: str
    raw_line: str


class BrowserOSClient:
    """Thin JSON-RPC client for BrowserOS MCP on localhost."""

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:9200/mcp",
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            }
        )
        self._request_id = 0
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the MCP session and store any returned session id.

        Returns:
            None.
        """
        if self._initialized:
            return
        response = self._post(
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {"listChanged": True}, "sampling": {}},
                "clientInfo": {"name": "postulator", "version": "1.0"},
            },
        )
        session_id = response.headers.get("Mcp-Session-Id")
        if session_id:
            self.session.headers["Mcp-Session-Id"] = session_id
        self._initialized = True
        logger.info("%s BrowserOS MCP initialized", LogTag.OK)

    def browseros_info(self) -> dict[str, Any]:
        """Fetch BrowserOS server metadata.

        Returns:
            The tool payload returned by ``browseros_info``.
        """
        return self.call_tool("browseros_info", {})

    def get_active_page(self) -> dict[str, Any]:
        """Return the currently active BrowserOS page payload."""
        return self.call_tool("get_active_page", {})

    def list_pages(self) -> dict[str, Any]:
        """Return the list_pages BrowserOS payload."""
        return self.call_tool("list_pages", {})

    def new_page(
        self,
        url: str = "about:blank",
        *,
        background: bool = True,
        hidden: bool = False,
    ) -> int:
        """Create a visible BrowserOS page.

        Returns:
            The created page id.
        """
        return self._extract_page_id(
            self.call_tool(
                "new_page",
                {"url": url, "background": background, "hidden": hidden},
            )
        )

    def new_hidden_page(self, url: str = "about:blank") -> int:
        """Create a hidden BrowserOS page.

        Returns:
            The created page id.
        """
        return self._extract_page_id(self.call_tool("new_hidden_page", {"url": url}))

    def close_page(self, page_id: int) -> None:
        """Close a BrowserOS page.

        Args:
            page_id: Page identifier to close.

        Returns:
            None.
        """
        self.call_tool("close_page", {"page": page_id})

    def show_page(self, page_id: int) -> None:
        """Bring a BrowserOS page to the foreground.

        Args:
            page_id: Page identifier to reveal.

        Returns:
            None.
        """
        self.call_tool("show_page", {"page": page_id})

    def navigate(self, url: str, page_id: int) -> None:
        """Navigate a page to the provided URL.

        Args:
            url: Destination URL.
            page_id: Page identifier to navigate.

        Returns:
            None.
        """
        self.call_tool("navigate_page", {"url": url, "page": page_id})

    def take_snapshot(self, page_id: int) -> list[SnapshotElement]:
        """Capture and parse the current interactive BrowserOS snapshot.

        Args:
            page_id: Page identifier to inspect.

        Returns:
            Parsed interactive elements extracted from the snapshot text.
        """
        result = self.call_tool("take_snapshot", {"page": page_id})
        text = "\n".join(self._collect_text_chunks(result))
        elements: list[SnapshotElement] = []
        for line in text.splitlines():
            match = _SNAPSHOT_LINE_RE.match(line.strip())
            if not match:
                continue
            elements.append(
                SnapshotElement(
                    element_id=int(match.group("id")),
                    element_type=match.group("type"),
                    text=match.group("text"),
                    raw_line=line,
                )
            )
        return elements

    def search_dom(self, page_id: int, selector: str) -> list[int]:
        """Search the DOM for elements matching a CSS selector.

        Args:
            page_id: Page identifier to search.
            selector: CSS selector.

        Returns:
            List of matching element ids.
        """
        result = self.call_tool("search_dom", {"page": page_id, "selector": selector})
        # Extract element IDs from the result
        ids = []
        if isinstance(result, list):
            ids = [int(i) for i in result if str(i).isdigit()]
        elif isinstance(result, dict):
            val = result.get("elements") or result.get("ids") or []
            if isinstance(val, list):
                ids = [int(i) for i in val if str(i).isdigit()]
        return ids

    def click(self, page_id: int, element_id: int) -> None:
        """Click an element identified from a BrowserOS snapshot.

        Args:
            page_id: Page identifier containing the element.
            element_id: BrowserOS element id to click.

        Returns:
            None.
        """
        self.call_tool("click", {"page": page_id, "element": element_id})

    def fill(self, page_id: int, element_id: int, value: str) -> None:
        """Fill a text-like element with a value.

        Args:
            page_id: Page identifier containing the element.
            element_id: BrowserOS element id to fill.
            value: Text value to write.

        Returns:
            None.
        """
        self.call_tool("fill", {"page": page_id, "element": element_id, "text": value})

    def clear(self, page_id: int, element_id: int) -> None:
        """Clear a text-like element."""
        self.call_tool("clear", {"page": page_id, "element": element_id})

    def select_option(self, page_id: int, element_id: int, value: str) -> None:
        """Select an option in a native select element.

        Args:
            page_id: Page identifier containing the element.
            element_id: BrowserOS element id to update.
            value: Option value or label to select.

        Returns:
            None.
        """
        self.call_tool(
            "select_option",
            {"page": page_id, "element": element_id, "value": value},
        )

    def press_key(self, page_id: int, key: str) -> None:
        """Press a key on the page."""
        self.call_tool("press_key", {"page": page_id, "key": key})

    def upload_file(self, page_id: int, element_id: int, file_path: Path) -> None:
        """Upload a local file into a file input element.

        Args:
            page_id: Page identifier containing the element.
            element_id: BrowserOS element id to target.
            file_path: Local file path to upload.

        Returns:
            None.
        """
        self.call_tool(
            "upload_file",
            {"page": page_id, "element": element_id, "filePath": str(file_path)},
        )

    def save_screenshot(self, page_id: int, file_path: Path) -> None:
        """Save a BrowserOS screenshot to disk.

        Args:
            page_id: Page identifier to capture.
            file_path: Destination file path.

        Returns:
            None.
        """
        self.call_tool(
            "save_screenshot",
            {"page": page_id, "path": str(file_path)},
        )

    def evaluate_script(self, page_id: int, expression: str) -> Any:
        """Evaluate raw JavaScript on a BrowserOS page.

        Args:
            page_id: Page identifier to evaluate against.
            expression: JavaScript expression to execute.

        Returns:
            The raw tool result payload.
        """
        return self.call_tool(
            "evaluate_script",
            {"page": page_id, "expression": expression},
        )

    def evaluate_script_react(self, page_id: int, selector: str, value: str) -> Any:
        """Update an input value through the DOM setter and dispatch input.

        Args:
            page_id: Page identifier to evaluate against.
            selector: CSS selector for the target element.
            value: Value to inject.

        Returns:
            The raw tool result payload.
        """
        safe_selector = json.dumps(selector)
        safe_value = json.dumps(value)
        script = (
            f"const el = document.querySelector({safe_selector});"
            "if (!el) { throw new Error('Element not found'); }"
            "const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
            f"setter.call(el, {safe_value});"
            "el.dispatchEvent(new Event('input', { bubbles: true }));"
        )
        return self.evaluate_script(page_id, script)

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a BrowserOS MCP tool after ensuring initialization.

        Args:
            name: Tool name to invoke.
            arguments: JSON-serializable tool arguments.

        Returns:
            The ``result`` object from the MCP response.
        """
        self.initialize()
        response = self._post(
            method="tools/call",
            params={"name": name, "arguments": arguments},
        )
        payload = response.json()
        if payload.get("error"):
            raise BrowserOSError(
                payload["error"].get("message", f"BrowserOS tool failed: {name}")
            )
        return payload.get("result", {})

    def _post(self, *, method: str, params: dict[str, Any]) -> requests.Response:
        self._request_id += 1
        response = self.session.post(
            self.base_url,
            json={
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": self._request_id,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response

    def _extract_page_id(self, result: dict[str, Any]) -> int:
        page_id = self._find_key(result, "pageId")
        if page_id is None:
            page_id = self._find_key(result, "page")
        if page_id is None:
            raise BrowserOSError("BrowserOS response did not include a page id")
        return int(page_id)

    def _find_key(self, value: Any, key: str) -> Any:
        if isinstance(value, dict):
            if key in value:
                return value[key]
            for child in value.values():
                found = self._find_key(child, key)
                if found is not None:
                    return found
            return None
        if isinstance(value, list):
            for item in value:
                found = self._find_key(item, key)
                if found is not None:
                    return found
        return None

    def _collect_text_chunks(self, value: Any) -> list[str]:
        chunks: list[str] = []
        if isinstance(value, str):
            chunks.append(value)
        elif isinstance(value, dict):
            text_value = value.get("text")
            if isinstance(text_value, str):
                chunks.append(text_value)
            for child_key, child in value.items():
                if child_key == "text":
                    continue
                chunks.extend(self._collect_text_chunks(child))
        elif isinstance(value, list):
            for item in value:
                chunks.extend(self._collect_text_chunks(item))
        return chunks
