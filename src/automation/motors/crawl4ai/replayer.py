"""Crawl4AI Replayer — Low-Level Path Execution.

This module owns the motor-specific execution loop for Crawl4AI.
It knows how to run a single AriadneStep or a sequence of steps
using the C4AI compiler and the active browser session.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Optional

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from src.automation.ariadne.exceptions import FormReviewRequired, ObservationFailed
from src.automation.ariadne.form_analyzer import AriadneFormAnalyzer
from src.automation.ariadne.models import AriadneIntent, AriadnePath, AriadneStep
from src.automation.motors.crawl4ai.compiler import (
    AriadneC4AICompiler,
    C4AIScriptSerializer,
)
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class C4AIReplayer:
    """Replays Ariadne Steps using the Crawl4AI motor."""

    def __init__(self):
        self.compiler = AriadneC4AICompiler()
        self.serializer = C4AIScriptSerializer()
        self._form_analyzer = AriadneFormAnalyzer()

    async def execute_step(
        self,
        step: AriadneStep,
        crawler: AsyncWebCrawler,
        session_id: str,
        context: dict[str, Any],
        cv_path: Path,
        letter_path: Optional[Path] = None,
        is_first_step: bool = False,
        application_url: Optional[str] = None,
    ) -> Any:
        """Executes a single Ariadne step."""
        step = await self._expand_form_analysis(
            step=step,
            crawler=crawler,
            session_id=session_id,
        )

        upload_targets = self._upload_targets(
            step,
            cv_path=cv_path,
            letter_path=letter_path,
        )

        # Compile step
        temp_path = AriadnePath(id="temp", task_id="temp", steps=[step])
        ir = self.compiler.compile(temp_path)
        raw_script = self.serializer.serialize(ir)

        # Render placeholders
        final_script = self._render_placeholders(raw_script, context)

        run_config = CrawlerRunConfig(
            c4a_script=final_script,
            session_id=session_id,
            screenshot=True,
        )

        if upload_targets:
            run_config.hooks = {
                "before_retrieve_html": self._build_file_upload_hook(upload_targets)
            }

        url = application_url if is_first_step and application_url else "about:blank"

        result = await crawler.arun(url=url, config=run_config)

        if not result.success:
            raise ObservationFailed(
                f"Step {step.name} execution failed: {result.error_message}",
                step_index=step.step_index,
            )

        return result

    async def _expand_form_analysis(
        self,
        *,
        step: AriadneStep,
        crawler: AsyncWebCrawler,
        session_id: str,
    ) -> AriadneStep:
        analyze_actions = [
            action
            for action in step.actions
            if action.intent == AriadneIntent.ANALYZE_FORM
        ]
        if not analyze_actions:
            return step

        elements = await self._extract_form_elements(
            crawler=crawler, session_id=session_id
        )
        analyzed_form = self._form_analyzer.analyze_generic_elements(elements)
        self._require_actionable_selectors(analyzed_form)
        if analyzed_form.requires_review():
            raise FormReviewRequired(
                "Form analysis requires human review before submission.",
                form=analyzed_form,
                details={"summary": analyzed_form.review_summary()},
            )

        derived_actions = analyzed_form.to_ariadne_actions()
        expanded_actions = []
        inserted_analysis = False
        for action in step.actions:
            if action.intent != AriadneIntent.ANALYZE_FORM:
                expanded_actions.append(action)
                continue
            if not inserted_analysis:
                expanded_actions.extend(derived_actions)
                inserted_analysis = True
        return step.model_copy(update={"actions": expanded_actions})

    def _require_actionable_selectors(self, analyzed_form) -> None:
        for field in analyzed_form.fields:
            action = field.resolve_action()
            if action is None:
                continue
            if action.target and action.target.css:
                continue
            field.review_required = True
            field.review_reason = "field selector missing for Crawl4AI execution"

    def _render_placeholders(self, text: str, context: dict) -> str:
        """Inject context values into {{placeholder}} strings."""
        result = text
        for key, value in context.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    placeholder = f"{{{{{key}.{k}}}}}"
                    if placeholder in result:
                        result = result.replace(
                            placeholder, str(v) if v is not None else ""
                        )
            else:
                placeholder = "{{" + key + "}}"
                if placeholder in result:
                    result = result.replace(
                        placeholder, str(value) if value is not None else ""
                    )
        return result

    async def _extract_form_elements(
        self,
        *,
        crawler: AsyncWebCrawler,
        session_id: str,
    ) -> list[dict[str, Any]]:
        extracted: list[dict[str, Any]] = []
        script = """
            return Array.from(
                document.querySelectorAll('input, textarea, select, button')
            ).map((element, index) => {
                const tag = element.tagName.toLowerCase();
                const type = tag === 'input'
                    ? (element.getAttribute('type') || 'input').toLowerCase()
                    : tag;
                const id = element.id || `field-${index}`;
                const labelNode = element.labels && element.labels.length
                    ? element.labels[0]
                    : null;
                const label = labelNode
                    ? labelNode.innerText
                    : (element.getAttribute('aria-label') || element.getAttribute('placeholder') || '');
                const name = element.getAttribute('name') || '';
                const ariaLabel = element.getAttribute('aria-label') || '';
                const placeholder = element.getAttribute('placeholder') || '';
                const options = tag === 'select'
                    ? Array.from(element.options || []).map((option) => option.textContent || '').filter(Boolean)
                    : [];
                const escaped = (value) => {
                    if (!value) {
                        return '';
                    }
                    if (window.CSS && typeof window.CSS.escape === 'function') {
                        return window.CSS.escape(value);
                    }
                    return value.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
                };
                let selector = null;
                if (element.id) {
                    selector = `#${escaped(element.id)}`;
                } else if (name) {
                    selector = `${tag}[name="${escaped(name)}"]`;
                } else if (ariaLabel) {
                    selector = `${tag}[aria-label="${escaped(ariaLabel)}"]`;
                } else if (placeholder) {
                    selector = `${tag}[placeholder="${escaped(placeholder)}"]`;
                }
                return {
                    id,
                    type: type === 'file' ? 'file' : tag,
                    input_type: type,
                    label,
                    text: (element.innerText || element.textContent || '').trim(),
                    selector,
                    required: Boolean(element.required || element.getAttribute('aria-required') === 'true'),
                    options,
                };
            });
        """

        async def _hook(page: Any, **kwargs: Any) -> Any:
            nonlocal extracted
            extracted = await page.evaluate(script)
            return page

        await crawler.arun(
            url="about:blank",
            config=CrawlerRunConfig(
                js_only=True,
                session_id=session_id,
                hooks={"before_retrieve_html": _hook},
            ),
        )
        return extracted

    def _upload_targets(
        self,
        step: AriadneStep,
        *,
        cv_path: Path,
        letter_path: Path | None,
    ) -> dict[str, Path]:
        uploads: dict[str, Path] = {}
        for action in step.actions:
            if not action.target or not action.target.css:
                continue
            if action.intent == AriadneIntent.UPLOAD:
                uploads[action.target.css] = cv_path
            elif action.intent == AriadneIntent.UPLOAD_LETTER:
                if letter_path is None:
                    if action.optional:
                        continue
                    raise ValueError(
                        "upload_letter action requires letter_path or an explicit value"
                    )
                uploads[action.target.css] = letter_path
        return uploads

    def _build_file_upload_hook(self, uploads: dict[str, Path]):
        """Return a hook that performs file uploads via raw Playwright."""

        async def _hook(page: Any, **kwargs: Any) -> Any:
            for selector, file_path in uploads.items():
                await page.set_input_files(selector, str(file_path))
            return page

        return _hook
