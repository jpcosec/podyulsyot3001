"""Path helpers for schema-v0 render jobs."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from src.core.data_manager import DataManager


class JobRenderPaths(NamedTuple):
    """Resolved job-local paths used by the render coordinator."""

    job_root: Path
    generate_dir: Path
    render_dir: Path
    build_dir: Path


def job_render_paths(source: str, job_id: str, document_type: str) -> JobRenderPaths:
    """Return schema-v0 job paths for render input and output resolution."""

    del document_type
    job_root = Path("data/jobs") / source / job_id
    generate_dir = job_root / "nodes" / "generate_documents" / "proposed"
    render_dir = job_root / "nodes" / "render" / "proposed"
    build_dir = job_root / "nodes" / "render" / "build"
    data_manager = DataManager()
    data_manager.ensure_dir(render_dir)
    data_manager.ensure_dir(build_dir)
    return JobRenderPaths(job_root, generate_dir, render_dir, build_dir)


def build_output_path(output_path: str | Path | None, default_name: str) -> Path:
    """Resolve an explicit output path or build a default one."""

    if output_path is None:
        return Path(default_name).resolve()
    return Path(output_path).resolve()
