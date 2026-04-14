"""Extractor — protocol for running structured data extraction on a page snapshot."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from src.automation.ariadne.thread.action import ExtractionAction
    from src.automation.contracts.sensor import SnapshotResult


class Extractor(Protocol):
    async def extract(
        self, action: "ExtractionAction", snapshot: "SnapshotResult"
    ) -> list[dict]:
        """Apply the schema keyed by action.schema_id to snapshot.html and return records."""
        ...
