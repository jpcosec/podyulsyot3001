"""Thin Pandoc subprocess wrapper used by the render engines."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class PandocRenderer:
    """Render markdown sources to PDF or DOCX using the `pandoc` binary."""

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
        pandoc = shutil.which("pandoc")
        if pandoc is None:
            raise FileNotFoundError("pandoc is required for rendering")

        output_path.parent.mkdir(parents=True, exist_ok=True)
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

        subprocess.run(command, check=True)
        return output_path
