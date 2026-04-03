"""BrowserOS-backed apply providers wired into the common apply CLI."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.apply.browseros_client import BrowserOSClient
from src.apply.browseros_executor import (
    BrowserOSObserveError,
    BrowserOSPlaybookExecutor,
)
from src.apply.browseros_models import BrowserOSPlaybook
from src.apply.models import ApplicationRecord, ApplyMeta
from src.core.data_manager import DataManager
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class BrowserOSApplyProvider:
    """Source-specific provider backed only by BrowserOS MCP."""

    def __init__(
        self,
        *,
        source_name: str,
        portal_base_url: str,
        playbook_path: Path,
        candidate_profile: dict[str, Any] | None = None,
        data_manager: DataManager | None = None,
        client: BrowserOSClient | None = None,
    ) -> None:
        self.source_name = source_name
        self.portal_base_url = portal_base_url
        self.playbook_path = playbook_path
        self.candidate_profile = candidate_profile or {}
        self.data_manager = data_manager or DataManager()
        self.client = client or BrowserOSClient()
        self.executor = BrowserOSPlaybookExecutor(self.client)

    async def setup_session(self) -> None:
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
    ) -> ApplyMeta:
        del letter_path
        self._check_idempotency(job_id)
        ingest_data = self._read_ingest_artifact(job_id)
        application_url = ingest_data.get("application_url") or ingest_data.get("url")
        if not application_url:
            raise ValueError(f"No application_url in ingest artifact for {job_id}")

        playbook = BrowserOSPlaybook.model_validate_json(
            self.playbook_path.read_text(encoding="utf-8")
        )
        timestamp = datetime.now(timezone.utc).isoformat()
        page_id = self.client.new_hidden_page()

        try:
            self.client.navigate(application_url, page_id)
            result = self.executor.run(
                page_id=page_id,
                playbook=playbook,
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
                "first_name": self.candidate_profile.get("first_name"),
                "last_name": self.candidate_profile.get("last_name"),
                "phone": self.candidate_profile.get("phone"),
                "phone_country_code": self.candidate_profile.get("phone_country_code"),
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
    manager = data_manager or DataManager()
    playbook_dir = Path(__file__).resolve().parent / "playbooks"
    return {
        "linkedin": BrowserOSApplyProvider(
            source_name="linkedin",
            portal_base_url="https://www.linkedin.com",
            playbook_path=playbook_dir / "linkedin_easy_apply_v1.json",
            candidate_profile=profile_data,
            data_manager=manager,
        )
    }
