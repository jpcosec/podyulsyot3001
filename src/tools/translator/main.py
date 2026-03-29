"""CLI entry point for the translation pipeline.

Scans ``data/source/<source>/`` for job folders that contain
``extracted_data.json`` and ``content.md``, translates all fields listed in
``P_FIELDS_TO_TRANSLATE`` and the Markdown body, and writes
``extracted_data_en.json`` and ``content_en.md`` to the same folder.
Already-translated jobs are skipped unless ``--force`` is set.
"""

import argparse
import logging
import os
import json
import sys
from pathlib import Path
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
        "--data_dir", default="data/source", help="Base directory for scraped outputs."
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
    source_path = Path(args.data_dir) / args.source

    if not source_path.exists():
        logger.error(f"Source path {source_path} does not exist.")
        return

    logger.info(f"[*] Scanning {source_path} for jobs to translate...")
    for job_dir in os.listdir(source_path):
        job_path = source_path / job_dir
        if not job_path.is_dir():
            continue

        json_path = job_path / "extracted_data.json"
        md_path = job_path / "content.md"
        out_json_path = job_path / "extracted_data_en.json"
        out_md_path = job_path / "content_en.md"

        if not json_path.exists() or not md_path.exists():
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
                # Create exact copies if they are already in the target language
                out_json_path.write_text(
                    json_path.read_text(encoding="utf-8"), encoding="utf-8"
                )
                out_md_path.write_text(
                    md_path.read_text(encoding="utf-8"), encoding="utf-8"
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
            md_content = md_path.read_text(encoding="utf-8")
            translated_md = adapter.translate_text(
                md_content, target_lang=args.target_lang, source_lang=orig_lang
            )

            # 3. Save
            with open(out_json_path, "w", encoding="utf-8") as f:
                json.dump(translated_data, f, indent=2, ensure_ascii=False)

            out_md_path.write_text(translated_md, encoding="utf-8")
            logger.info(f"  [✅] {job_dir} successfully translated.")

        except Exception as e:
            logger.error(f"  [❌] Failed to translate {job_dir}: {str(e)}")


if __name__ == "__main__":
    main()
