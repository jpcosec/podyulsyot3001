"""Ariadne Recorder — Session Capture & Trace Persistence.

Handles the real-time logging of raw interaction events and their 
persistence to the data artifact store.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.data_manager import DataManager
from .trace_models import AriadneSessionTrace, RawTraceEvent

logger = logging.getLogger(__name__)


class AriadneRecorder:
    """Manages raw trace capture for a single automation session."""

    def __init__(self, portal_name: str, data_manager: Optional[DataManager] = None):
        self.data_manager = data_manager or DataManager()
        self.portal_name = portal_name
        self.session_id = f"rec_{portal_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.trace = AriadneSessionTrace(
            session_id=self.session_id,
            portal_name=portal_name,
            start_time=datetime.now()
        )
        self._recording_path = self._get_session_dir() / "raw_trace.jsonl"
        self._recording_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_session_dir(self) -> Path:
        """Returns the directory where session artifacts are stored."""
        return Path("data/ariadne/recordings") / self.session_id

    def log_event(self, event_type: str, **kwargs) -> None:
        """Capture a raw event and append it to the live trace file."""
        event = RawTraceEvent(event_type=event_type, **kwargs)
        self.trace.events.append(event)
        
        # Append to JSONL for crash resilience
        with open(self._recording_path, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")
            
        logger.debug("Ariadne logged event: %s", event_type)

    def capture_screenshot(self, name: str, content: bytes) -> str:
        """Save a screenshot artifact and return its relative path."""
        filename = f"{name}.png"
        path = self._get_session_dir() / "screenshots" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path.relative_to(self._get_session_dir()))

    def stop(self) -> str:
        """Finalize the recording and return the session ID."""
        self.trace.end_time = datetime.now()
        
        # Write the full trace manifest
        trace_path = self._get_session_dir() / "trace_manifest.json"
        trace_path.write_text(self.trace.model_dump_json(indent=2), encoding="utf-8")
        
        logger.info("Ariadne recording finished: %s", self.session_id)
        return self.session_id
