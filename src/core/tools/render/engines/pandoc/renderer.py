"""Thin Pandoc subprocess wrapper used by the render engines."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from src.core.data_manager import DataManager


class PandocRenderer:
    """Render markdown sources to PDF or DOCX using the `pandoc` binary."""

    def __init__(self) -> None:
        self.data_manager = DataManager()

    def render(
        self,
        source_path: Path,
        output_path: Path,
        *,
        target_format: str,
        template_path: Path | None = None,
        lua_filters: list[Path] | None = None,
        asset_roots: list[Path] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Path:
        """Invoke pandoc to render one markdown source.

        Args:
            source_path: Markdown source to render.
            output_path: Destination output file.
            target_format: Pandoc output format such as ``pdf`` or ``docx``.
            template_path: Optional pandoc template path.
            lua_filters: Optional lua filters to apply.
            asset_roots: Optional resource roots for templates and assets.
            metadata: Optional pandoc ``-V`` metadata entries.

        Returns:
            The resolved output path after a successful render.
        """
        pandoc = shutil.which("pandoc")
        if pandoc is None:
            raise FileNotFoundError("pandoc is required for rendering")

        source_path = source_path.resolve()
        output_path = output_path.resolve()
        self.data_manager.ensure_dir(output_path.parent)
        command = [
            pandoc,
            str(source_path),
            "-o",
            str(output_path),
            "-t",
            target_format,
        ]

        if template_path and template_path.exists():
            command.extend(["--template", str(template_path)])

        for lua_filter in lua_filters or []:
            if lua_filter.exists():
                command.extend(["--lua-filter", str(lua_filter)])

        for key, value in (metadata or {}).items():
            command.extend(["-V", f"{key}={value}"])

        resource_paths = [str(path) for path in asset_roots or [] if path.exists()]
        if resource_paths:
            command.extend(["--resource-path", ":".join(resource_paths)])

        working_dir = next((path for path in asset_roots or [] if path.exists()), None)
        subprocess.run(command, check=True, cwd=working_dir)
        return output_path
