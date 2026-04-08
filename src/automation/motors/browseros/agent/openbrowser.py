"""OpenBrowser Level 2 Agent Integration.

Wraps the OpenBrowser API behind a local service interface.
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from pydantic import BaseModel

from src.automation.ariadne.contracts import ReplayPath

logger = logging.getLogger(__name__)


class OpenBrowserAgentResult(BaseModel):
    """Playbook data returned by OpenBrowser agent."""

    status: str
    playbook: ReplayPath | None = None
    error: str | None = None


class OpenBrowserClient:
    """Client for invoking the OpenBrowser agent API."""

    def __init__(self, base_url: str = "http://127.0.0.1:9200") -> None:
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

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
