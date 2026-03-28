"""Jinja2 LaTeX template rendering with latex_safe filter."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined


_LATEX_ESCAPE = str.maketrans(#TODO: This could be incorporated onto templates
    {
        "#": r"\atswhite{\#}",
        "*": r"\atswhite{*}",
        "%": r"\%",
        "&": r"\&",
    }
)

_ASSETS_DIR = Path(__file__).parent / "latex_assets"
_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _latex_safe(text: str) -> str:
    """Escape characters that need special treatment in LaTeX output."""
    return text.translate(_LATEX_ESCAPE)


def render_template(
    template_name: str,
    template_dir: str | Path,
    context: dict[str, Any],
) -> str:
    """Render a Jinja2 LaTeX template with latex_safe filter available."""
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        undefined=StrictUndefined,
        block_start_string=r"{%",
        block_end_string=r"%}",
        variable_start_string=r"{{",
        variable_end_string=r"}}",
        comment_start_string=r"{#",
        comment_end_string=r"#}",
    )
    env.filters["latex_safe"] = _latex_safe
    template = env.get_template(template_name)
    return template.render(**context)


def render_to_file(
    template_name: str,
    template_dir: str | Path,
    context: dict[str, Any],
    output_path: str | Path,
) -> None:
    """Render template and write result to output_path."""
    content = render_template(template_name, template_dir, context)
    Path(output_path).write_text(content, encoding="utf-8")


def compile_cv_pdf(
    context: dict[str, Any],
    output_dir: str | Path,
    *,
    language: str = "english",
    photo_path: str | Path | None = None,
) -> Path:
    """Render CV template and compile to PDF via pdflatex.

    Copies LaTeX support assets into output_dir, renders the Jinja2 template
    to main.tex, then runs pdflatex. Returns path to the generated PDF.

    Args:
        context: Template context dict (personal, education, experience, etc.)
        output_dir: Directory where main.tex and main.pdf will be written.
        language: One of 'english', 'german', 'spanish'.
        photo_path: Optional override for profile photo. If None, uses the
            bundled default from latex_assets/Abbildungen/profile.jpg.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Copy support assets (Einstellungen/ and Abbildungen/)
    for asset_subdir in ("Einstellungen", "Abbildungen"):
        src = _ASSETS_DIR / asset_subdir
        dst = out / asset_subdir
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    # Override photo if caller supplies one
    if photo_path is not None:
        shutil.copy(str(photo_path), str(out / "Abbildungen" / "profile.jpg"))

    # Render .tex
    template_name = f"{language}.tex.jinja2"
    tex_path = out / "main.tex"
    render_to_file(template_name, _TEMPLATES_DIR, context, tex_path)

    # Compile — run twice for stable cross-references
    for _ in range(2):
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "main.tex"],
            cwd=str(out),
            capture_output=True,
            text=True,
        )

    pdf_path = out / "main.pdf"
    if not pdf_path.exists():
        raise RuntimeError(f"pdflatex did not produce {pdf_path}")

    return pdf_path
