"""Central render coordinator."""

from __future__ import annotations

from pathlib import Path

from src.core.data_manager import DataManager
from src.core.tools.render.engines.base import ResolvedRenderConfig
from src.core.tools.render.languages.registry import get_language_bundle
from src.core.tools.render.registry import (
    get_document_adapter,
    get_engine_adapter,
    load_style_manifest,
    resolve_manifest_paths,
)
from src.core.tools.render.request import RenderRequest
from src.core.tools.render.shared.paths import build_output_path, job_render_paths


class RenderCoordinator:
    """Resolve sources, manifests, and engines for render requests."""

    def __init__(self) -> None:
        self.data_manager = DataManager()

    def render(self, request: RenderRequest) -> Path:
        """Execute a rendering request end-to-end."""

        document_adapter = get_document_adapter(request.document_type)
        style = request.style or document_adapter.default_style
        source_path, output_path, build_dir = self._resolve_paths(
            request, document_adapter
        )
        payload = document_adapter.build_payload(source_path, request)

        if payload.source_kind == "legacy_json":
            raise ValueError(
                "Legacy JSON rendering is no longer supported in schema-v0"
            )

        manifest = load_style_manifest(request.document_type, style)
        template_path, reference_doc, lua_filters, asset_roots = resolve_manifest_paths(
            manifest,
            request.engine,
        )
        metadata = get_language_bundle(request.language).metadata_for(
            request.document_type,
            style,
        )
        metadata.update(request.extra_vars)

        config = ResolvedRenderConfig(
            document_type=request.document_type,
            style=style,
            language=request.language,
            engine=request.engine,
            template_path=template_path,
            reference_doc=reference_doc,
            lua_filters=lua_filters,
            asset_roots=asset_roots,
            metadata=metadata,
            output_path=output_path,
            build_dir=build_dir,
        )
        engine_adapter = get_engine_adapter(request.engine)
        return engine_adapter.render(payload, config)

    def _resolve_paths(
        self, request: RenderRequest, document_adapter
    ) -> tuple[Path, Path, Path]:
        """Resolve source, output, and build paths for a render request."""

        if request.source_kind == "job":
            if not request.job_id:
                raise ValueError("job_id is required for job-based rendering")
            paths = job_render_paths(
                request.source, request.job_id, request.document_type
            )
            source_path = document_adapter.resolve_job_source(request, paths)
            extension = ".docx" if request.engine == "docx" else ".pdf"
            basename = "cv" if request.document_type == "cv" else "cover_letter"
            output_path = paths.render_dir / f"{basename}{extension}"
            return source_path, output_path, paths.build_dir

        source_path = Path(request.source)
        if not source_path.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")
        extension = ".docx" if request.engine == "docx" else ".pdf"
        default_name = f"{source_path.stem}-{request.language}{extension}"
        output_path = build_output_path(request.output_path, default_name)
        build_dir = (
            output_path.parent / f".{request.document_type}-{request.language}-build"
        )
        self.data_manager.ensure_dir(build_dir)
        return source_path, output_path, build_dir
