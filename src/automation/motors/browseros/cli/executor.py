"""Executor for BrowserOS-backed apply flows using Ariadne Semantic Maps."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.automation.ariadne.models import (
    AriadneAction,
    AriadneIntent,
    AriadneObserve,
    AriadnePath,
    AriadneTarget,
)
from src.automation.motors.browseros.cli.client import BrowserOSClient, SnapshotElement
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)

_PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z0-9_.-]+)\s*}}")


class BrowserOSObserveError(RuntimeError):
    """Raised when a step does not match the live page state."""


@dataclass
class BrowserOSExecutionResult:
    """Outcome summary returned after replaying an Ariadne path."""

    status: str
    fields_filled: list[str]
    confirmation_text: str | None = None


class BrowserOSPlaybookExecutor:
    """Execute an Ariadne Path against a live BrowserOS page."""

    def __init__(self, client: BrowserOSClient, *, input_func=input) -> None:
        self.client = client
        self.input_func = input_func

    def run(
        self,
        *,
        page_id: int,
        path: AriadnePath,
        context: dict[str, Any],
        cv_path: Path,
        dry_run: bool,
    ) -> BrowserOSExecutionResult:
        """Execute an Ariadne path against an already-open page.

        Args:
            page_id: BrowserOS page identifier to operate on.
            path: AriadnePath definition to replay.
            context: Template context for interpolation.
            cv_path: Local CV path used by upload actions.
            dry_run: Whether execution should stop at a dry-run guard.

        Returns:
            A summary of execution status and touched fields.
        """
        fields_filled: list[str] = []

        for step in path.steps:
            logger.info("%s Executing Step %s: %s", LogTag.FAST, step.step_index, step.name)
            
            # 1. Observation Guards
            snapshot = self.client.take_snapshot(page_id)
            self._assert_observation(snapshot, step.observe, step.name)

            if dry_run and step.dry_run_stop:
                logger.info("%s Dry-run stop at step '%s'", LogTag.OK, step.name)
                return BrowserOSExecutionResult(
                    status="dry_run", fields_filled=fields_filled
                )

            if step.human_required:
                self._request_human_confirmation(step.description)

            # 2. Actions
            for action in step.actions:
                self._execute_action(
                    page_id=page_id,
                    action=action,
                    context=context,
                    cv_path=cv_path,
                    fields_filled=fields_filled,
                )

        return BrowserOSExecutionResult(
            status="submitted",
            fields_filled=fields_filled,
            confirmation_text=f"Ariadne Path {path.id} completed",
        )

    def render_template(self, template: str, context: dict[str, Any]) -> str:
        """Render {{key}} placeholders from a nested context mapping."""

        def _replace(match: re.Match[str]) -> str:
            key = match.group(1)
            value = self._lookup_context_value(context, key)
            return match.group(0) if value is None else str(value)

        return _PLACEHOLDER_RE.sub(_replace, template)

    def _lookup_context_value(self, context: dict[str, Any], key: str) -> Any:
        current: Any = context
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    def _assert_observation(
        self,
        snapshot: list[SnapshotElement],
        observe: AriadneObserve,
        step_name: str,
    ) -> None:
        """Verify that required elements are present in the snapshot."""
        for target in observe.required_elements:
            self._resolve_element_id(snapshot, target)
        logger.info("%s Step '%s' matched expected snapshot", LogTag.OK, step_name)

    def _resolve_element_id(
        self,
        snapshot: list[SnapshotElement],
        target: AriadneTarget,
    ) -> int:
        """Resolve an AriadneTarget to a BrowserOS element ID using text or CSS."""
        if target.text:
            normalized_target = self._normalize_text(target.text)
            matches = [
                e for e in snapshot 
                if normalized_target in self._normalize_text(e.text)
            ]
            if matches:
                return matches[0].element_id
                
        if target.css:
            # BrowserOS client doesn't support CSS directly via MCP yet? 
            # (In this codebase it seems to only support text matching in the client's current stub)
            # We fallback to text if possible.
            pass

        raise BrowserOSObserveError(
            f"Target '{target}' not found in BrowserOS snapshot"
        )

    def _normalize_text(self, value: str) -> str:
        return " ".join(value.lower().split())

    def _execute_action(
        self,
        *,
        page_id: int,
        action: AriadneAction,
        context: dict[str, Any],
        cv_path: Path,
        fields_filled: list[str],
    ) -> None:
        """Execute a single AriadneAction."""
        if action.intent == AriadneIntent.NAVIGATE:
            url = self.render_template(action.value or "", context)
            self.client.navigate(page_id, url)
            return

        if not action.target:
            logger.warning("%s Action '%s' has no target; skipping.", LogTag.WARN, action.intent)
            return

        # Resolve Target ID
        try:
            target_id = self._resolve_element_id(self.client.take_snapshot(page_id), action.target)
        except BrowserOSObserveError:
            if action.fallback:
                logger.warning("%s Falling back for intent %s", LogTag.WARN, action.intent)
                return self._execute_action(
                    page_id=page_id, action=action.fallback, context=context, 
                    cv_path=cv_path, fields_filled=fields_filled
                )
            if action.optional:
                return
            raise

        # Map Intents to Tools
        rendered_value = self.render_template(action.value or "", context) if action.value else None
        
        if action.intent == AriadneIntent.CLICK:
            self.client.click(page_id, target_id)
        elif action.intent == AriadneIntent.FILL:
            self.client.fill(page_id, target_id, rendered_value or "")
        elif action.intent == AriadneIntent.FILL_REACT:
            # We need a text selector for evaluate_script_react in current stub
            selector = action.target.text or action.target.css or ""
            self.client.evaluate_script_react(page_id, selector, rendered_value or "")
        elif action.intent == AriadneIntent.SELECT:
            self.client.select_option(page_id, target_id, rendered_value or "")
        elif action.intent == AriadneIntent.UPLOAD:
            # Use value as path if provided, else use cv_path
            upload_path = Path(rendered_value) if rendered_value else cv_path
            self.client.upload_file(page_id, target_id, upload_path)
        
        if action.target.text:
            fields_filled.append(action.target.text)

    def _request_human_confirmation(self, message: str) -> None:
        answer = self.input_func(f"[apply/browseros] {message} [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            raise RuntimeError("Application aborted by operator")
