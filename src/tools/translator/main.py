"""CLI entry point for the translation pipeline.

Scans canonical ingested jobs under ``data/jobs/<source>/<job_id>/`` and reads
raw input artifacts from ``nodes/ingest/proposed/``. Translated artifacts are
written to ``nodes/translate/proposed/``.
"""

import argparse
import logging
import os
import json
import sys
from pathlib import Path

from src.core.data_manager import DataManager
from src.tools.translator.providers.google.adapter import GoogleTranslatorAdapter

logger = logging.getLogger(__name__)

PROVIDERS = {"google": GoogleTranslatorAdapter()}

P_FIELDS_TO_TRANSLATE = [
    "job_title",
    "company_name",
    "location",
    "employment_type",
    "posted_date",
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


def main(argv: list[str] | None = None) -> None:
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
        "--target_lang", default="en", help="Target language (e.g. 'en')."
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
    log_filename = f"logs/translator_{args.source}_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] Translator: %(message)s",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )

    adapter = PROVIDERS[args.provider]
    data_manager = DataManager(args.data_dir)
    source_path = data_manager.source_root(args.source)

    if not source_path.exists():
        logger.error(f"Source path {source_path} does not exist.")
        return

    logger.info(f"[*] Scanning {source_path} for jobs to translate...")
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
        md_path = data_manager.artifact_path(
            source=args.source,
            job_id=job_dir,
            node_name="ingest",
            stage="proposed",
            filename="content.md",
        )
        out_json_path = data_manager.artifact_path(
            source=args.source,
            job_id=job_dir,
            node_name="translate",
            stage="proposed",
            filename="state.json",
        )
        out_md_path = data_manager.artifact_path(
            source=args.source,
            job_id=job_dir,
            node_name="translate",
            stage="proposed",
            filename="content.md",
        )

        if not json_path.exists():
            continue

        if not args.force and out_json_path.exists() and out_md_path.exists():
            logger.info(f"  [⏭️] Skipping {job_dir} (Already translated)")
            continue

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            orig_lang = data.get("original_language", "auto")

            if orig_lang == args.target_lang:
                logger.info(
                    f"  [⏭️] Skipping {job_dir} (Already matches target language: '{orig_lang}')"
                )
                data_manager.write_json_artifact(
                    source=args.source,
                    job_id=job_dir,
                    node_name="translate",
                    stage="proposed",
                    filename="state.json",
                    data=data,
                )
                data_manager.write_text_artifact(
                    source=args.source,
                    job_id=job_dir,
                    node_name="translate",
                    stage="proposed",
                    filename="content.md",
                    content=md_path.read_text(encoding="utf-8")
                    if md_path.exists()
                    else "",
                )
                continue

            logger.info(
                f"  [🔄] Translating {job_dir} from '{orig_lang}' to '{args.target_lang}' using {args.provider}..."
            )

            # 1. Translate JSON Dictionary Elements
            translated_data = adapter.translate_fields(
                data,
                fields=P_FIELDS_TO_TRANSLATE,
                target_lang=args.target_lang,
                source_lang=orig_lang,
            )
            translated_data["original_language"] = args.target_lang

            # 2. Translate body markdown
            md_content = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
            translated_md = adapter.translate_text(
                md_content, target_lang=args.target_lang, source_lang=orig_lang
            )

            data_manager.write_json_artifact(
                source=args.source,
                job_id=job_dir,
                node_name="translate",
                stage="proposed",
                filename="state.json",
                data=translated_data,
            )
            data_manager.write_text_artifact(
                source=args.source,
                job_id=job_dir,
                node_name="translate",
                stage="proposed",
                filename="content.md",
                content=translated_md,
            )
            logger.info(f"  [✅] {job_dir} successfully translated.")

        except Exception as e:
            logger.error(f"  [❌] Failed to translate {job_dir}: {str(e)}")


if __name__ == "__main__":
    main()
