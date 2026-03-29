"""Pipeline scrape node adapters for schema-v0."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.core.data_manager import DataManager
from src.core.state import GraphState
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def make_scrape_node(data_manager: DataManager):
    """Create the scrape node adapter that persists canonical scrape artifacts."""

    async def scrape_node(state: GraphState) -> dict:
        from src.ai.scraper.main import PROVIDERS

        source = state["source"]
        job_id = state["job_id"]
        source_dir = Path("data/source") / source / job_id
        json_path = source_dir / "extracted_data.json"
        content_path = source_dir / "content.md"

        try:
            if not json_path.exists():
                adapter = PROVIDERS[source]
                await adapter.run(already_scraped=[], limit=1)

            if not json_path.exists():
                raise FileNotFoundError(f"Scraped state not found at {json_path}")

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            state_ref = data_manager.write_json_artifact(
                source=source,
                job_id=job_id,
                node_name="scrape",
                stage="proposed",
                filename="state.json",
                data=payload,
            )

            refs = {**state.get("artifact_refs", {}), "scrape_state": str(state_ref)}
            if content_path.exists():
                content_ref = data_manager.write_text_artifact(
                    source=source,
                    job_id=job_id,
                    node_name="scrape",
                    stage="proposed",
                    filename="content.md",
                    content=content_path.read_text(encoding="utf-8"),
                )
                refs["scrape_content"] = str(content_ref)

            logger.info(
                f"{LogTag.OK} Persisted canonical scrape artifacts for {source}/{job_id}"
            )
            return {
                "artifact_refs": refs,
                "current_node": "scrape",
                "status": "running",
            }
        except Exception as exc:
            logger.error(f"{LogTag.FAIL} Scrape node failed: {exc}")
            return {
                "current_node": "scrape",
                "status": "failed",
                "error_state": {"node": "scrape", "message": str(exc), "details": None},
            }

    return scrape_node
