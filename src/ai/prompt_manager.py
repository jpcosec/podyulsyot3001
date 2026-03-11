"""Prompt loading and Jinja2 rendering utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from jinja2 import Environment, StrictUndefined


class PromptManager:
    """Load node-local prompt files and render runtime prompt strings."""

    def __init__(self, base_path: str = "src/nodes"):
        self.base_path = Path(base_path)

    def load_template(self, node_name: str, template_type: str) -> str:
        """Load one markdown template from `<base>/<node>/prompt/<type>.md`."""
        path = self.base_path / node_name / "prompt" / f"{template_type}.md"
        if not path.exists():
            raise FileNotFoundError(f"template not found: {path}")
        return path.read_text(encoding="utf-8")

    def build_prompt(
        self,
        node_name: str,
        data: Any,
        *,
        required_xml_tags: tuple[str, ...] = ("input_data",),
        optional_xml_tags: tuple[str, ...] = ("feedback_rules",),
    ) -> tuple[str, str]:
        """Render `(system_prompt, user_prompt)` for a node execution."""
        system_prompt = self.load_template(node_name, "system")
        user_template_str = self.load_template(node_name, "user_template")

        context = self._to_context(data)
        user_prompt = self._render_user_template(user_template_str, context)

        self._validate_xml_tags(user_prompt, required_xml_tags, must_exist=True)
        self._validate_xml_tags(user_prompt, optional_xml_tags, must_exist=False)
        return system_prompt, user_prompt

    def _render_user_template(self, template_str: str, context: dict[str, Any]) -> str:
        env = Environment(
            undefined=StrictUndefined,
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.from_string(template_str)
        return template.render(**context)

    def _to_context(self, data: Any) -> dict[str, Any]:
        if hasattr(data, "model_dump"):
            dumped = data.model_dump()
            if not isinstance(dumped, dict):
                raise TypeError("model_dump() must return a dict")
            return dumped

        if isinstance(data, Mapping):
            return dict(data)

        raise TypeError("data must be a mapping or a pydantic-like model")

    def _validate_xml_tags(
        self,
        prompt: str,
        tags: tuple[str, ...],
        *,
        must_exist: bool,
    ) -> None:
        for tag in tags:
            open_tag = f"<{tag}>"
            close_tag = f"</{tag}>"

            open_count = prompt.count(open_tag)
            close_count = prompt.count(close_tag)

            if must_exist and (open_count != 1 or close_count != 1):
                raise ValueError(f"required XML tag pair invalid for '{tag}'")

            if not must_exist and open_count == 0 and close_count == 0:
                continue

            if open_count != close_count:
                raise ValueError(f"unbalanced XML tag pair for '{tag}'")

            if open_count > 1:
                raise ValueError(f"multiple XML tag pairs found for '{tag}'")

            if prompt.find(open_tag) > prompt.find(close_tag):
                raise ValueError(f"XML tags out of order for '{tag}'")
