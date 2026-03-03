#!/usr/bin/env python3
"""Unified CLI for the PhD application data pipeline.

Thin argparse dispatcher that routes commands to step registry.
All business logic lives in src/steps/*.py.

Command structure:
  pipeline job <id> <verb> [--force] [step-specific options]
  pipeline jobs [--expiring <days>] [--expired] [--keyword <word>] [--category <cat>]
                [--filter-by-keyword <word>] [--filter-by-property <key=value>]
  pipeline run-marked [--tags <t1,t2>] [--mode next|all]
  pipeline {ingest-url|ingest-listing|archive|index|backup}
"""

from __future__ import annotations

import argparse
import csv
import importlib
import inspect
import json
import logging
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

# Ensure src is importable when run as script
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.steps import STEPS, StepResult
from src.utils.state import PIPELINE_ROOT, JobState

logger = logging.getLogger(__name__)


def main() -> int:
    """Parse CLI args and dispatch to appropriate handler."""
    parser = _build_parser()
    args = parser.parse_args()

    try:
        if args.command == "job":
            return _handle_job(args)
        elif args.command == "jobs":
            return _handle_jobs(args)
        elif args.command == "ingest-url":
            return _handle_ingest_url(args)
        elif args.command == "ingest-listing":
            return _handle_ingest_listing(args)
        elif args.command == "archive":
            return _handle_archive(args)
        elif args.command == "run-marked":
            return _handle_run_marked(args)
        elif args.command == "index":
            return _handle_index(args)
        elif args.command == "backup":
            return _handle_backup(args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        logger.exception(f"Unhandled error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    """Build the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="pipeline",
        description="PhD application data pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pipeline job 201084 ingest
  pipeline job 201084 match
  pipeline job 201084 render --via docx --docx-template modern
  pipeline job 201084 run
  pipeline job 201084 run --resume
  pipeline job 201084 status
  pipeline jobs
  pipeline jobs --expiring 7
  pipeline jobs --keyword bioprocess
  pipeline jobs --filter-by-property category="Student assistant"
  pipeline run-marked --tags continue,yes --mode next
  pipeline ingest-url <url>
  pipeline archive 201084
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Job commands: job <id> <verb>
    job_parser = subparsers.add_parser(
        "job",
        help="Execute step or query for a specific job",
    )
    job_parser.add_argument("job_id", help="Job ID (e.g., 201084)")
    job_parser.add_argument(
        "verb",
        choices=[
            "ingest",
            "match",
            "match-approve",
            "motivate",
            "tailor-cv",
            "draft-email",
            "render",
            "package",
            "status",
            "run",
            "graph-status",
            "regenerate",
            "validate-ats",
            "template-test",
        ],
        help="Action to perform",
    )
    job_parser.add_argument(
        "--force", action="store_true", help="Re-run step even if complete"
    )
    job_parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume graph run after review interrupt",
    )
    job_parser.add_argument(
        "--source", default="tu_berlin", help="Job source (default: tu_berlin)"
    )

    # Step-specific options
    job_parser.add_argument(
        "--via",
        default="docx",
        choices=["docx", "latex"],
        help="Rendering engine (render step)",
    )
    job_parser.add_argument(
        "--docx-template",
        default="modern",
        choices=["classic", "modern", "harvard", "executive"],
        help="DOCX template style (render step)",
    )
    job_parser.add_argument(
        "--language",
        default="english",
        choices=["english", "german", "spanish"],
        help="Language for rendering (render step)",
    )
    job_parser.add_argument(
        "--ats-target",
        default="pdf",
        choices=["pdf", "docx"],
        help="Format to validate (validate-ats step)",
    )
    job_parser.add_argument(
        "--target",
        default="pdf",
        choices=["pdf", "docx"],
        help="Template test target (template-test step)",
    )
    job_parser.add_argument(
        "--require-perfect",
        action="store_true",
        help="Require 100%% match for template test",
    )
    job_parser.add_argument(
        "regenerate_step",
        nargs="?",
        help="Step name to regenerate (for regenerate verb)",
    )

    # Job queries: jobs [--expiring|--expired|--keyword|--category]
    jobs_parser = subparsers.add_parser(
        "jobs",
        help="List and filter open jobs",
    )
    jobs_parser.add_argument(
        "--expiring",
        type=int,
        metavar="DAYS",
        help="Show jobs with deadline within N days",
    )
    jobs_parser.add_argument(
        "--expired",
        action="store_true",
        help="Show jobs past deadline",
    )
    jobs_parser.add_argument(
        "--keyword",
        metavar="WORD",
        help="Filter by matching keyword",
    )
    jobs_parser.add_argument(
        "--filter-by-keyword",
        "--filterbykeyword",
        dest="filter_by_keyword",
        metavar="WORD",
        help="Filter by matching keyword (alias)",
    )
    jobs_parser.add_argument(
        "--category",
        metavar="CAT",
        help="Filter by job category",
    )
    jobs_parser.add_argument(
        "--filter-by-property",
        "--filterbyproperty",
        dest="filter_by_property",
        metavar="KEY=VALUE",
        help="Filter by job metadata property (e.g. category=Student assistant)",
    )
    jobs_parser.add_argument(
        "--source", default="tu_berlin", help="Job source (default: tu_berlin)"
    )

    run_marked_parser = subparsers.add_parser(
        "run-marked",
        help="Run pipeline steps for jobs marked with frontmatter tags",
    )
    run_marked_parser.add_argument(
        "--tags",
        default="continue,yes",
        help="Comma-separated marker tags to include (default: continue,yes)",
    )
    run_marked_parser.add_argument(
        "--mode",
        choices=["next", "all"],
        default="next",
        help="Run only next pending step or all pending steps (default: next)",
    )
    run_marked_parser.add_argument(
        "--force",
        action="store_true",
        help="Force step execution when applicable",
    )
    run_marked_parser.add_argument(
        "--source", default="tu_berlin", help="Job source (default: tu_berlin)"
    )

    # Ingestion helpers
    ingest_url_parser = subparsers.add_parser(
        "ingest-url",
        help="Fetch and ingest specific job URLs",
    )
    ingest_url_parser.add_argument("urls", nargs="+", help="URL(s) to ingest")
    ingest_url_parser.add_argument(
        "--source", default="tu_berlin", help="Job source (default: tu_berlin)"
    )

    ingest_listing_parser = subparsers.add_parser(
        "ingest-listing",
        help="Crawl and ingest from a listing page",
    )
    ingest_listing_parser.add_argument(
        "url",
        help="Listing page URL to crawl",
    )
    ingest_listing_parser.add_argument(
        "--source", default="tu_berlin", help="Job source (default: tu_berlin)"
    )
    ingest_listing_parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between requests (seconds)",
    )

    # Archive commands
    archive_parser = subparsers.add_parser(
        "archive",
        help="Archive jobs",
    )
    archive_parser.add_argument(
        "job_id",
        nargs="?",
        help="Job ID to archive (omit to archive expired)",
    )
    archive_parser.add_argument(
        "--expired",
        action="store_true",
        help="Archive all expired jobs",
    )
    archive_parser.add_argument(
        "--marked",
        action="store_true",
        help="Archive jobs marked in job.md frontmatter (archive tags/properties)",
    )
    archive_parser.add_argument(
        "--source", default="tu_berlin", help="Job source (default: tu_berlin)"
    )

    # Admin commands
    subparsers.add_parser(
        "index",
        help="Rebuild job index",
    )
    subparsers.add_parser(
        "backup",
        help="Rebuild backup manifest",
    )

    return parser


def _handle_job(args: argparse.Namespace) -> int:
    """Handle job <id> <verb> commands."""
    job_id = args.job_id
    verb = args.verb
    source = args.source
    force = args.force

    try:
        state = JobState(job_id, source=source)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Status command (doesn't dispatch to step registry)
    if verb == "status":
        return _show_status(state)

    # Run command (execute all pending steps)
    if verb == "run":
        return _run_graph(
            state,
            force=force,
            resume=args.resume,
            args=args,
        )

    if verb == "graph-status":
        return _show_graph_status(state)

    # Regenerate command (re-run a specific step)
    if verb == "regenerate":
        if not args.regenerate_step:
            print(
                "Error: regenerate requires a step name",
                file=sys.stderr,
            )
            return 1
        return _regenerate_step(state, args.regenerate_step, force=True)

    # ATS validation commands (not steps in registry, special handling)
    if verb == "validate-ats":
        return _validate_ats(state, ats_target=args.ats_target, via=args.via)

    if verb == "template-test":
        return _template_test(
            state,
            via=args.via,
            docx_template=args.docx_template,
            target=args.target,
            require_perfect=args.require_perfect,
            language=args.language,
        )

    # Dispatch to step registry
    if verb not in STEPS:
        print(f"Error: unknown verb '{verb}'", file=sys.stderr)
        return 1

    return _dispatch_step(state, verb, force=force, args=args)


def _parse_property_filter(raw_filter: str) -> tuple[str, str]:
    """Parse KEY=VALUE property filter syntax."""
    if "=" not in raw_filter:
        raise ValueError("Property filter must be KEY=VALUE")

    key, value = raw_filter.split("=", maxsplit=1)
    key = key.strip()
    value = value.strip()

    if not key or not value:
        raise ValueError("Property filter must include both key and value")

    return key, value


def _property_values(job: JobState, key: str) -> list[str]:
    """Resolve a property from metadata/frontmatter as comparable strings."""
    key_norm = key.strip().lower()
    frontmatter = _parse_frontmatter(job.artifact_path("job.md"))

    if key_norm in {"tags", "tag", "labels"}:
        tags: list[str] = []
        for tag_key in ("tags", "tag", "labels"):
            tags.extend(_to_tag_list(frontmatter.get(tag_key)))
        if tags:
            return tags
        return _to_tag_list(job.metadata.get(key_norm))

    if key_norm in frontmatter and frontmatter.get(key_norm) not in (None, ""):
        value = frontmatter.get(key_norm)
    else:
        value = job.metadata.get(key_norm, "")

    if isinstance(value, list):
        return [str(v) for v in value]
    if value in (None, ""):
        return []
    return [str(value)]


def _handle_jobs(args: argparse.Namespace) -> int:
    """Handle jobs [--expiring|--expired|--keyword|--category|--filter-by-property] commands."""
    source = args.source
    keyword = args.filter_by_keyword or args.keyword

    if args.expired:
        jobs = JobState.list_expired(source=source)
        print(f"Found {len(jobs)} expired job(s):")
    elif args.expiring:
        jobs = JobState.list_expiring(args.expiring, source=source)
        print(f"Found {len(jobs)} job(s) expiring within {args.expiring} day(s):")
    elif keyword:
        jobs = JobState.list_by_keyword(keyword, source=source)
        print(f"Found {len(jobs)} job(s) matching keyword '{keyword}':")
    elif args.filter_by_property:
        try:
            key, value = _parse_property_filter(args.filter_by_property)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        all_jobs = JobState.list_open_jobs(source=source)
        needle = value.lower()
        jobs = [
            job
            for job in all_jobs
            if any(
                needle in candidate.lower() for candidate in _property_values(job, key)
            )
        ]
        print(f"Found {len(jobs)} job(s) where {key} contains '{value}':")
    elif args.category:
        # Filter by posting category from job metadata/frontmatter.
        all_jobs = JobState.list_open_jobs(source=source)
        needle = args.category.strip().lower()
        jobs = [
            job
            for job in all_jobs
            if any(
                needle in candidate.lower()
                for candidate in _property_values(job, "category")
            )
        ]
        print(f"Found {len(jobs)} job(s) in category '{args.category}':")
    else:
        jobs = JobState.list_open_jobs(source=source)
        print(f"Found {len(jobs)} open job(s):")

    # Format output
    for job in jobs:
        deadline_str = job.deadline.isoformat() if job.deadline else "unknown"
        title = job.metadata.get("title", "Unknown")
        print(f"  {job.job_id:6s}  {deadline_str}  {title}")

    return 0


def _parse_marker_tags(raw_tags: str) -> set[str]:
    """Parse comma-separated marker tags."""
    tags = {part.strip().lower().lstrip("#") for part in raw_tags.split(",")}
    tags.discard("")
    return tags


def _handle_run_marked(args: argparse.Namespace) -> int:
    """Handle run-marked command."""
    tags = _parse_marker_tags(args.tags)
    if not tags:
        print("Error: --tags must include at least one tag", file=sys.stderr)
        return 1

    marked_jobs = _list_marked_for_continue(args.source, tags)
    if not marked_jobs:
        print(f"No jobs found with marker tags: {', '.join(sorted(tags))}")
        return 0

    print(
        f"Running mode='{args.mode}' for {len(marked_jobs)} marked job(s) "
        + f"with tags: {', '.join(sorted(tags))}"
    )

    success = 0
    failed = 0
    for job in marked_jobs:
        print(f"\n[{job.job_id}]")
        if args.mode == "all":
            rc = _run_graph(
                job,
                force=args.force,
                resume=False,
                args=_default_dispatch_args(),
            )
        else:
            rc = _run_next_pending(job, force=args.force)

        if rc == 0:
            success += 1
        else:
            failed += 1

    print(
        f"\nCompleted run-marked: {success} succeeded, {failed} failed, "
        + f"total {len(marked_jobs)}"
    )
    return 0 if failed == 0 else 1


def _handle_ingest_url(args: argparse.Namespace) -> int:
    """Handle ingest-url command."""
    try:
        from src.scraper.scrape_single_url import run_for_url
    except ImportError:
        print("Error: scraper module not found", file=sys.stderr)
        return 1

    print(f"Ingesting {len(args.urls)} URL(s)...")
    try:
        pipeline_root = REPO_ROOT / "data" / "pipelined_data"
        failed_urls: list[str] = []
        for url in args.urls:
            try:
                result = run_for_url(
                    url=url,
                    source=args.source,
                    pipeline_root=pipeline_root,
                )
                print(f"  [ok] {result['job_id']} <- {url}")
            except Exception as e:
                failed_urls.append(url)
                print(f"  [failed] {url}: {e}")
        return 0 if not failed_urls else 1
    except Exception as e:
        logger.exception(f"Failed to ingest URLs: {e}")
        return 1


def _handle_ingest_listing(args: argparse.Namespace) -> int:
    """Handle ingest-listing command."""
    try:
        from src.scraper.fetch_listing import crawl_listing
    except ImportError:
        print("Error: scraper module not found", file=sys.stderr)
        return 1

    print(f"Crawling listing: {args.url}")
    try:
        crawl_listing(
            listing_url=args.url,
            source=args.source,
            pipeline_root=REPO_ROOT / "data" / "pipelined_data",
            delay=args.delay,
        )
        return 0
    except Exception as e:
        logger.exception(f"Failed to crawl listing: {e}")
        return 1


def _handle_archive(args: argparse.Namespace) -> int:
    """Handle archive command."""
    source = args.source

    if args.marked:
        marked_jobs = _list_marked_for_archive(source)
        if not marked_jobs:
            print("No marked jobs found")
            return 0

        print(f"Archiving {len(marked_jobs)} marked job(s)...")
        archived = _archive_jobs(marked_jobs)
        _rebuild_job_index(source)
        print(f"Archived {archived}/{len(marked_jobs)} marked job(s)")
        return 0 if archived == len(marked_jobs) else 1

    if args.expired or (not args.job_id):
        # Archive all expired jobs
        expired_jobs = JobState.list_expired(source=source)
        if not expired_jobs:
            print("No expired jobs found")
            return 0
        print(f"Archiving {len(expired_jobs)} expired job(s)...")
        archived = _archive_jobs(expired_jobs)
        _rebuild_job_index(source)
        return 0 if archived == len(expired_jobs) else 1

    # Archive specific job
    if not args.job_id:
        print("Error: provide job_id or use --expired", file=sys.stderr)
        return 1

    try:
        state = JobState(args.job_id, source=source)
        state.archive()
        print(f"Archived job: {args.job_id}")
        _rebuild_job_index(source)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _handle_index(args: argparse.Namespace) -> int:
    """Handle index command."""
    print("Rebuilding job index...")
    _rebuild_job_index("tu_berlin")
    print("Index rebuild complete")
    return 0


def _archive_jobs(jobs: list[JobState]) -> int:
    """Archive jobs and return archived count."""
    archived_count = 0
    for job in jobs:
        try:
            job.archive()
            archived_count += 1
            print(f"  Archived: {job.job_id}")
        except Exception as e:
            logger.warning(f"Failed to archive {job.job_id}: {e}")
    return archived_count


def _parse_frontmatter(job_md_path: Path) -> dict[str, object]:
    """Parse simple YAML frontmatter from job.md without external deps."""
    if not job_md_path.exists():
        return {}

    content = job_md_path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        return {}

    end_idx = content.find("\n---", 4)
    if end_idx == -1:
        return {}

    frontmatter = content[4:end_idx]
    data: dict[str, object] = {}
    current_key: str | None = None

    for raw_line in frontmatter.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue

        key_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if key_match:
            key = key_match.group(1).strip().lower()
            value = key_match.group(2).strip()
            if value:
                data[key] = value.strip("\"'")
            else:
                data[key] = []
            current_key = key
            continue

        if current_key and line.lstrip().startswith("- "):
            item = line.lstrip()[2:].strip().strip("\"'")
            existing = data.get(current_key)
            if isinstance(existing, list):
                existing.append(item)
            else:
                data[current_key] = [item]

    return data


def _to_tag_list(value: object) -> list[str]:
    """Normalize frontmatter tag-like field into list of lowercase tags."""
    if isinstance(value, list):
        raw_tags = [str(v) for v in value]
    elif isinstance(value, str):
        v = value.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1]
            raw_tags = [p.strip() for p in inner.split(",") if p.strip()]
        elif "," in v:
            raw_tags = [p.strip() for p in v.split(",") if p.strip()]
        elif v:
            raw_tags = [v]
        else:
            raw_tags = []
    else:
        raw_tags = []

    return [tag.lower().lstrip("#") for tag in raw_tags]


def _is_truthy(value: object) -> bool:
    """Interpret common truthy frontmatter strings."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _is_archive_marked(frontmatter: dict[str, object]) -> bool:
    """Check whether frontmatter indicates the job should be archived."""
    for key in ("archive", "archived", "to_archive", "to-archive"):
        if _is_truthy(frontmatter.get(key)):
            return True

    status = str(frontmatter.get("status", "")).strip().lower()
    if status in {"archive", "archived", "to archive", "to-archive"}:
        return True

    tags = []
    for key in ("tags", "tag", "labels"):
        tags.extend(_to_tag_list(frontmatter.get(key)))

    archive_tags = {
        "archive",
        "archived",
        "to-archive",
        "to_archive",
        "drop",
        "reject",
        "rejected",
    }
    return any(tag in archive_tags for tag in tags)


def _list_marked_for_archive(source: str) -> list[JobState]:
    """List open jobs marked for archive in job.md frontmatter."""
    marked: list[JobState] = []
    for job in JobState.list_open_jobs(source=source):
        frontmatter = _parse_frontmatter(job.artifact_path("job.md"))
        if _is_archive_marked(frontmatter):
            marked.append(job)
    return marked


def _is_continue_marked(frontmatter: dict[str, object], marker_tags: set[str]) -> bool:
    """Check whether frontmatter indicates the job should continue in pipeline."""
    status = str(frontmatter.get("status", "")).strip().lower()
    if status in marker_tags:
        return True

    for key in marker_tags:
        if _is_truthy(frontmatter.get(key)):
            return True

    tags = []
    for key in ("tags", "tag", "labels"):
        tags.extend(_to_tag_list(frontmatter.get(key)))
    return any(tag in marker_tags for tag in tags)


def _list_marked_for_continue(source: str, marker_tags: set[str]) -> list[JobState]:
    """List open jobs marked with continue tags/properties in frontmatter."""
    marked: list[JobState] = []
    for job in JobState.list_open_jobs(source=source):
        frontmatter = _parse_frontmatter(job.artifact_path("job.md"))
        if _is_continue_marked(frontmatter, marker_tags):
            marked.append(job)
    return marked


def _load_job_record(job_dir: Path, pipeline_status: str) -> dict[str, str]:
    """Load a normalized row for index CSVs from a job directory."""
    metadata: dict[str, object] = {}
    extracted_path = job_dir / "raw" / "extracted.json"
    if extracted_path.exists():
        try:
            metadata = json.loads(extracted_path.read_text(encoding="utf-8"))
        except Exception:
            metadata = {}

    frontmatter = _parse_frontmatter(job_dir / "job.md")

    def pick(key: str, default: str = "") -> str:
        meta_val = metadata.get(key)
        if meta_val not in (None, ""):
            return str(meta_val)
        fm_val = frontmatter.get(key)
        if fm_val not in (None, ""):
            return str(fm_val)
        return default

    facts = "; ".join(
        [
            f"Status: {pipeline_status}",
            f"Category: {pick('category', 'Unknown')}",
            f"Duration: {pick('duration', 'Unknown')}",
            f"Salary: {pick('salary', 'Unknown')}",
        ]
    )

    tags: list[str] = []
    for key in ("tags", "tag", "labels"):
        tags.extend(_to_tag_list(frontmatter.get(key)))
    tags = sorted(set(tags))
    tags_str = ",".join(tags)

    if tags_str:
        facts = f"{facts}; Tags: {tags_str}"

    return {
        "job_id": job_dir.name,
        "pipeline_status": pipeline_status,
        "metadata_status": pick("status", ""),
        "url": pick("url", ""),
        "title": pick("title", "Unknown"),
        "deadline": pick("deadline", "unknown"),
        "category": pick("category", ""),
        "reference_number": pick("reference_number", ""),
        "contact_email": pick("contact_email", ""),
        "tags": tags_str,
        "facts": facts,
        "path": str(job_dir),
    }


def _rebuild_job_index(source: str) -> None:
    """Rebuild summary.csv and summary_detailed.csv for a source."""
    source_root = PIPELINE_ROOT / source
    source_root.mkdir(parents=True, exist_ok=True)
    archive_root = source_root / JobState.ARCHIVE_DIR

    records: list[dict[str, str]] = []

    for child in sorted(source_root.iterdir(), key=lambda p: p.name):
        if (
            child.is_dir()
            and child.name.isdigit()
            and child.name != JobState.ARCHIVE_DIR
        ):
            records.append(_load_job_record(child, "open"))

    if archive_root.exists():
        for child in sorted(archive_root.iterdir(), key=lambda p: p.name):
            if child.is_dir() and child.name.isdigit():
                records.append(_load_job_record(child, "archived"))

    records.sort(key=lambda r: int(r["job_id"]))

    summary_csv = source_root / "summary.csv"
    with open(summary_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["URL", "Title", "Deadline", "Facts"])
        writer.writeheader()
        for row in records:
            writer.writerow(
                {
                    "URL": row["url"],
                    "Title": row["title"],
                    "Deadline": row["deadline"],
                    "Facts": row["facts"],
                }
            )

    detailed_csv = source_root / "summary_detailed.csv"
    with open(detailed_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "JobID",
                "PipelineStatus",
                "MetadataStatus",
                "Category",
                "Deadline",
                "Title",
                "URL",
                "ReferenceNumber",
                "ContactEmail",
                "Tags",
                "Path",
            ],
        )
        writer.writeheader()
        for row in records:
            writer.writerow(
                {
                    "JobID": row["job_id"],
                    "PipelineStatus": row["pipeline_status"],
                    "MetadataStatus": row["metadata_status"],
                    "Category": row["category"],
                    "Deadline": row["deadline"],
                    "Title": row["title"],
                    "URL": row["url"],
                    "ReferenceNumber": row["reference_number"],
                    "ContactEmail": row["contact_email"],
                    "Tags": row["tags"],
                    "Path": row["path"],
                }
            )


def _handle_backup(args: argparse.Namespace) -> int:
    """Handle backup command."""
    print("Rebuilding backup manifest...")
    try:
        import subprocess

        subprocess.run(
            [sys.executable, "src/utils/build_backup_compendium.py"],
            cwd=REPO_ROOT,
            check=True,
        )
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


# ── Step dispatching ──


def _dispatch_step(
    state: JobState,
    verb: str,
    *,
    force: bool = False,
    args: argparse.Namespace | None = None,
) -> int:
    """Dispatch a verb to its step function from the registry."""
    if verb not in STEPS:
        print(f"Error: unknown step verb '{verb}'", file=sys.stderr)
        return 1
    module_path, func_name = STEPS[verb]

    try:
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
    except (ImportError, AttributeError) as e:
        print(f"Error loading step {verb}: {e}", file=sys.stderr)
        return 1

    # Build kwargs for step function
    kwargs: dict[str, Any] = {}
    if "force" in inspect.signature(func).parameters:
        kwargs["force"] = force

    # Add step-specific options from argparse
    if args:
        if verb == "render":
            kwargs.update(
                {
                    "via": args.via,
                    "docx_template": args.docx_template,
                    "language": args.language,
                }
            )

    # Call step function
    try:
        result: StepResult = func(state, **kwargs)
        _print_result(result)
        return 0 if result.status == "ok" else 1
    except Exception as e:
        logger.exception(f"Step {verb} failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _run_graph(
    state: JobState,
    *,
    force: bool = False,
    resume: bool = False,
    args: argparse.Namespace | None = None,
) -> int:
    """Run graph-coordinated pipeline flow with review interrupt/resume."""
    from src.graph.pipeline import run_graph_pipeline

    run_args = args or _default_dispatch_args()
    result = run_graph_pipeline(
        state,
        force=force,
        resume=resume,
        via=run_args.via,
        docx_template=run_args.docx_template,
        language=run_args.language,
    )

    for step_name, step_result in result.step_results:
        print(f"[{step_name.replace('-', '_')}]")
        _print_result(step_result)
        print()

    if result.status == "interrupted":
        print(result.message)
        print(f"Resume with: pipeline job {state.job_id} run --resume")
        return 0

    if result.status == "error":
        print(f"Error: {result.message}", file=sys.stderr)
        return 1

    print(result.message)
    return 0


def _show_graph_status(state: JobState) -> int:
    """Inspect current LangGraph checkpoint state for a job."""
    from src.graph.pipeline import build_graph

    try:
        from langgraph.checkpoint.sqlite import SqliteSaver  # type: ignore[import-not-found]
    except ImportError:
        print(
            "Error: LangGraph runtime unavailable. Install langgraph dependencies.",
            file=sys.stderr,
        )
        return 1

    db_path = state.job_dir / ".graph" / "checkpoints.db"
    if not db_path.exists():
        print(
            f"No graph state for job {state.job_id}. Run 'pipeline job {state.job_id} run' first."
        )
        return 1

    config = {"configurable": {"thread_id": f"{state.source}/{state.job_id}"}}
    with SqliteSaver.from_conn_string(f"sqlite:///{db_path}") as checkpointer:
        graph = build_graph().compile(checkpointer=checkpointer)
        snapshot = graph.get_state(config)

    values = snapshot.values if snapshot else {}
    next_nodes = list(snapshot.next) if snapshot and snapshot.next else []
    executed = values.get("step_results", [])

    print(f"Job: {state.job_id}")
    print(f"Checkpoint DB: {db_path}")
    print(f"Executed nodes: {len(executed)}")

    if next_nodes:
        print(f"Next node(s): {', '.join(next_nodes)}")
    else:
        print("Next node(s): none")

    if "review_gate" in next_nodes:
        print("Review gate pending. Resume with:")
        print(f"  pipeline job {state.job_id} run --resume")
    elif not next_nodes:
        print("Graph appears complete for current thread.")

    return 0


def _run_all_pending(state: JobState, *, force: bool = False) -> int:
    """Run all pending steps in order."""
    first_verb = _next_workflow_verb(state)
    if not first_verb:
        print(f"Job {state.job_id}: all steps complete")
        return 0

    print(f"Job {state.job_id}: running workflow from '{first_verb}'")

    while True:
        verb = _next_workflow_verb(state)
        if not verb:
            break
        print(f"[{verb.replace('-', '_')}]")
        if _dispatch_step(state, verb, force=force, args=_default_dispatch_args()) != 0:
            print(f"Error: step {verb} failed", file=sys.stderr)
            return 1
        print()

    return 0


def _next_workflow_verb(state: JobState) -> str | None:
    """Return the next verb in the canonical workflow, including match-approve."""
    if not state.step_complete("ingestion"):
        return "ingest"

    has_proposal = state.artifact_path("planning/match_proposal.md").exists()
    has_keywords = state.artifact_path("planning/keywords.json").exists()
    if not (has_proposal and has_keywords):
        return "match"

    has_reviewed_mapping = state.artifact_path(
        "planning/reviewed_mapping.json"
    ).exists()
    if not has_reviewed_mapping:
        return "match-approve"

    if not state.step_complete("motivation"):
        return "motivate"
    if not state.step_complete("cv_tailoring"):
        return "tailor-cv"
    if not state.step_complete("email_draft"):
        return "draft-email"
    if not state.step_complete("rendering"):
        return "render"
    if not state.step_complete("packaging"):
        return "package"
    return None


def _run_next_pending(state: JobState, *, force: bool = False) -> int:
    """Run only the next workflow step for a job."""
    verb = _next_workflow_verb(state)
    if not verb:
        print(f"Job {state.job_id}: all steps complete")
        return 0

    print(f"Job {state.job_id}: next step '{verb}'")
    return _dispatch_step(state, verb, force=force, args=_default_dispatch_args())


def _default_dispatch_args() -> argparse.Namespace:
    """Default argparse namespace for step dispatch outside CLI parser contexts."""
    return argparse.Namespace(
        via="docx",
        docx_template="modern",
        language="english",
        ats_target="pdf",
        target="pdf",
        require_perfect=False,
    )


def _regenerate_step(state: JobState, step_name: str, *, force: bool = True) -> int:
    """Re-run a specific step (force=True by default)."""
    verb = step_name.replace("_", "-")  # Convert internal name to verb

    if verb not in STEPS:
        print(f"Error: step '{step_name}' not in registry", file=sys.stderr)
        return 1

    print(f"Regenerating step: {step_name}")

    return _dispatch_step(state, verb, force=force, args=_default_dispatch_args())


def _show_status(state: JobState) -> int:
    """Show step completion status and comments for a job."""
    print(f"Job: {state.job_id}")
    print(f"Status: {state.status}")
    if state.deadline:
        print(f"Deadline: {state.deadline.isoformat()}")
    print()

    print("Step completion:")
    for step in state.STEP_ORDER:
        is_complete = state.step_complete(step)
        marker = "✓" if is_complete else " "
        print(f"  [{marker}] {step}")

    pending = state.pending_steps()
    if pending:
        print()
        print(f"Pending steps: {', '.join(pending)}")
        next_step = pending[0]
        print(f"Next: pipeline job {state.job_id} {next_step.replace('_', '-')}")

    return 0


def _validate_ats(
    state: JobState, *, ats_target: str = "pdf", via: str = "docx"
) -> int:
    """Validate rendered CV against job description using ATS system."""
    try:
        from src.steps.rendering import validate_ats
    except ImportError:
        print("Error: rendering module not found", file=sys.stderr)
        return 1

    try:
        report = validate_ats(state, ats_target=ats_target, via=via)
        print(f"ATS Validation Report ({ats_target}):")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _template_test(
    state: JobState,
    *,
    via: str = "docx",
    docx_template: str = "modern",
    target: str = "pdf",
    require_perfect: bool = False,
    language: str = "english",
) -> int:
    """Run deterministic parity check on rendered CV."""
    try:
        from src.steps.rendering import template_test
    except ImportError:
        print("Error: rendering module not found", file=sys.stderr)
        return 1

    try:
        report = template_test(
            state,
            via=via,
            docx_template=docx_template,
            target=target,
            require_perfect=require_perfect,
            language=language,
        )
        print(f"Template Test Report ({target}):")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _print_result(result: StepResult) -> None:
    """Pretty-print a StepResult."""
    status_marker = {
        "ok": "✓",
        "skipped": "⊘",
        "error": "✗",
    }.get(result.status, "?")

    print(f"[{status_marker}] {result.message}")
    if result.produced:
        print(f"    Produced: {', '.join(result.produced)}")
    if result.comments_found:
        print(f"    Comments found: {result.comments_found}")


if __name__ == "__main__":
    sys.exit(main())
