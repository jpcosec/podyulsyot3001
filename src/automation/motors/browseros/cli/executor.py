"""Playbook executor for BrowserOS-backed apply flows."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.automation.motors.browseros.cli.client import BrowserOSClient, SnapshotElement
from src.automation.motors.browseros.cli.models import (
    BrowserOSPlaybook,
    ExpectedElement,
    PlaybookAction,
)
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)

_PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z0-9_.-]+)\s*}}")


class BrowserOSObserveError(RuntimeError):
    """Raised when a playbook step does not match the live page state."""


@dataclass
class BrowserOSExecutionResult:
    """Outcome summary returned after replaying a BrowserOS playbook."""

    status: str
    fields_filled: list[str]
    confirmation_text: str | None = None


class BrowserOSPlaybookExecutor:
    """Execute a BrowserOS playbook against a live BrowserOS page."""

    def __init__(self, client: BrowserOSClient, *, input_func=input) -> None:
        self.client = client
        self.input_func = input_func

    def run(
        self,
        *,
        page_id: int,
        playbook: BrowserOSPlaybook,
        context: dict[str, Any],
        cv_path: Path,
        dry_run: bool,
    ) -> BrowserOSExecutionResult:
        """Execute a BrowserOS playbook against an already-open page.

        Args:
            page_id: BrowserOS page identifier to operate on.
            playbook: Parsed playbook definition to replay.
            context: Template context for selector and value interpolation.
            cv_path: Local CV path used by upload steps.
            dry_run: Whether execution should stop at a dry-run guard step.

        Returns:
            A summary of execution status and touched fields.
        """
        fields_filled: list[str] = []

        for step in playbook.steps:
            snapshot = self.client.take_snapshot(page_id)
            self._assert_expected_elements(
                snapshot, step.observe.expected_elements, step.name
            )

            if dry_run and step.dry_run_stop:
                logger.info("%s Dry-run stop at step '%s'", LogTag.OK, step.name)
                return BrowserOSExecutionResult(
                    status="dry_run", fields_filled=fields_filled
                )

            if step.human_required:
                self._request_human_confirmation(step.human_message or step.description)

            for action in step.actions:
                self._execute_action(
                    page_id=page_id,
                    action=action,
                    context=context,
                    cv_path=cv_path,
                    fields_filled=fields_filled,
                )

            if step.next_button_text:
                button_id = self._resolve_element_id(
                    self.client.take_snapshot(page_id),
                    self.render_template(step.next_button_text, context),
                )
                self.client.click(page_id, button_id)

        return BrowserOSExecutionResult(
            status="submitted",
            fields_filled=fields_filled,
            confirmation_text=f"Playbook {playbook.path} completed",
        )

    def render_template(self, template: str, context: dict[str, Any]) -> str:
        """Render ``{{key}}`` placeholders from a nested context mapping.

        Args:
            template: Template string containing zero or more placeholders.
            context: Nested dictionary used for placeholder resolution.

        Returns:
            The rendered string. Unresolved placeholders are left unchanged.
        """

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

    def _assert_expected_elements(
        self,
        snapshot: list[SnapshotElement],
        expected: list[ExpectedElement],
        step_name: str,
    ) -> None:
        for expected_element in expected:
            self._resolve_element_id(
                snapshot, expected_element.text, required_type=expected_element.type
            )
        logger.info("%s Step '%s' matched expected snapshot", LogTag.OK, step_name)

    def _resolve_element_id(
        self,
        snapshot: list[SnapshotElement],
        selector_text: str,
        *,
        required_type: str | None = None,
    ) -> int:
        normalized_target = self._normalize_text(selector_text)
        exact_matches = [
            element
            for element in snapshot
            if self._matches_type(element, required_type)
            and self._normalize_text(element.text) == normalized_target
        ]
        if exact_matches:
            return exact_matches[0].element_id

        partial_matches = [
            element
            for element in snapshot
            if self._matches_type(element, required_type)
            and normalized_target in self._normalize_text(element.text)
        ]
        if partial_matches:
            return partial_matches[0].element_id

        raise BrowserOSObserveError(
            f"Element '{selector_text}' not found in BrowserOS snapshot"
        )

    def _matches_type(
        self, element: SnapshotElement, required_type: str | None
    ) -> bool:
        return required_type is None or element.element_type == required_type

    def _normalize_text(self, value: str) -> str:
        return " ".join(value.lower().split())

    def _execute_action(
        self,
        *,
        page_id: int,
        action: PlaybookAction,
        context: dict[str, Any],
        cv_path: Path,
        fields_filled: list[str],
    ) -> None:
        selector_text = self.render_template(action.selector_text, context)
        if "{{" in selector_text:
            raise BrowserOSObserveError(
                f"Unresolved selector template for action '{action.tool}': {action.selector_text}"
            )

        if action.tool == "upload_file":
            target_id = self._resolve_element_id(
                self.client.take_snapshot(page_id), selector_text
            )
            self.client.upload_file(page_id, target_id, cv_path)
            fields_filled.append(selector_text)
            return

        rendered_value = (
            self.render_template(action.value, context) if action.value else None
        )
        if rendered_value and "{{" in rendered_value:
            logger.warning(
                "%s Skipping '%s' because value is unresolved: %s",
                LogTag.WARN,
                action.tool,
                action.value,
            )
            return

        try:
            target_id = self._resolve_element_id(
                self.client.take_snapshot(page_id), selector_text
            )
        except BrowserOSObserveError:
            if action.fallback is None:
                raise
            logger.warning(
                "%s Falling back from '%s' to '%s' for selector '%s'",
                LogTag.WARN,
                action.tool,
                action.fallback.tool,
                action.selector_text,
            )
            fallback_action = PlaybookAction(
                tool=action.fallback.tool,
                selector_text=action.fallback.selector_text,
                value=action.fallback.value,
            )
            self._execute_action(
                page_id=page_id,
                action=fallback_action,
                context=context,
                cv_path=cv_path,
                fields_filled=fields_filled,
            )
            return
        if action.tool == "click":
            self.client.click(page_id, target_id)
            fields_filled.append(selector_text)
            return
        if action.tool == "fill":
            if rendered_value is None:
                return
            self.client.fill(page_id, target_id, rendered_value)
            fields_filled.append(selector_text)
            return
        if action.tool == "select_option":
            if rendered_value is None:
                return
            self.client.select_option(page_id, target_id, rendered_value)
            fields_filled.append(selector_text)
            return
        if action.tool == "evaluate_script_react":
            if rendered_value is None:
                return
            self.client.evaluate_script_react(page_id, selector_text, rendered_value)
            fields_filled.append(selector_text)
            return

        raise BrowserOSObserveError(f"Unsupported BrowserOS action: {action.tool}")

    def _request_human_confirmation(self, message: str) -> None:
        answer = self.input_func(f"[apply/browseros] {message} [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            raise RuntimeError("Application aborted by operator")
