"""BrowserOS-backed apply providers using Ariadne Semantic Maps."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.automation.ariadne.models import ApplicationRecord, ApplyMeta, AriadnePortalMap
from src.automation.motors.browseros.cli.client import BrowserOSClient
from src.automation.motors.browseros.cli.executor import (
    BrowserOSObserveError,
    BrowserOSPlaybookExecutor,
)
from src.core.data_manager import DataManager
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class BrowserOSApplyProvider:
    """Source-specific provider backed only by BrowserOS MCP, consuming Ariadne Maps."""

    def __init__(
        self,
        *,
        portal_map: AriadnePortalMap,
        candidate_profile: dict[str, Any] | None = None,
        data_manager: DataManager | None = None,
        client: BrowserOSClient | None = None,
    ) -> None:
        self.portal_map = portal_map
        self.source_name = portal_map.portal_name
        self.portal_base_url = portal_map.base_url
        self.candidate_profile = candidate_profile or {}
        self.data_manager = data_manager or DataManager()
        self.client = client or BrowserOSClient()
        self.executor = BrowserOSPlaybookExecutor(self.client)

    async def setup_session(self) -> None:
        """Open a visible BrowserOS page and wait for manual login."""
        page_id = self.client.new_page()
        self.client.navigate(self.portal_base_url, page_id)
        self.client.show_page(page_id)
        input(f"\n[{self.source_name}] Log in in BrowserOS, then press Enter.\n")
        logger.info("%s BrowserOS session ready for %s", LogTag.OK, self.source_name)

    async def run(
        self,
        *,
        job_id: str,
        cv_path: Path,
        letter_path: Path | None,
        dry_run: bool,
        path_id: str = "standard_easy_apply",
    ) -> ApplyMeta:
        """Run a BrowserOS-backed application flow using an Ariadne path."""
        del letter_path
        self._check_idempotency(job_id)
        ingest_data = self._read_ingest_artifact(job_id)
        application_url = ingest_data.get("application_url") or ingest_data.get("url")
        if not application_url:
            raise ValueError(f"No application_url in ingest artifact for {job_id}")

        path = self.portal_map.paths.get(path_id)
        if not path:
            raise ValueError(f"Path '{path_id}' not found in map for {self.source_name}")

        timestamp = datetime.now(timezone.utc).isoformat()
        page_id = self.client.new_hidden_page()

        try:
            self.client.navigate(application_url, page_id)
            result = self.executor.run(
                page_id=page_id,
                path=path,
                context=self._build_context(ingest_data, cv_path),
                cv_path=cv_path,
                dry_run=dry_run,
            )
            screenshot_name = (
                "screenshot.png"
                if result.status == "dry_run"
                else "screenshot_submitted.png"
            )
            self.client.save_screenshot(
                page_id, self._artifact_path(job_id, "proposed", screenshot_name)
            )
            record = self._build_application_record(
                job_id=job_id,
                ingest_data=ingest_data,
                application_url=application_url,
                cv_path=cv_path,
                dry_run=result.status == "dry_run",
                submitted_at=None
                if result.status == "dry_run"
                else datetime.now(timezone.utc).isoformat(),
                confirmation_text=result.confirmation_text,
                fields_filled=result.fields_filled,
            )
            self._write_application_record(job_id, record)
            meta = ApplyMeta(status=result.status, timestamp=timestamp)
            self._write_apply_meta(job_id, meta)
            return meta
        except Exception as exc:
            error_status = (
                "portal_changed" if isinstance(exc, BrowserOSObserveError) else "failed"
            )
            try:
                self.client.save_screenshot(
                    page_id, self._artifact_path(job_id, "proposed", "error_state.png")
                )
            except Exception:
                pass
            meta = ApplyMeta(status=error_status, timestamp=timestamp, error=str(exc))
            self._write_apply_meta(job_id, meta)
            raise
        finally:
            try:
                self.client.close_page(page_id)
            except Exception:
                logger.warning(
                    "%s Failed to close BrowserOS page %s", LogTag.WARN, page_id
                )

    def _build_context(
        self, ingest_data: dict[str, Any], cv_path: Path
    ) -> dict[str, Any]:
        return {
            "profile": {
                "first_name": self.candidate_profile.get("first_name", "Juan Pablo"),
                "last_name": self.candidate_profile.get("last_name", "Ruiz"),
                "phone": self.candidate_profile.get("phone", "+49123456789"),
                "email": self.candidate_profile.get("email", "jp@example.com"),
            },
            "job": {
                "job_title": ingest_data.get("job_title", ""),
                "company_name": ingest_data.get("company_name", ""),
                "application_url": ingest_data.get("application_url")
                or ingest_data.get("url", ""),
            },
            "cv_path": str(cv_path),
            "cv_filename": cv_path.name,
        }

    def _check_idempotency(self, job_id: str) -> None:
        try:
            meta = self.data_manager.read_json_artifact(
                source=self.source_name,
                job_id=job_id,
                node_name="apply",
                stage="meta",
                filename="apply_meta.json",
            )
        except (FileNotFoundError, KeyError):
            return
        if meta.get("status") == "submitted":
            raise RuntimeError(
                f"Job {job_id} ({self.source_name}) was already submitted."
            )

    def _read_ingest_artifact(self, job_id: str) -> dict[str, Any]:
        return self.data_manager.read_json_artifact(
            source=self.source_name,
            job_id=job_id,
            node_name="ingest",
            stage="proposed",
            filename="state.json",
        )

    def _write_apply_meta(self, job_id: str, meta: ApplyMeta) -> None:
        self.data_manager.write_json_artifact(
            source=self.source_name,
            job_id=job_id,
            node_name="apply",
            stage="meta",
            filename="apply_meta.json",
            data=meta.model_dump(),
        )

    def _write_application_record(self, job_id: str, record: ApplicationRecord) -> None:
        self.data_manager.write_json_artifact(
            source=self.source_name,
            job_id=job_id,
            node_name="apply",
            stage="proposed",
            filename="application_record.json",
            data=record.model_dump(),
        )

    def _artifact_path(self, job_id: str, stage: str, filename: str) -> Path:
        path = self.data_manager.artifact_path(
            source=self.source_name,
            job_id=job_id,
            node_name="apply",
            stage=stage,
            filename=filename,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _build_application_record(
        self,
        *,
        job_id: str,
        ingest_data: dict[str, Any],
        application_url: str,
        cv_path: Path,
        dry_run: bool,
        submitted_at: str | None,
        confirmation_text: str | None,
        fields_filled: list[str],
    ) -> ApplicationRecord:
        return ApplicationRecord(
            source=self.source_name,
            job_id=job_id,
            job_title=ingest_data.get("job_title", ""),
            company_name=ingest_data.get("company_name", ""),
            application_url=application_url,
            cv_path=str(cv_path),
            letter_path=None,
            fields_filled=fields_filled,
            dry_run=dry_run,
            submitted_at=submitted_at,
            confirmation_text=confirmation_text,
        )


def build_browseros_providers(
    data_manager: DataManager | None = None,
    *,
    profile_data: dict[str, Any] | None = None,
) -> dict[str, BrowserOSApplyProvider]:
    """Build BrowserOS-backed apply providers from Ariadne Maps."""
    manager = data_manager or DataManager()
    
    portals_root = Path(__file__).parent.parent.parent.parent.parent / "portals"
    providers = {}
    
    for portal in ["linkedin", "xing", "stepstone"]:
        map_path = portals_root / portal / "maps" / "easy_apply.json"
        if map_path.exists():
            with open(map_path, "r") as f:
                portal_map = AriadnePortalMap.model_validate(json.load(f))
                providers[portal] = BrowserOSApplyProvider(
                    portal_map=portal_map,
                    candidate_profile=profile_data,
                    data_manager=manager,
                )
    
    return providers
