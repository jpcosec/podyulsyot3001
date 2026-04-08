"""Executor for BrowserOS-backed apply flows using Ariadne Semantic Maps."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.automation.ariadne.contracts import (
    ReplayAction,
    ReplayObserve,
    ReplayPath,
    ReplayStep,
    ReplayTarget,
)
from src.automation.ariadne.exceptions import FormReviewRequired
from src.automation.ariadne.form_analyzer import (
    AriadneFormAnalyzer,
    BrowserOSFieldElement,
)
from src.automation.ariadne.danger_contracts import (
    ApplyDangerReport,
    ApplyDangerSignals,
)
from src.automation.ariadne.danger_detection import ApplyDangerDetector
from src.automation.ariadne.exceptions import HumanInterventionRequired
from src.automation.motors.browseros.cli.client import BrowserOSClient, SnapshotElement
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)

_PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z0-9_.-]+)\s*}}")


class BrowserOSObserveError(RuntimeError):
    """Raised when a step does not match the live page state."""


@dataclass
class BrowserOSExecutionResult:
    """Outcome summary returned after replaying a BrowserOS-compatible path."""

    status: str
    fields_filled: list[str]
    confirmation_text: str | None = None


class BrowserOSReplayer:
    """Execute replay-contract steps against a live BrowserOS page."""

    def __init__(self, client: BrowserOSClient, *, input_func=input) -> None:
        self.client = client
        self.input_func = input_func
        self._danger_detector = ApplyDangerDetector()
        self._form_analyzer = AriadneFormAnalyzer()

    def run(
        self,
        *,
        page_id: int,
        path: ReplayPath,
        context: dict[str, Any],
        cv_path: Path,
        letter_path: Path | None = None,
        dry_run: bool,
    ) -> BrowserOSExecutionResult:
        """Execute a replay path against an already-open page.

        .. deprecated::
            Production code now calls execute_single_step() step-by-step via
            BrowserOSMotorSession. This method is retained for existing tests only.

        Args:
            page_id: BrowserOS page identifier to operate on.
            path: ReplayPath definition to replay.
            context: Template context for interpolation.
            cv_path: Local CV path used by upload actions.
            letter_path: Optional cover letter path used by letter upload actions.
            dry_run: Whether execution should stop at a dry-run guard.

        Returns:
            A summary of execution status and touched fields.
        """
        fields_filled: list[str] = []

        for step in path.steps:
            logger.info(
                "%s Executing Step %s: %s", LogTag.FAST, step.step_index, step.name
            )

            # 1. Observation Guards
            snapshot = self.client.take_snapshot(page_id)
            try:
                self._assert_observation(snapshot, step.observe, step.name, page_id)
            except BrowserOSObserveError as exc:
                raise self._build_hitl_request(
                    step,
                    reason="observation_failed",
                    message=str(exc),
                ) from exc

            if dry_run and step.dry_run_stop:
                logger.info("%s Dry-run stop at step '%s'", LogTag.OK, step.name)
                return BrowserOSExecutionResult(
                    status="dry_run", fields_filled=fields_filled
                )

            if step.human_required:
                raise self._build_hitl_request(
                    step,
                    reason="human_required",
                    message=step.description,
                )

            # 2. Actions
            for action in step.actions:
                try:
                    self._execute_action(
                        page_id=page_id,
                        action=action,
                        context=context,
                        cv_path=cv_path,
                        letter_path=letter_path,
                        fields_filled=fields_filled,
                    )
                except BrowserOSObserveError as exc:
                    raise self._build_hitl_request(
                        step,
                        reason="target_not_found",
                        message=str(exc),
                    ) from exc

        return BrowserOSExecutionResult(
            status="submitted",
            fields_filled=fields_filled,
            confirmation_text=f"Replay path {path.id} completed",
        )

    def execute_single_step(
        self,
        *,
        page_id: int,
        step: ReplayStep,
        context: dict[str, Any],
        cv_path: Path,
        letter_path: Path | None = None,
        fields_filled: list[str] | None = None,
    ) -> None:
        """Execute a single replay-contract step on the given page.

        Args:
            page_id: BrowserOS page to operate on.
            step: The motor-facing step contract to execute.
            context: Template context for interpolation.
            cv_path: Local CV path for upload actions.
            letter_path: Optional cover letter path for upload actions.
            fields_filled: Optional accumulator list for tracking touched fields.

        Returns:
            None. The method performs in-place browser actions and may append to
            `fields_filled` as a side effect.
        """
        if fields_filled is None:
            fields_filled = []
        logger.info("%s Executing Step %s: %s", LogTag.FAST, step.step_index, step.name)
        snapshot = self.client.take_snapshot(page_id)
        try:
            self._assert_observation(snapshot, step.observe, step.name, page_id)
        except BrowserOSObserveError as exc:
            raise self._build_hitl_request(
                step,
                reason="observation_failed",
                message=str(exc),
            ) from exc
        if step.human_required:
            raise self._build_hitl_request(
                step,
                reason="human_required",
                message=step.description,
            )
        for action in step.actions:
            try:
                self._execute_action(
                    page_id=page_id,
                    action=action,
                    context=context,
                    cv_path=cv_path,
                    letter_path=letter_path,
                    fields_filled=fields_filled,
                )
            except BrowserOSObserveError as exc:
                raise self._build_hitl_request(
                    step,
                    reason="target_not_found",
                    message=str(exc),
                ) from exc

    def render_template(self, template: str, context: dict[str, Any]) -> str:
        """Render {{key}} placeholders from a nested context mapping."""

        def _replace(match: re.Match[str]) -> str:
            key = match.group(1)
            value = self._lookup_context_value(context, key)
            return match.group(0) if value is None else str(value)

        return _PLACEHOLDER_RE.sub(_replace, template)

    def inspect_page_danger(
        self,
        *,
        page_id: int,
        application_url: str | None,
    ) -> ApplyDangerReport:
        """Inspect the current BrowserOS page for risky apply-flow states."""
        snapshot = self.client.take_snapshot(page_id)
        snapshot_text = "\n".join(
            element.raw_line or element.text for element in snapshot
        )
        return self._danger_detector.detect(
            ApplyDangerSignals(
                dom_text=snapshot_text,
                current_url=self._read_current_url(page_id),
                application_url=application_url,
            )
        )

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
        observe: ReplayObserve,
        step_name: str,
        page_id: int,
    ) -> None:
        """Verify that required elements are present in the snapshot."""
        for target in observe.required_elements:
            self._resolve_element_id(snapshot, target, page_id=page_id)
        logger.info("%s Step '%s' matched expected snapshot", LogTag.OK, step_name)

    def _resolve_element_id(
        self,
        snapshot: list[SnapshotElement],
        target: ReplayTarget,
        *,
        page_id: int | None = None,
    ) -> int:
        """Resolve a replay target to a BrowserOS element ID using text or CSS."""
        # 1. Try Text Matching (Superior fuzzy matching in BrowserOS)
        if target.text:
            normalized_target = self._normalize_text(target.text)
            matches = [
                e for e in snapshot if normalized_target in self._normalize_text(e.text)
            ]
            if matches:
                interactive = [
                    element
                    for element in matches
                    if element.element_type not in {"text", "label"}
                ]
                chosen = interactive[0] if interactive else matches[0]
                return chosen.element_id

        # 2. Try CSS Selection (Requires page_id for live search)
        if target.css and page_id is not None:
            matches = self.client.search_dom(page_id, target.css)
            if matches:
                return matches[0]

        raise BrowserOSObserveError(
            f"Target '{target}' not found in BrowserOS (Text search failed, CSS search failed or skipped)"
        )

    def _normalize_text(self, value: str) -> str:
        return " ".join(value.lower().split())

    def _read_current_url(self, page_id: int) -> str | None:
        result = self.client.evaluate_script(page_id, "window.location.href")
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            for key in ("result", "value", "text"):
                value = result.get(key)
                if isinstance(value, str) and value:
                    return value
        return None

    def _execute_action(
        self,
        *,
        page_id: int,
        action: ReplayAction,
        context: dict[str, Any],
        cv_path: Path,
        letter_path: Path | None,
        fields_filled: list[str],
    ) -> None:
        """Execute a single replay-contract action."""
        if action.intent == "navigate":
            url = self.render_template(action.value or "", context)
            self.client.navigate(url, page_id)
            return

        if action.intent == "analyze_form":
            self._execute_analyze_form(
                page_id=page_id,
                context=context,
                cv_path=cv_path,
                letter_path=letter_path,
                fields_filled=fields_filled,
            )
            return

        if not action.target:
            logger.warning(
                "%s Action '%s' has no target; skipping.", LogTag.WARN, action.intent
            )
            return

        # Resolve Target ID
        try:
            target_id = self._resolve_element_id(
                self.client.take_snapshot(page_id), action.target, page_id=page_id
            )
        except BrowserOSObserveError:
            if action.fallback:
                logger.warning(
                    "%s Falling back for intent %s", LogTag.WARN, action.intent
                )
                return self._execute_action(
                    page_id=page_id,
                    action=action.fallback,
                    context=context,
                    cv_path=cv_path,
                    letter_path=letter_path,
                    fields_filled=fields_filled,
                )
            if action.optional:
                return
            raise

        # Map Intents to Tools
        rendered_value = (
            self.render_template(action.value or "", context) if action.value else None
        )

        if action.intent == "click":
            self.client.click(page_id, target_id)
        elif action.intent == "fill":
            self.client.fill(page_id, target_id, rendered_value or "")
        elif action.intent == "fill_react_controlled":
            # We need a text selector for evaluate_script_react in current stub
            selector = action.target.text or action.target.css or ""
            self.client.evaluate_script_react(page_id, selector, rendered_value or "")
        elif action.intent == "select":
            self.client.select_option(page_id, target_id, rendered_value or "")
        elif action.intent == "upload":
            # Use value as path if provided, else use cv_path
            upload_path = Path(rendered_value) if rendered_value else cv_path
            self.client.upload_file(page_id, target_id, upload_path)
        elif action.intent == "upload_letter":
            upload_path = Path(rendered_value) if rendered_value else letter_path
            if upload_path is None:
                if action.optional:
                    return
                raise ValueError(
                    "upload_letter action requires letter_path or an explicit value"
                )
            self.client.upload_file(page_id, target_id, upload_path)

        if action.target.text:
            fields_filled.append(action.target.text)

    def _execute_analyze_form(
        self,
        *,
        page_id: int,
        context: dict[str, Any],
        cv_path: Path,
        letter_path: Path | None,
        fields_filled: list[str],
    ) -> None:
        snapshot = self.client.take_snapshot(page_id)
        analyzed_form = self._form_analyzer.analyze_browseros_snapshot(
            [
                BrowserOSFieldElement(
                    element_id=element.element_id,
                    element_type=element.element_type,
                    text=element.text,
                )
                for element in snapshot
            ]
        )
        if analyzed_form.requires_review():
            raise FormReviewRequired(
                "Form analysis requires human review before submission.",
                form=analyzed_form,
                details={"summary": analyzed_form.review_summary()},
            )

        for derived_action in analyzed_form.to_ariadne_actions():
            replay_action = ReplayAction.model_validate(
                derived_action, from_attributes=True
            )
            self._execute_action(
                page_id=page_id,
                action=replay_action,
                context=context,
                cv_path=cv_path,
                letter_path=letter_path,
                fields_filled=fields_filled,
            )

    def _build_hitl_request(
        self,
        step: ReplayStep,
        *,
        reason: str,
        message: str,
    ) -> HumanInterventionRequired:
        return HumanInterventionRequired(
            message,
            reason=reason,
            step_index=step.step_index,
            details={"step_name": step.name},
        )
