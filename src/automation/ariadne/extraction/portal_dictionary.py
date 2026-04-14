"""PortalDictionary — per-portal mapping of schema_id → JsonCssExtractionStrategy.

Bridges the abstract Labyrinth (AbstractElement / schema_id) with
Crawl4AI's concrete extraction (JsonCssExtractionStrategy).

Usage:
    pd = PortalDictionary.load("stepstone", builder)
    strategy = pd.get_strategy("job_listings")   # ready to pass to CrawlerRunConfig
"""

from __future__ import annotations

import json
from pathlib import Path

from crawl4ai import JsonCssExtractionStrategy

from src.automation.ariadne.extraction.schema_builder import SchemaBuilder

DATA_ROOT = Path("data/portals")


class PortalDictionary:

    def __init__(self, portal_name: str, builder: SchemaBuilder) -> None:
        self._portal_name = portal_name
        self._builder = builder
        self._strategies: dict[str, JsonCssExtractionStrategy] = {}

    def get_strategy(self, schema_id: str) -> JsonCssExtractionStrategy | None:
        """Return ready-to-use extraction strategy, or None if schema not built yet."""
        if schema_id in self._strategies:
            return self._strategies[schema_id]
        schema = self._builder.load_cached(schema_id)
        if schema:
            strategy = JsonCssExtractionStrategy(schema)
            self._strategies[schema_id] = strategy
            return strategy
        return None

    def register(self, schema_id: str, sample_html: str, query: str) -> JsonCssExtractionStrategy:
        """Build schema (or load from cache) and register strategy."""
        schema = self._builder.build(schema_id, sample_html, query)
        strategy = JsonCssExtractionStrategy(schema)
        self._strategies[schema_id] = strategy
        return strategy

    @classmethod
    def load(cls, portal_name: str, builder: SchemaBuilder) -> "PortalDictionary":
        """Load all cached schemas for this portal into ready strategies."""
        pd = cls(portal_name, builder)
        schemas_dir = DATA_ROOT / portal_name / "schemas"
        if schemas_dir.exists():
            for schema_file in schemas_dir.glob("*.json"):
                schema_id = schema_file.stem
                schema = json.loads(schema_file.read_text())
                pd._strategies[schema_id] = JsonCssExtractionStrategy(schema)
        return pd
