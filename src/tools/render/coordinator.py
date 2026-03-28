"""Central render coordinator."""

from __future__ import annotations

import shutil
from pathlib import Path

from src.render.documents.base import DocumentPayload
from src.render.engines.base import ResolvedRenderConfig
from src.render.engines.latex.renderer import LatexRenderer
from src.render.languages.registry import get_language_bundle
from src.render.registry import (
    get_document_adapter,
    get_engine_adapter,
    load_style_manifest,
    resolve_manifest_paths,
)
from src.render.request import RenderRequest
from src.render.shared.paths import build_output_path, job_render_paths


class RenderCoordinator:
    """Orchestrates the document rendering process by resolving adapters, manifests, and engines.

    This coordinator acts as a facade, hiding the complexity of resolving engine-specific 
    configurations, style manifests, and localized asset paths.
    """

    def __init__(self):
        """Initialize the coordinator with required renderers."""
        self.latex = LatexRenderer()

    def render(self, request: RenderRequest) -> Path:
        """Execute a rendering request end-to-end.

        Args:
            request (RenderRequest): The unified request object containing document type, 
                engine, language, and source data.

        Returns:
            Path: The absolute path to the generated document file.
        """
        document_adapter = get_document_adapter(request.document_type)
        style = request.style or document_adapter.default_style
        source_path, output_path, build_dir = self._resolve_paths(
            request, document_adapter
        )
        payload = document_adapter.build_payload(source_path, request)
        language_bundle = get_language_bundle(request.language)

        if payload.source_kind == "legacy_json":
            return self._render_legacy_json(payload, request, output_path, build_dir)

        manifest = load_style_manifest(request.document_type, style)
        template_path, reference_doc, lua_filters, asset_roots = resolve_manifest_paths(
            manifest, request.engine
        )
        metadata = language_bundle.metadata_for(request.document_type, style)
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
        """Resolve relevant source, output, and build paths for a render request.

        Args:
            request (RenderRequest): The current render request.
            document_adapter: The resolved document adapter for the request type.

        Returns:
            tuple[Path, Path, Path]: A tuple containing (source_path, output_path, build_dir).
        """
        if request.source_kind == "job":
            if not request.job_id:
                raise ValueError("job_id is required for job-based rendering")
            paths = job_render_paths(
                request.source, request.job_id, request.document_type
            )
            source_path = document_adapter.resolve_job_source(request, paths)
            extension = ".docx" if request.engine == "docx" else ".pdf"
            basename = "cv" if request.document_type == "cv" else "motivation_letter"
            output_path = paths.application_dir / f"{basename}{extension}"
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
        build_dir.mkdir(parents=True, exist_ok=True)
        return source_path, output_path, build_dir

    def _render_legacy_json(
        self,
        payload: DocumentPayload,
        request: RenderRequest,
        output_path: Path,
        build_dir: Path,
    ) -> Path:
        pdf_path = self.latex.compile_cv_pdf(
            payload.legacy_context or {},
            build_dir,
            language={"en": "english", "es": "spanish", "de": "german"}[
                request.language
            ],
        )
        shutil.copy(str(pdf_path), str(output_path))
        return output_path
