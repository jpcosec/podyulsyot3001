"""Ariadne Session — Orchestrator for portal apply flows."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.automation.contracts import ApplyJobContext, CandidateProfile, ExecutionContext
from src.automation.credentials import CredentialStore
from src.automation.ariadne.exceptions import (
    HumanInterventionRequired,
    TaskAborted,
    TerminalStateReached,
)
from src.automation.ariadne.danger_contracts import (
    ApplyDangerFinding,
    ApplyDangerSignals,
)
from src.automation.ariadne.danger_detection import ApplyDangerDetector
from src.automation.ariadne.hitl import ApplyHitlController
from src.automation.ariadne.models import ApplyMeta, AriadnePortalMap
from src.automation.ariadne.motor_protocol import MotorProvider
from src.automation.ariadne.navigator import AriadneNavigator
from src.automation.portals.routing import resolve_portal_routing
from src.automation.storage import AutomationStorage
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class UnsupportedRoutingDecisionError(Exception):
    """Raised when a portal route cannot be executed by the Ariadne map runtime."""


class AriadneSession:
    """Owns the apply orchestration loop: map loading, navigation, step dispatch.

    The motor is injected at run-time so the same session can be driven by any
    motor (Crawl4AI, BrowserOS, future Vision motor) without changes here.
    """

    def __init__(
        self,
        portal_name: str,
        storage: AutomationStorage | None = None,
        *,
        input_func=input,
    ) -> None:
        self.portal_name = portal_name
        self.storage = storage or AutomationStorage()
        self._map: AriadnePortalMap | None = None
        self._hitl = ApplyHitlController(self.storage, input_func=input_func)
        self._danger_detector = ApplyDangerDetector()

    @property
    def portal_map(self) -> AriadnePortalMap:
        """Load the portal map lazily from `src/automation/portals/<name>/maps/easy_apply.json`."""
        if not self._map:
            map_path = (
                Path(__file__).parent.parent
                / "portals"
                / self.portal_name
                / "maps"
                / "easy_apply.json"
            )
            if not map_path.exists():
                raise FileNotFoundError(
                    f"Ariadne Map not found for '{self.portal_name}' at {map_path}"
                )
            with open(map_path) as f:
                self._map = AriadnePortalMap.model_validate(json.load(f))
        return self._map

    async def run(
        self,
        motor: MotorProvider,
        *,
        job_id: str,
        cv_path: Path,
        letter_path: Path | None = None,
        profile: dict[str, Any] | CandidateProfile | None = None,
        credentials: dict[str, Any] | CredentialStore | None = None,
        dry_run: bool = False,
        path_id: str | None = None,
    ) -> ApplyMeta:
        """Run an apply flow using the supplied motor.

        Args:
            motor: A MotorProvider that opens browser sessions.
            job_id: The job to apply to.
            cv_path: Local path to the CV file.
            letter_path: Optional cover letter.
            profile: Candidate profile payload for placeholder resolution.
            credentials: Optional credential metadata for login-required flows.
            dry_run: If True, stop at the first step marked dry_run_stop.
            path_id: Optional explicit path override when the resolved route stays onsite.

        Returns:
            ApplyMeta with final status.

        Raises:
            RuntimeError: If the job was already submitted.
            ValueError: If the resolved path_id does not exist in the map.
            TerminalStateReached: If the navigator detects a failure state.
        """
        self._raise_for_danger(
            self._danger_detector.detect(
                ApplyDangerSignals(
                    already_submitted=self.storage.check_already_submitted(
                        self.portal_name, job_id
                    )
                )
            ),
            step=None,
        )

        portal_map = self.portal_map
        ingest_data = self.storage.get_job_state(self.portal_name, job_id)
        session_id = f"apply_{self.portal_name}_{job_id}"
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            route = resolve_portal_routing(self.portal_name, ingest_data)
            self._raise_for_danger(
                self._danger_detector.detect(
                    ApplyDangerSignals(
                        route_outcome=route.outcome,
                        route_reason=route.reason,
                        application_url=route.application_url,
                    )
                ),
                step=None,
                unsupported_error_cls=UnsupportedRoutingDecisionError,
            )

            selected_path_id = path_id or route.path_id
            if not selected_path_id:
                raise ValueError(
                    f"No Ariadne path resolved for onsite route in {self.portal_name}"
                )

            path = portal_map.paths.get(selected_path_id)
            if not path:
                raise ValueError(
                    f"Path '{selected_path_id}' not found in map for {self.portal_name}"
                )

            application_url = route.application_url
            if not application_url:
                raise ValueError(
                    f"No application_url resolved for onsite route in job {job_id}"
                )

            candidate_profile = self.storage.load_candidate_profile(profile)
            credential_store = self.storage.load_credential_store(credentials)
            resolved_credentials = credential_store.resolve(
                self.portal_name, application_url
            )
            context = self._build_context(
                ingest_data=ingest_data,
                profile=candidate_profile,
                cv_path=cv_path,
                letter_path=letter_path,
                application_url=application_url,
            )
            all_selectors = self._collect_selectors(portal_map)
            navigator = AriadneNavigator(portal_map)

            async with motor.open_session(
                session_id,
                credentials=resolved_credentials,
            ) as ms:
                step_index = 1
                while step_index <= len(path.steps):
                    step = path.steps[step_index - 1]

                    if dry_run and step.dry_run_stop:
                        logger.info(
                            "%s Dry-run stop at step '%s'", LogTag.OK, step.name
                        )
                        break

                    try:
                        self._raise_for_danger(
                            await ms.inspect_danger(application_url),
                            step=step,
                        )
                        obs = await ms.observe(all_selectors)
                        current_state = navigator.find_current_state(obs)

                        finished, mission_status = navigator.check_mission_status(
                            path.task_id, current_state or ""
                        )
                        if finished:
                            if mission_status == "terminal_failure":
                                raise TerminalStateReached(
                                    f"Reached failure state: {current_state}"
                                )
                            break

                        logger.info(
                            "%s Step %s/%s: %s",
                            LogTag.FAST,
                            step_index,
                            len(path.steps),
                            step.name,
                        )
                        await ms.execute_step(
                            step=step,
                            context=context,
                            cv_path=cv_path,
                            letter_path=letter_path,
                            is_first=(step_index == 1),
                            url=application_url,
                        )
                        self._raise_for_danger(
                            await ms.inspect_danger(application_url),
                            step=step,
                        )
                    except HumanInterventionRequired as exc:
                        (
                            resumed_index,
                            finished,
                            mission_status,
                        ) = await self._handle_hitl_pause(
                            ms=ms,
                            navigator=navigator,
                            path=path,
                            task_id=path.task_id,
                            current_step_index=step_index,
                            all_selectors=all_selectors,
                            session_id=session_id,
                            job_id=job_id,
                            step=step,
                            application_url=application_url,
                            exc=exc,
                        )
                        if finished:
                            break
                        step_index = resumed_index
                        continue

                    obs_after = await ms.observe(all_selectors)
                    next_state = navigator.find_current_state(obs_after)
                    step_index = navigator.get_next_step_index(
                        path, step_index, next_state
                    )

            final_status = "dry_run" if dry_run else "submitted"
            meta = ApplyMeta(status=final_status, timestamp=timestamp)
            self.storage.write_apply_meta(self.portal_name, job_id, meta.model_dump())
            logger.info("%s Apply finished: %s", LogTag.OK, final_status)
            return meta

        except Exception as exc:
            logger.error("%s Apply failed: %s", LogTag.FAIL, exc)
            error_meta = ApplyMeta(status="failed", timestamp=timestamp, error=str(exc))
            self.storage.write_apply_meta(
                self.portal_name, job_id, error_meta.model_dump()
            )
            raise

    def _collect_selectors(self, portal_map: AriadnePortalMap) -> set[str]:
        """Collect all CSS selectors from state presence predicates."""
        selectors: set[str] = set()
        for state in portal_map.states.values():
            for target in state.presence_predicate.required_elements:
                if target.css:
                    selectors.add(target.css)
        return selectors

    def _build_context(
        self,
        ingest_data: dict[str, Any],
        profile: CandidateProfile,
        cv_path: Path,
        letter_path: Path | None,
        application_url: str | None,
    ) -> dict[str, Any]:
        return ExecutionContext(
            profile=profile,
            job=ApplyJobContext(
                job_title=ingest_data.get("job_title", ""),
                company_name=ingest_data.get("company_name", ""),
                application_url=application_url or "",
            ),
            cv_path=str(cv_path),
            letter_path=str(letter_path) if letter_path else None,
        ).to_runtime_dict()

    def _raise_for_danger(
        self,
        report: Any,
        *,
        step: Any,
        unsupported_error_cls: type[Exception] | None = None,
    ) -> None:
        finding = report.primary if report else None
        if finding is None:
            return
        if finding.recommended_action == "pause":
            raise HumanInterventionRequired(
                finding.message,
                reason=finding.code,
                step_index=getattr(step, "step_index", None),
                details={"danger_source": finding.source},
            )
        if unsupported_error_cls is not None and finding.source == "routing":
            raise unsupported_error_cls(
                f"Portal routing resolved to '{finding.code}' for {self.portal_name}: {finding.message}"
            )
        raise RuntimeError(self._danger_message(finding))

    def _danger_message(self, finding: ApplyDangerFinding) -> str:
        if finding.code == "duplicate_submission":
            return f"Job was already submitted. {finding.message}"
        return f"Danger {finding.code}: {finding.message}"

    async def _handle_hitl_pause(
        self,
        *,
        ms: Any,
        navigator: AriadneNavigator,
        path: Any,
        task_id: str,
        current_step_index: int,
        all_selectors: set[str],
        session_id: str,
        job_id: str,
        step: Any,
        application_url: str | None,
        exc: HumanInterventionRequired,
    ) -> tuple[int, bool, str | None]:
        self.storage.write_apply_meta(
            self.portal_name,
            job_id,
            ApplyMeta(
                status="interrupted",
                timestamp=datetime.now(timezone.utc).isoformat(),
                error=str(exc),
            ).model_dump(),
        )
        decision = await self._hitl.pause(
            motor_session=ms,
            session_id=session_id,
            portal_name=self.portal_name,
            job_id=job_id,
            step=step,
            reason=exc.reason,
            message=str(exc),
            application_url=application_url,
        )
        if decision.action == "abort":
            raise TaskAborted(
                f"Operator aborted apply run at step {step.step_index}: {step.name}",
                step_index=step.step_index,
            ) from exc
        resumed_index, finished, mission_status = await self._resume_after_hitl(
            ms=ms,
            navigator=navigator,
            path=path,
            task_id=task_id,
            current_step_index=current_step_index,
            all_selectors=all_selectors,
        )
        if finished and mission_status == "terminal_failure":
            raise TerminalStateReached(
                "Reached failure state during manual intervention"
            ) from exc
        return resumed_index, finished, mission_status

    async def _resume_after_hitl(
        self,
        *,
        ms: Any,
        navigator: AriadneNavigator,
        path: Any,
        task_id: str,
        current_step_index: int,
        all_selectors: set[str],
    ) -> tuple[int, bool, str | None]:
        """Re-observe the page after manual intervention and decide where to resume."""
        obs = await ms.observe(all_selectors)
        current_state = navigator.find_current_state(obs)
        finished, mission_status = navigator.check_mission_status(
            task_id, current_state or ""
        )
        if finished:
            return current_step_index, True, mission_status
        for index, step in enumerate(path.steps, start=1):
            if (
                step.state_id
                and step.state_id == current_state
                and index > current_step_index
            ):
                return index, False, None
        return current_step_index, False, None
