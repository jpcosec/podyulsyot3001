"""Pipeline translate node adapters for schema-v0."""

from __future__ import annotations

import logging

from src.core.data_manager import DataManager
from src.core.state import GraphState
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def make_translate_node(data_manager: DataManager):
    """Create the translate node adapter that persists canonical translated artifacts."""

    def _translate_sync(
        source: str, job_id: str, artifact_refs: dict[str, str]
    ) -> dict:
        from src.core.tools.translator.main import P_FIELDS_TO_TRANSLATE
        from src.core.tools.translator.providers.google.adapter import (
            GoogleTranslatorAdapter,
        )

        adapter = GoogleTranslatorAdapter()
        raw_state = data_manager.read_json_artifact(
            source=source,
            job_id=job_id,
            node_name="ingest",
            stage="proposed",
            filename="state.json",
        )
        raw_content = artifact_refs.get("ingest_content")
        content_md = ""
        if raw_content:
            content_md = data_manager.read_text_artifact(
                source=source,
                job_id=job_id,
                node_name="ingest",
                stage="proposed",
                filename="content.md",
            )

        original_language = raw_state.get("original_language", "auto")
        if original_language == "en":
            translated_state = raw_state
            translated_content = content_md
        else:
            translated_state = adapter.translate_fields(
                raw_state,
                fields=P_FIELDS_TO_TRANSLATE,
                target_lang="en",
                source_lang=original_language,
            )
            translated_state["original_language"] = "en"
            translated_content = (
                adapter.translate_text(
                    content_md,
                    target_lang="en",
                    source_lang=original_language,
                )
                if content_md
                else ""
            )

        state_ref = data_manager.write_json_artifact(
            source=source,
            job_id=job_id,
            node_name="translate",
            stage="proposed",
            filename="state.json",
            data=translated_state,
        )
        refs = {
            **artifact_refs,
            "translated_state": str(state_ref),
        }
        if translated_content:
            content_ref = data_manager.write_text_artifact(
                source=source,
                job_id=job_id,
                node_name="translate",
                stage="proposed",
                filename="content.md",
                content=translated_content,
            )
            refs["translated_content"] = str(content_ref)

        return refs

    def translate_node(state: GraphState) -> dict:
        source = state["source"]
        job_id = state["job_id"]

        try:
            refs = _translate_sync(source, job_id, state.get("artifact_refs", {}))

            logger.info(
                f"{LogTag.OK} Persisted translated artifacts for {source}/{job_id}"
            )
            return {
                "artifact_refs": refs,
                "current_node": "translate",
                "status": "running",
            }
        except Exception as exc:
            logger.error(f"{LogTag.FAIL} Translate node failed: {exc}")
            return {
                "current_node": "translate",
                "status": "failed",
                "error_state": {
                    "node": "translate",
                    "message": str(exc),
                    "details": None,
                },
            }

    return translate_node
