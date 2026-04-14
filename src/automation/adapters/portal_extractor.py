"""PortalExtractor — Extractor backed by PortalDictionary + JsonCssExtractionStrategy.

No browser needed. Applies CSS selectors directly to already-fetched HTML.
"""

from __future__ import annotations

import json

from src.automation.ariadne.thread.action import ExtractionAction
from src.automation.ariadne.extraction.portal_dictionary import PortalDictionary
from src.automation.contracts.sensor import SnapshotResult


class PortalExtractor:
    """Resolves schema_id → strategy, runs CSS extraction on snapshot HTML."""

    def __init__(self, portal_dictionary: PortalDictionary) -> None:
        self._pd = portal_dictionary

    async def extract(self, action: ExtractionAction, snapshot: SnapshotResult) -> list[dict]:
        strategy = self._pd.get_strategy(action.schema_id)
        if not strategy:
            return []
        raw = strategy.extract(snapshot.url, snapshot.html)
        return json.loads(raw) if isinstance(raw, str) else (raw or [])
