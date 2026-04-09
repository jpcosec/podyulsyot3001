"""CLI entry point for the translation pipeline.

Scans canonical ingested jobs under ``data/jobs/<source>/<job_id>/`` and reads
raw input artifacts from ``nodes/ingest/proposed/``. Translated artifacts are
written to ``nodes/translate/proposed/``.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from src.core.data_manager import DataManager
from src.core.tools.translator.providers.google.adapter import GoogleTranslatorAdapter
from src.shared.log_tags import LogTag
from src.shared.logging_config import configure_logging

logger = logging.getLogger(__name__)

PROVIDERS = {"google": GoogleTranslatorAdapter()}

P_FIELDS_TO_TRANSLATE = [
    "job_title",
    "company_name",
    "location",
    "employment_type",
    "posted_date",
    "days_ago",
    "responsibilities",
    "requirements",
    "salary",
    "remote_policy",
    "benefits",
    "company_description",
    "company_industry",
    "company_size",
    "application_deadline",
    "application_method",
    "application_instructions",
    "contact_info",
]


def translate_single_job(
    data_manager: DataManager,
    adapter,
    source: str,
    job_id: str,
    *,
    target_lang: str = "en",
    force: bool = False,
) -> bool:
    """Translate a single job's ingest artifacts to the target language.

    Returns True on success or skip, raises on unrecoverable error.
    """
    json_path = data_manager.artifact_path(
        source=source,
        job_id=job_id,
        node_name="ingest",
        stage="proposed",
        filename="state.json",
    )
    md_path = data_manager.artifact_path(
        source=source,
        job_id=job_id,
        node_name="ingest",
        stage="proposed",
        filename="content.md",
    )
    out_json_path = data_manager.artifact_path(
        source=source,
        job_id=job_id,
        node_name="translate",
        stage="proposed",
        filename="state.json",
    )
    out_md_path = data_manager.artifact_path(
        source=source,
        job_id=job_id,
        node_name="translate",
        stage="proposed",
        filename="content.md",
    )

    if not json_path.exists():
        raise FileNotFoundError(f"Ingest artifact not found: {json_path}")

    if not force and out_json_path.exists() and out_md_path.exists():
        logger.info(f"  [skip] {job_id} already translated")
        return True

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    orig_lang = data.get("original_language", "auto")

    if orig_lang == target_lang:
        logger.info(f"  [skip] {job_id} already in target language '{orig_lang}'")
        data_manager.write_json_artifact(
            source=source,
            job_id=job_id,
            node_name="translate",
            stage="proposed",
            filename="state.json",
            data=data,
        )
        md_content = data_manager.read_text_path(md_path) if md_path.exists() else ""
        data_manager.write_text_artifact(
            source=source,
            job_id=job_id,
            node_name="translate",
            stage="proposed",
            filename="content.md",
            content=md_content,
        )
        return True

    logger.info(f"  [translate] {job_id}: '{orig_lang}' -> '{target_lang}'")

    translated_data = adapter.translate_fields(
        data,
        fields=P_FIELDS_TO_TRANSLATE,
        target_lang=target_lang,
        source_lang=orig_lang,
    )
    translated_data["original_language"] = target_lang

    md_content = data_manager.read_text_path(md_path) if md_path.exists() else ""
    translated_md = adapter.translate_text(
        md_content, target_lang=target_lang, source_lang=orig_lang
    )

    data_manager.write_json_artifact(
        source=source,
        job_id=job_id,
        node_name="translate",
        stage="proposed",
        filename="state.json",
        data=translated_data,
    )
    data_manager.write_text_artifact(
        source=source,
        job_id=job_id,
        node_name="translate",
        stage="proposed",
        filename="content.md",
        content=translated_md,
    )
    logger.info(f"  [done] {job_id} translated successfully")
    return True


def main(argv: list[str] | None = None) -> int:
    """Run the translation CLI over canonical ingest artifacts.

    Args:
        argv: Optional command-line arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description="Deterministic Translation Pipeline")
    parser.add_argument(
        "--provider",
        default="google",
        choices=list(PROVIDERS.keys()),
        help="Translation engine to use.",
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Job portal source folder to scan (e.g. 'tuberlin', 'stepstone').",
    )
    parser.add_argument(
        "--target_lang",
        "--target-lang",
        dest="target_lang",
        default="en",
        help="Target language (e.g. 'en').",
    )
    parser.add_argument(
        "--data_dir", default="data/jobs", help="Base directory for canonical job data."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-translation even if translated files exist.",
    )
    args = parser.parse_args(argv or sys.argv[1:])

    # Configure logging
    os.makedirs("logs", exist_ok=True)
    import datetime

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    configure_logging(log_file=f"translator_{args.source}_{timestamp}.log")

    adapter = PROVIDERS[args.provider]
    data_manager = DataManager(args.data_dir)
    source_path = data_manager.source_root(args.source)

    if not source_path.exists():
        logger.error(f"Source path {source_path} does not exist.")
        return 1

    logger.info(f"{LogTag.FAST} Scanning {source_path} for jobs to translate...")
    for job_dir in os.listdir(source_path):
        job_path = source_path / job_dir
        if not job_path.is_dir():
            continue

        json_path = data_manager.artifact_path(
            source=args.source,
            job_id=job_dir,
            node_name="ingest",
            stage="proposed",
            filename="state.json",
        )
        if not json_path.exists():
            continue

        try:
            translate_single_job(
                data_manager,
                adapter,
                args.source,
                job_dir,
                target_lang=args.target_lang,
                force=args.force,
            )
        except Exception as e:
            logger.error(f"  [error] Failed to translate {job_dir}: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
