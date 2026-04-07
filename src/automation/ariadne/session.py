"""Ariadne Session — Orchestrator for portal apply flows."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.automation.ariadne.exceptions import TerminalStateReached
from src.automation.ariadne.models import ApplyMeta, AriadnePortalMap
from src.automation.ariadne.motor_protocol import MotorProvider
from src.automation.ariadne.navigator import AriadneNavigator
from src.automation.storage import AutomationStorage
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class AriadneSession:
    """Owns the apply orchestration loop: map loading, navigation, step dispatch.

    The motor is injected at run-time so the same session can be driven by any
    motor (Crawl4AI, BrowserOS, future Vision motor) without changes here.
    """

    def __init__(
        self,
        portal_name: str,
        storage: AutomationStorage | None = None,
    ) -> None:
        self.portal_name = portal_name
        self.storage = storage or AutomationStorage()
        self._map: AriadnePortalMap | None = None

    @property
    def portal_map(self) -> AriadnePortalMap:
        """Load the portal map lazily from `src/automation/portals/<name>/maps/easy_apply.json`."""
        if not self._map:
            map_path = (
                Path(__file__).parent.parent
                / "portals" / self.portal_name / "maps" / "easy_apply.json"
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
        dry_run: bool = False,
        path_id: str = "standard_easy_apply",
    ) -> ApplyMeta:
        """Run an apply flow using the supplied motor.

        Args:
            motor: A MotorProvider that opens browser sessions.
            job_id: The job to apply to.
            cv_path: Local path to the CV file.
            letter_path: Optional cover letter.
            dry_run: If True, stop at the first step marked dry_run_stop.
            path_id: Which path in the portal map to follow.

        Returns:
            ApplyMeta with final status.

        Raises:
            RuntimeError: If the job was already submitted.
            ValueError: If the path_id does not exist in the map.
            TerminalStateReached: If the navigator detects a failure state.
        """
        if self.storage.check_already_submitted(self.portal_name, job_id):
            raise RuntimeError(
                f"Job {job_id} ({self.portal_name}) was already submitted."
            )

        portal_map = self.portal_map
        path = portal_map.paths.get(path_id)
        if not path:
            raise ValueError(
                f"Path '{path_id}' not found in map for {self.portal_name}"
            )

        ingest_data = self.storage.get_job_state(self.portal_name, job_id)
        application_url = ingest_data.get("application_url") or ingest_data.get("url")
        context = self._build_context(ingest_data, cv_path, letter_path, application_url)
        all_selectors = self._collect_selectors(portal_map)
        navigator = AriadneNavigator(portal_map)
        session_id = f"apply_{self.portal_name}_{job_id}"
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            async with motor.open_session(session_id) as ms:
                step_index = 1
                while step_index <= len(path.steps):
                    step = path.steps[step_index - 1]

                    if dry_run and step.dry_run_stop:
                        logger.info("%s Dry-run stop at step '%s'", LogTag.OK, step.name)
                        break

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

                    obs_after = await ms.observe(all_selectors)
                    next_state = navigator.find_current_state(obs_after)
                    step_index = navigator.get_next_step_index(path, step_index, next_state)

            final_status = "dry_run" if dry_run else "submitted"
            meta = ApplyMeta(status=final_status, timestamp=timestamp)
            self.storage.write_apply_meta(self.portal_name, job_id, meta.model_dump())
            logger.info("%s Apply finished: %s", LogTag.OK, final_status)
            return meta

        except Exception as exc:
            logger.error("%s Apply failed: %s", LogTag.FAIL, exc)
            error_meta = ApplyMeta(status="failed", timestamp=timestamp, error=str(exc))
            self.storage.write_apply_meta(self.portal_name, job_id, error_meta.model_dump())
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
        cv_path: Path,
        letter_path: Path | None,
        application_url: str | None,
    ) -> dict[str, Any]:
        return {
            "profile": {
                "first_name": "Juan Pablo",
                "last_name": "Ruiz",
                "email": "jp@example.com",
                "phone": "+49123456789",
            },
            "job": {
                "job_title": ingest_data.get("job_title", ""),
                "company_name": ingest_data.get("company_name", ""),
                "application_url": application_url or "",
            },
            "cv_path": str(cv_path),
            "letter_path": str(letter_path) if letter_path else None,
        }
