"""BrowserOS Level 2 agent integration.

This module captures BrowserOS `/chat` SSE traces for Level 2 agent sessions.
It does not attempt to behave like a deterministic replay motor.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests
from pydantic import BaseModel, Field

from src.automation.motors.browseros.runtime import (
    resolve_browseros_runtime,
    ensure_browseros_running,
)
from .models import BrowserOSLevel2StreamEvent, BrowserOSLevel2Trace
from .normalizer import BrowserOSLevel2TraceNormalizer
from .promoter import BrowserOSLevel2Promoter
from src.automation.motors.browseros.promotion_pipeline import (
    BrowserOSCandidateGrouper,
    BrowserOSPathValidator,
)

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class OpenBrowserAgentResult(BaseModel):
    """Compatibility wrapper for older Level 2 callers."""

    status: str
    playbook: Any | None = None
    error: str | None = None
    conversation_id: str | None = None
    recording_path: str | None = None
    trace: dict[str, Any] | None = None
    candidates: list[dict[str, Any]] = Field(default_factory=list)


class OpenBrowserConversationResult(BaseModel):
    """Outcome of a Level 2 BrowserOS `/chat` session."""

    status: str
    conversation_id: str
    final_text: str | None = None
    finish_reason: str | None = None
    trace: BrowserOSLevel2Trace
    recording_path: str | None = None
    error: str | None = None


class OpenBrowserClient:
    """Client for BrowserOS Level 2 `/chat` sessions."""

    def __init__(
        self,
        base_url: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.runtime = resolve_browseros_runtime(preferred_base_url=base_url)
        self.base_url = self.runtime.base_http_url
        self.session = session or requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.normalizer = BrowserOSLevel2TraceNormalizer()
        self.grouper = BrowserOSCandidateGrouper()
        self.validator = BrowserOSPathValidator()
        self.promoter = BrowserOSLevel2Promoter()

    def communicate(
        self,
        prompt: str,
        *,
        source: str = "browseros",
        provider: str = "browseros",
        model: str = "browseros-auto",
        mode: str = "agent",
        recording_path: Path | None = None,
        browser_context: dict[str, Any] | None = None,
        user_system_prompt: str | None = None,
        user_working_dir: str | None = None,
        timeout_seconds: float = 180.0,
    ) -> OpenBrowserConversationResult:
        """Run a Level 2 BrowserOS `/chat` session and capture its raw trace."""
        ensure_browseros_running(self.runtime)

        conversation_id = str(uuid4())
        started_at = _utc_now()
        trace = BrowserOSLevel2Trace(
            conversation_id=conversation_id,
            source=source,
            goal=prompt,
            provider=provider,
            model=model,
            mode=mode,
            started_at=started_at,
        )
        payload = {
            "conversationId": conversation_id,
            "message": prompt,
            "provider": provider,
            "model": model,
            "mode": mode,
        }
        if browser_context is not None:
            payload["browserContext"] = browser_context
        if user_system_prompt is not None:
            payload["userSystemPrompt"] = user_system_prompt
        if user_working_dir is not None:
            payload["userWorkingDir"] = user_working_dir

        text_chunks: list[str] = []
        stream_errors: list[str] = []
        try:
            with self.session.post(
                f"{self.base_url}/chat",
                json=payload,
                stream=True,
                timeout=timeout_seconds,
            ) as response:
                if response.status_code == 429:
                    return self._finalize_result(
                        trace=trace,
                        status="rate_limited",
                        recording_path=recording_path,
                        error="BrowserOS /chat rate limited the request.",
                    )
                response.raise_for_status()
                for raw_line in response.iter_lines(decode_unicode=True):
                    event = self._parse_sse_line(raw_line, conversation_id)
                    if event is None:
                        continue
                    trace.stream_events.append(event)
                    if event.event_type == "text-delta":
                        delta = event.payload.get("delta")
                        if isinstance(delta, str):
                            text_chunks.append(delta)
                    if event.event_type == "tool-output-available":
                        output = event.payload.get("output")
                        if isinstance(output, dict) and output.get("isError") is True:
                            stream_errors.append(
                                self._extract_tool_error(output)
                                or "BrowserOS tool output reported an error."
                            )
                    if event.event_type == "finish":
                        finish_reason = event.payload.get("finishReason")
                        trace.finish_reason = (
                            str(finish_reason) if finish_reason is not None else None
                        )
            trace.final_text = "".join(text_chunks) or None
            status = "success"
            error = None
            if stream_errors:
                status = "failed"
                error = "; ".join(stream_errors)
            return self._finalize_result(
                trace=trace,
                status=status,
                recording_path=recording_path,
                error=error,
            )
        except requests.HTTPError as exc:
            logger.error("BrowserOS /chat HTTP error: %s", exc)
            return self._finalize_result(
                trace=trace,
                status="failed",
                recording_path=recording_path,
                error=str(exc),
            )
        except requests.RequestException as exc:
            logger.error("BrowserOS /chat request failed: %s", exc)
            return self._finalize_result(
                trace=trace,
                status="failed",
                recording_path=recording_path,
                error=str(exc),
            )

    def run_agent(
        self,
        portal: str,
        url: str,
        context: dict[str, Any],
    ) -> OpenBrowserAgentResult:
        """Compatibility path for older callers.

        This captures a Level 2 trace but does not yet promote it into a replay path.
        """
        goal = self._build_goal(portal=portal, url=url, context=context)
        result = self.communicate(
            goal,
            source=portal,
            browser_context={"entry_url": url, "context": context},
        )
        candidates = self.normalizer.normalize_shared(result.trace)
        grouped_candidates = self.grouper.group(candidates)
        assessment = self.validator.assess(grouped_candidates)
        playbook = None
        if assessment.outcome == "promotable":
            playbook = self.promoter.promote(
                portal=portal, candidates=grouped_candidates
            )
        status = result.status
        error = result.error
        if result.status == "success" and playbook is None:
            status = "capture_only"
            error = (
                error
                or "; ".join(assessment.reasons)
                or "Level 2 trace captured but could not be promoted into a replay path."
            )
        return OpenBrowserAgentResult(
            status=status,
            playbook=playbook,
            error=error,
            conversation_id=result.conversation_id,
            recording_path=result.recording_path,
            trace=result.trace.model_dump(mode="json"),
            candidates=[
                candidate.model_dump(mode="json") for candidate in grouped_candidates
            ],
        )

    def _finalize_result(
        self,
        *,
        trace: BrowserOSLevel2Trace,
        status: str,
        recording_path: Path | None,
        error: str | None = None,
    ) -> OpenBrowserConversationResult:
        trace.ended_at = _utc_now()
        final_path = None
        if recording_path is not None:
            recording_path.parent.mkdir(parents=True, exist_ok=True)
            recording_path.write_text(trace.model_dump_json(indent=2), encoding="utf-8")
            final_path = str(recording_path)
        return OpenBrowserConversationResult(
            status=status,
            conversation_id=trace.conversation_id,
            final_text=trace.final_text,
            finish_reason=trace.finish_reason,
            trace=trace,
            recording_path=final_path,
            error=error,
        )

    def _parse_sse_line(
        self,
        raw_line: str | bytes,
        conversation_id: str,
    ) -> BrowserOSLevel2StreamEvent | None:
        if not raw_line:
            return None
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
        if not line.startswith("data: "):
            return None
        payload_text = line[6:]
        if payload_text == "[DONE]":
            return None
        payload = json.loads(payload_text)
        event_type = str(payload.get("type", "unknown"))
        return BrowserOSLevel2StreamEvent(
            timestamp=_utc_now(),
            conversation_id=conversation_id,
            event_type=event_type,
            payload=payload,
        )

    def _extract_tool_error(self, output: dict[str, Any]) -> str | None:
        content = output.get("content")
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                text = item.get("text")
                if isinstance(text, str) and text:
                    parts.append(text)
            if parts:
                return " ".join(parts)
        return None

    def _build_goal(self, *, portal: str, url: str, context: dict[str, Any]) -> str:
        summary = {
            "portal": portal,
            "url": url,
            "context_keys": sorted(context.keys()),
        }
        return (
            "Start from the provided application URL and explore the flow. "
            "Capture enough information to later normalize the interaction into a reusable application path. "
            f"Session summary: {json.dumps(summary, sort_keys=True)}"
        )
