"""Automation Storage — Artifact Persistence and Path Resolution.

This module owns the data-plane for the automation package, handling 
all file I/O and artifact placement logic. It abstracts the underlying 
DataManager to provide automation-specific storage semantics.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.core.data_manager import DataManager
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class AutomationStorage:
    """Manager for automation artifacts (traces, snapshots, results)."""

    def __init__(self, data_manager: Optional[DataManager] = None):
        """Initializes the storage manager.
        
        Args:
            data_manager: Optional central DataManager instance.
        """
        self.data_manager = data_manager or DataManager()

    def get_job_state(self, source: str, job_id: str) -> dict[str, Any]:
        """Reads the ingestion state for a specific job.
        
        Args:
            source: Portal name (e.g., 'linkedin').
            job_id: Unique job identifier.
            
        Returns:
            Dict containing the job ingestion state.
        """
        return self.data_manager.read_json_artifact(
            source=source,
            job_id=job_id,
            node_name="ingest",
            stage="proposed",
            filename="state.json"
        )

    def write_apply_meta(self, source: str, job_id: str, data: dict[str, Any]) -> None:
        """Writes application attempt metadata.
        
        Args:
            source: Portal name.
            job_id: Job identifier.
            data: Metadata payload to persist.
        """
        self.data_manager.write_json_artifact(
            source=source,
            job_id=job_id,
            node_name="apply",
            stage="meta",
            filename="apply_meta.json",
            data=data
        )

    def write_artifact(self, source: str, job_id: str, filename: str, content: bytes | str) -> None:
        """Writes a raw artifact (screenshot, HTML, etc) to the job's apply node.
        
        Args:
            source: Portal name.
            job_id: Job identifier.
            filename: Name of the file.
            content: Bytes or string content to write.
        """
        if isinstance(content, bytes):
            self.data_manager.write_bytes_artifact(
                source=source, job_id=job_id, node_name="apply", stage="proposed",
                filename=filename, content=content
            )
        else:
            path = self.data_manager.artifact_path(
                source=source, job_id=job_id, node_name="apply", stage="proposed",
                filename=filename
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def check_already_submitted(self, source: str, job_id: str) -> bool:
        """Checks if a job has already been successfully submitted.
        
        Args:
            source: Portal name.
            job_id: Job identifier.
            
        Returns:
            True if already submitted, False otherwise.
        """
        try:
            meta = self.data_manager.read_json_artifact(
                source=source,
                job_id=job_id,
                node_name="apply",
                stage="meta",
                filename="apply_meta.json",
            )
            return meta.get("status") == "submitted"
        except (FileNotFoundError, KeyError):
            return False
