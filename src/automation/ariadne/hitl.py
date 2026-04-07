"""HITL support for Ariadne apply runs.

This module defines the persisted interrupt contract and the terminal-first
controller AriadneSession uses to pause and resume active apply sessions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.automation.ariadne.models import AriadneStep
from src.automation.storage import AutomationStorage


class ApplyInterruptRecord(BaseModel):
    """Persisted context for one human-in-the-loop pause."""

    session_id: str = Field(description="Stable apply-session identifier.")
    portal_name: str = Field(description="Portal/source name for the active job.")
    job_id: str = Field(description="Job identifier for the active apply run.")
    status: Literal["pending", "resumed", "aborted"] = Field(
        description="Current lifecycle status of the interrupt record."
    )
    reason: str = Field(description="Machine-friendly reason code for the pause.")
    message: str = Field(
        description="Human-readable explanation shown to the operator."
    )
    step_index: int = Field(description="1-based path step where the pause happened.")
    step_name: str = Field(description="Step name where the pause happened.")
    application_url: str | None = Field(
        default=None, description="Resolved application URL for operator context."
    )
    created_at: str = Field(description="ISO timestamp when the pause started.")
    resolved_at: str | None = Field(
        default=None, description="ISO timestamp when the pause was resolved."
    )
    screenshot_path: str | None = Field(
        default=None, description="Optional screenshot artifact captured for the pause."
    )
    snapshot_path: str | None = Field(
        default=None,
        description="Optional text snapshot artifact captured for the pause.",
    )
    motor_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Backend-specific context captured at interruption time.",
    )
    decision_action: Literal["resume", "abort"] | None = Field(
        default=None, description="Final operator action once the pause is resolved."
    )
    decision_note: str | None = Field(
        default=None, description="Optional operator note recorded with the decision."
    )


class ApplyDecisionRecord(BaseModel):
    """One persisted operator decision for an interrupted apply run."""

    action: Literal["resume", "abort"] = Field(
        description="Operator action chosen in the terminal controller."
    )
    note: str | None = Field(
        default=None, description="Optional free-text note supplied by the operator."
    )
    step_index: int = Field(description="Step index associated with the decision.")
    step_name: str = Field(description="Step name associated with the decision.")
    reason: str = Field(description="Reason code that triggered the pause.")
    decided_at: str = Field(description="ISO timestamp when the decision was taken.")


class ApplyHitlController:
    """Pause active sessions, persist interrupt artifacts, and collect decisions."""

    def __init__(self, storage: AutomationStorage, *, input_func=input) -> None:
        self._storage = storage
        self._input_func = input_func

    async def pause(
        self,
        *,
        motor_session: Any,
        session_id: str,
        portal_name: str,
        job_id: str,
        step: AriadneStep,
        reason: str,
        message: str,
        application_url: str | None,
    ) -> ApplyDecisionRecord:
        """Persist an interrupt, prompt the operator, and return the decision."""
        hitl_dir = self._storage.get_apply_hitl_dir(
            portal_name, job_id, step.step_index
        )
        captured = await motor_session.begin_human_intervention(hitl_dir, step, reason)
        interrupt = ApplyInterruptRecord(
            session_id=session_id,
            portal_name=portal_name,
            job_id=job_id,
            status="pending",
            reason=reason,
            message=message,
            step_index=step.step_index,
            step_name=step.name,
            application_url=application_url,
            created_at=self._timestamp(),
            screenshot_path=self._to_str(captured.get("screenshot_path")),
            snapshot_path=self._to_str(captured.get("snapshot_path")),
            motor_context=self._normalize_context(captured),
        )
        self._storage.write_apply_interrupt(
            portal_name, job_id, interrupt.model_dump(mode="json")
        )
        action = self._prompt_action(interrupt)
        note = self._prompt_note(action)
        decision = ApplyDecisionRecord(
            action=action,
            note=note,
            step_index=step.step_index,
            step_name=step.name,
            reason=reason,
            decided_at=self._timestamp(),
        )
        self._storage.append_apply_hitl_decision(
            portal_name, job_id, decision.model_dump(mode="json")
        )
        resolved = interrupt.model_copy(
            update={
                "status": "resumed" if action == "resume" else "aborted",
                "resolved_at": decision.decided_at,
                "decision_action": action,
                "decision_note": note,
            }
        )
        self._storage.write_apply_interrupt(
            portal_name, job_id, resolved.model_dump(mode="json")
        )
        return decision

    def _prompt_action(
        self, interrupt: ApplyInterruptRecord
    ) -> Literal["resume", "abort"]:
        prompt = (
            f"[apply/hitl] Step {interrupt.step_index} '{interrupt.step_name}' paused"
            f" ({interrupt.reason}). Screenshot: {interrupt.screenshot_path or 'n/a'}"
            f". Snapshot: {interrupt.snapshot_path or 'n/a'}. [r]esume/[a]bort: "
        )
        while True:
            answer = self._input_func(prompt).strip().lower()
            if answer in {"r", "resume"}:
                return "resume"
            if answer in {"a", "abort"}:
                return "abort"

    def _prompt_note(self, action: Literal["resume", "abort"]) -> str | None:
        note = self._input_func(
            f"[apply/hitl] Optional note for {action} (press Enter to skip): "
        ).strip()
        return note or None

    def _normalize_context(self, captured: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key, value in captured.items():
            normalized[key] = self._to_str(value) if isinstance(value, Path) else value
        return normalized

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _to_str(self, value: Any) -> str | None:
        if value is None:
            return None
        return str(value)
