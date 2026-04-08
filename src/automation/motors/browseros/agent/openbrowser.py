"""OpenBrowser Level 2 Agent Integration.

Wraps the OpenBrowser API behind a local service interface.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel

from src.automation.ariadne.contracts import ReplayPath
from src.automation.motors.browseros.cli.client import BrowserOSClient, SnapshotElement

logger = logging.getLogger(__name__)


_AGENT_LAUNCHER_TEXT = "Ask BrowserOS or search Google"
_AGENT_COMPOSER_TEXT = "What should I do?"
_SEND_BUTTON_TEXT = "Send"


class OpenBrowserAgentResult(BaseModel):
    """Playbook data returned by OpenBrowser agent."""

    status: str
    playbook: ReplayPath | None = None
    error: str | None = None


class OpenBrowserConversationResult(BaseModel):
    """Outcome of a natural-language BrowserOS agent interaction."""

    status: str
    page_id: int | None = None
    page_url: str | None = None
    page_title: str | None = None
    screenshot_path: str | None = None
    snapshot_excerpt: str | None = None
    error: str | None = None


class OpenBrowserClient:
    """Client for invoking the OpenBrowser agent API."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:9200",
        browser_client: BrowserOSClient | None = None,
    ) -> None:
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.browser_client = browser_client or BrowserOSClient(
            base_url=f"{base_url}/mcp"
        )

    def communicate(
        self,
        prompt: str,
        *,
        screenshot_path: Path | None = None,
        timeout_seconds: float = 90.0,
        poll_interval: float = 2.0,
    ) -> OpenBrowserConversationResult:
        """Send a natural-language prompt to the BrowserOS UI agent.

        This uses BrowserOS's own new-tab agent surface via MCP tool calls rather
        than the undocumented `/chat` endpoint.
        """
        created_page_id = self.browser_client.new_page(
            "chrome://newtab/", background=False
        )
        page_id = self._wait_for_agent_surface(
            created_page_id,
            timeout_seconds=timeout_seconds,
        )
        self._submit_prompt(page_id, prompt)
        final_page = self._wait_for_agent_progress(
            page_id,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
        )
        shot = str(screenshot_path) if screenshot_path else None
        if screenshot_path is not None:
            self.browser_client.save_screenshot(final_page["pageId"], screenshot_path)
        snapshot = self.browser_client.take_snapshot(final_page["pageId"])
        excerpt = "\n".join(element.raw_line for element in snapshot[:12])
        return OpenBrowserConversationResult(
            status="success",
            page_id=final_page["pageId"],
            page_url=final_page.get("url"),
            page_title=final_page.get("title"),
            screenshot_path=shot,
            snapshot_excerpt=excerpt,
        )

    def run_agent(
        self,
        portal: str,
        url: str,
        context: dict[str, Any],
    ) -> OpenBrowserAgentResult:
        """Invoke OpenBrowser, pass context, and validate returned playbook.

        Args:
            portal: Portal name for context.
            url: Starting application URL.
            context: Job/profile/document context.

        Returns:
            Validated playbook result.
        """
        payload = {"portal": portal, "url": url, "context": context}
        try:
            resp = self.session.post(f"{self.base_url}/chat", json=payload, timeout=300)
            resp.raise_for_status()
            data = resp.json()
            return OpenBrowserAgentResult.model_validate(data)
        except Exception as exc:
            logger.error("OpenBrowser agent invocation failed: %s", exc)
            return OpenBrowserAgentResult(status="error", error=str(exc))

    def _wait_for_agent_surface(
        self,
        page_id: int,
        *,
        timeout_seconds: float,
    ) -> int:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            active = (
                self.browser_client.get_active_page()
                .get("structuredContent", {})
                .get("page", {})
            )
            active_page_id = active.get("pageId") or page_id
            snapshot = self.browser_client.take_snapshot(active_page_id)
            if self._find_element(snapshot, _AGENT_LAUNCHER_TEXT) or self._find_element(
                snapshot, _AGENT_COMPOSER_TEXT
            ):
                return active_page_id
            time.sleep(1.0)
        raise RuntimeError("BrowserOS agent surface did not become ready")

    def _submit_prompt(self, page_id: int, prompt: str) -> None:
        snapshot = self.browser_client.take_snapshot(page_id)
        composer = self._find_element(snapshot, _AGENT_COMPOSER_TEXT)
        if composer is not None:
            self._send_from_composer(page_id, composer.element_id, prompt)
            return

        launcher = self._find_element(snapshot, _AGENT_LAUNCHER_TEXT)
        if launcher is None:
            raise RuntimeError("Could not find BrowserOS agent prompt input")
        self.browser_client.click(page_id, launcher.element_id)
        self.browser_client.fill(page_id, launcher.element_id, prompt)

        launcher_snapshot = self.browser_client.take_snapshot(page_id)
        ask_option = self._find_element(launcher_snapshot, f"Ask BrowserOS: {prompt}")
        if ask_option is not None:
            self.browser_client.click(page_id, ask_option.element_id)
        else:
            self.browser_client.press_key(page_id, "Enter")

        time.sleep(1.0)
        composer_snapshot = self.browser_client.take_snapshot(page_id)
        composer = self._find_element(composer_snapshot, _AGENT_COMPOSER_TEXT)
        send_button = self._find_element(composer_snapshot, _SEND_BUTTON_TEXT)
        if composer is not None and send_button is not None:
            self._send_from_composer(page_id, composer.element_id, prompt)

    def _send_from_composer(self, page_id: int, composer_id: int, prompt: str) -> None:
        self.browser_client.click(page_id, composer_id)
        self.browser_client.fill(page_id, composer_id, prompt)
        snapshot = self.browser_client.take_snapshot(page_id)
        send_button = self._find_element(snapshot, _SEND_BUTTON_TEXT)
        if send_button is None:
            raise RuntimeError("Could not find BrowserOS agent send button")
        self.browser_client.click(page_id, send_button.element_id)

    def _wait_for_agent_progress(
        self,
        page_id: int,
        *,
        timeout_seconds: float,
        poll_interval: float,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            active = (
                self.browser_client.get_active_page()
                .get("structuredContent", {})
                .get("page", {})
            )
            active_id = active.get("pageId")
            if (
                active_id
                and active.get("url")
                and active.get("url") != "chrome://newtab/"
            ):
                return active

            snapshot = self.browser_client.take_snapshot(active_id or page_id)
            stop_button = self._find_element(snapshot, "Stop")
            send_button = self._find_element(snapshot, _SEND_BUTTON_TEXT)
            if stop_button is None and send_button is not None:
                return active or {"pageId": page_id}
            time.sleep(poll_interval)
        raise RuntimeError("BrowserOS agent did not complete within timeout")

    def _find_element(
        self,
        snapshot: list[SnapshotElement],
        text: str,
    ) -> SnapshotElement | None:
        normalized = self._normalize(text)
        for element in snapshot:
            if normalized in self._normalize(element.text):
                return element
        return None

    def _normalize(self, value: str) -> str:
        return " ".join(value.lower().split())
