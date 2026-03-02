"""Render Jinja2 templates with CV data."""

import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


def _latex_safe(text: object) -> str:
    """Escape markdown/special chars for LaTeX.

    # and leading * are rendered in white: ATS text-extractors see them,
    the printed PDF does not. % and & are escaped to avoid LaTeX errors.
    """
    result = str(text) if text else ""
    # # is a LaTeX parameter char — must escape; white keeps it ATS-visible
    result = result.replace("#", r"\textcolor{white}{\#}")
    # Leading * (markdown bullet at start of line) — white for ATS
    result = re.sub(r"(?m)^(\s*)\*(\s)", r"\1\textcolor{white}{*}\2", result)
    # Standard escapes that affect LaTeX compilation
    result = result.replace("%", r"\%")
    result = result.replace("&", r"\&")
    return result


def render_template(
    template_name: str,
    template_dir: str | Path,
    context: dict[str, Any],
) -> str:
    """Render a Jinja2 template with the given context.

    Args:
        template_name: Name of the template file (e.g., 'german.tex.jinja2')
        template_dir: Directory containing templates
        context: Dictionary with variables for template rendering

    Returns:
        Rendered template as string
    """
    template_dir = Path(template_dir)

    if not template_dir.exists():
        raise FileNotFoundError(f"Template directory not found: {template_dir}")

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["latex_safe"] = _latex_safe

    template = env.get_template(template_name)
    return template.render(**context)


def render_to_file(
    template_name: str,
    template_dir: str | Path,
    context: dict[str, Any],
    output_path: str | Path,
) -> Path:
    """Render template and save to file.

    Args:
        template_name: Name of the template file
        template_dir: Directory containing templates
        context: Dictionary with variables for template rendering
        output_path: Path where to save rendered output

    Returns:
        Path to the created file
    """
    rendered = render_template(template_name, template_dir, context)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered)

    return output_path
