"""SchemaBuilder — wraps generate_schema() for one-time LLM cost.

Call once per (portal, room, query). Result cached to disk forever.
Subsequent calls load from cache with zero LLM cost.
"""

from __future__ import annotations

import json
from pathlib import Path

from crawl4ai import LLMConfig
from crawl4ai import JsonCssExtractionStrategy

DATA_ROOT = Path("data/portals")


class SchemaBuilder:

    def __init__(self, portal_name: str, llm_config: LLMConfig) -> None:
        self._portal_name = portal_name
        self._llm_config = llm_config

    def build(self, schema_id: str, sample_html: str, query: str) -> dict:
        """Return cached schema or generate it via LLM (one call)."""
        cached = self._load(schema_id)
        if cached:
            return cached
        schema = JsonCssExtractionStrategy.generate_schema(
            html=sample_html,
            query=query,
            llm_config=self._llm_config,
        )
        self._save(schema_id, schema)
        return schema

    def _load(self, schema_id: str) -> dict | None:
        path = self._schema_path(schema_id)
        if path.exists():
            return json.loads(path.read_text())
        return None

    def _save(self, schema_id: str, schema: dict) -> None:
        path = self._schema_path(schema_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(schema, indent=2))

    def _schema_path(self, schema_id: str) -> Path:
        return DATA_ROOT / self._portal_name / "schemas" / f"{schema_id}.json"
