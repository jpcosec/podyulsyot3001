"""Shared utilities for CLI commands."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)

DEFAULT_PROFILE_PATH = "data/reference_data/profile/base_profile/profile_base_data.json"


def load_json(path: str | None) -> Any:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_pipeline_input(
    *,
    profile_evidence_path: str | None,
    requirements_path: str | None,
) -> dict[str, Any]:
    initial_input: dict[str, Any] = {}
    if profile_evidence_path:
        initial_input["profile_evidence"] = load_json(profile_evidence_path)
    if requirements_path:
        initial_input["requirements"] = load_json(requirements_path)
    return initial_input


def translate_jobs(
    jobs: list[tuple[str, str]], *, force: bool = False
) -> list[tuple[str, str]]:
    from src.core import DataManager
    from src.core.tools.translator.main import translate_single_job, PROVIDERS

    data_manager = DataManager()
    adapter = PROVIDERS["google"]
    ready: list[tuple[str, str]] = []

    for source, job_id in jobs:
        try:
            translate_single_job(data_manager, adapter, source, job_id, force=force)
            ready.append((source, job_id))
        except Exception as exc:
            logger.error(
                "%s Translation failed for %s/%s — skipping: %s",
                LogTag.FAIL,
                source,
                job_id,
                exc,
            )

    return ready


def parse_job_selector(selector: str, sources: list[str]) -> tuple[str, str]:
    if ":" in selector:
        source, job_id = selector.split(":", 1)
        return source, job_id
    if len(sources) == 1:
        return sources[0], selector
    raise ValueError(
        f"Ambiguous job selector '{selector}'. Use source:job_id when multiple sources are provided."
    )


def read_jobs_from_stdin(sources: list[str]) -> list[tuple[str, str]]:
    import sys

    jobs: list[tuple[str, str]] = []
    for line in sys.stdin.read().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "\t" in stripped:
            source, job_id = stripped.split("\t", 1)
            jobs.append((source, job_id))
        else:
            jobs.append(parse_job_selector(stripped, sources))
    return jobs


def newest_jobs_for_sources(
    data_manager: Any, sources: list[str], limit: int | None
) -> list[tuple[str, str]]:
    from src.core import DataManager

    jobs: list[tuple[str, str, float]] = []
    for source in sources:
        root = data_manager.source_root(source)
        if not root.exists():
            continue
        source_jobs: list[tuple[str, str, float]] = []
        for job_dir in root.iterdir():
            if not job_dir.is_dir() or not data_manager.has_ingested_job(
                source, job_dir.name
            ):
                continue
            source_jobs.append((source, job_dir.name, job_dir.stat().st_mtime))
        source_jobs.sort(key=lambda item: item[2], reverse=True)
        jobs.extend(source_jobs[:limit] if limit else source_jobs)
    jobs.sort(key=lambda item: item[2], reverse=True)
    return [(source, job_id) for source, job_id, _ in jobs]
