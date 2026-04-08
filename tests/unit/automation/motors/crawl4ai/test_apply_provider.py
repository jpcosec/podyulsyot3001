"""Unit tests for C4AIReplayer pure logic helpers.

These tests do NOT import crawl4ai. They test only the pure methods
that can be called without browser infrastructure.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from src.automation.ariadne.exceptions import FormReviewRequired
from src.automation.ariadne.models import (
    AriadneAction,
    AriadneIntent,
    AriadneObserve,
    AriadneStep,
)
from src.automation.motors.crawl4ai.replayer import C4AIReplayer


class TestRenderPlaceholders:
    def test_basic_interpolation(self):
        """_render_placeholders substitutes {{placeholders}} with context values."""
        replayer = C4AIReplayer()
        template = 'SET `input` "{{first_name}}"'
        result = replayer._render_placeholders(template, {"first_name": "Alice"})
        assert result == 'SET `input` "Alice"'

    def test_nested_interpolation(self):
        """_render_placeholders supports nested profile.key access."""
        replayer = C4AIReplayer()
        template = 'SET `input` "{{profile.first_name}}"'
        result = replayer._render_placeholders(
            template, {"profile": {"first_name": "Alice"}}
        )
        assert result == 'SET `input` "Alice"'


class _FakeCrawler:
    def __init__(self, extracted=None):
        self.extracted = extracted or []
        self.calls = []

    async def arun(self, url: str, config):
        self.calls.append((url, config))
        hook = getattr(config, "hooks", {}).get("before_retrieve_html")
        if hook is not None:
            page = _FakePage(self.extracted)
            await hook(page)
        return SimpleNamespace(success=True, error_message=None)


class _FakePage:
    def __init__(self, extracted):
        self.extracted = extracted
        self.uploads = []

    async def evaluate(self, _script: str):
        return self.extracted

    async def set_input_files(self, selector: str, file_path: str):
        self.uploads.append((selector, file_path))


@pytest.mark.asyncio
async def test_execute_step_expands_form_analysis_before_compilation(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "src.automation.motors.crawl4ai.replayer.CrawlerRunConfig",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )
    replayer = C4AIReplayer()
    crawler = _FakeCrawler(
        extracted=[
            {
                "id": "first-name",
                "type": "input",
                "label": "First name",
                "selector": "#first-name",
                "required": True,
            },
            {
                "id": "resume",
                "type": "file",
                "label": "Resume",
                "selector": "#resume",
                "required": True,
            },
        ]
    )
    step = AriadneStep(
        step_index=1,
        name="dynamic_form",
        description="Analyze and fill the live form",
        observe=AriadneObserve(),
        actions=[AriadneAction(intent=AriadneIntent.ANALYZE_FORM)],
    )

    await replayer.execute_step(
        step=step,
        crawler=crawler,
        session_id="sess-1",
        context={"profile": {"first_name": "Ada"}},
        cv_path=Path("/tmp/cv.pdf"),
        is_first_step=False,
    )

    _url, config = crawler.calls[-1]
    assert 'SET #first-name "Ada"' in config.c4a_script
    assert "UPLOAD #resume" in config.c4a_script
    assert "before_retrieve_html" in config.hooks


@pytest.mark.asyncio
async def test_execute_step_raises_form_review_when_required_field_is_unknown(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "src.automation.motors.crawl4ai.replayer.CrawlerRunConfig",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )
    replayer = C4AIReplayer()
    crawler = _FakeCrawler(
        extracted=[
            {
                "id": "employee-code",
                "type": "input",
                "label": "Employee code",
                "selector": "#employee-code",
                "required": True,
            }
        ]
    )
    step = AriadneStep(
        step_index=1,
        name="dynamic_form",
        description="Analyze and fill the live form",
        observe=AriadneObserve(),
        actions=[AriadneAction(intent=AriadneIntent.ANALYZE_FORM)],
    )

    with pytest.raises(FormReviewRequired, match="requires human review") as exc:
        await replayer.execute_step(
            step=step,
            crawler=crawler,
            session_id="sess-1",
            context={"profile": {}},
            cv_path=Path("/tmp/cv.pdf"),
            is_first_step=False,
        )

    assert "Employee code" in exc.value.details["summary"]


@pytest.mark.asyncio
async def test_execute_step_raises_review_when_selector_is_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "src.automation.motors.crawl4ai.replayer.CrawlerRunConfig",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )
    replayer = C4AIReplayer()
    crawler = _FakeCrawler(
        extracted=[
            {
                "id": "first-name",
                "type": "input",
                "label": "First name",
                "selector": None,
                "required": True,
            }
        ]
    )
    step = AriadneStep(
        step_index=1,
        name="dynamic_form",
        description="Analyze and fill the live form",
        observe=AriadneObserve(),
        actions=[AriadneAction(intent=AriadneIntent.ANALYZE_FORM)],
    )

    with pytest.raises(FormReviewRequired, match="requires human review") as exc:
        await replayer.execute_step(
            step=step,
            crawler=crawler,
            session_id="sess-1",
            context={"profile": {"first_name": "Ada"}},
            cv_path=Path("/tmp/cv.pdf"),
            is_first_step=False,
        )

    assert "selector missing" in exc.value.details["summary"]


@pytest.mark.asyncio
async def test_execute_step_preserves_action_order_when_expanding_form_analysis(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "src.automation.motors.crawl4ai.replayer.CrawlerRunConfig",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )
    replayer = C4AIReplayer()
    crawler = _FakeCrawler(
        extracted=[
            {
                "id": "first-name",
                "type": "input",
                "label": "First name",
                "selector": "#first-name",
                "required": True,
            }
        ]
    )
    step = AriadneStep(
        step_index=1,
        name="dynamic_form",
        description="Analyze and fill the live form",
        observe=AriadneObserve(),
        actions=[
            AriadneAction(
                intent=AriadneIntent.CLICK,
                target={"css": "#start"},
            ),
            AriadneAction(intent=AriadneIntent.ANALYZE_FORM),
            AriadneAction(
                intent=AriadneIntent.CLICK,
                target={"css": "#submit"},
            ),
        ],
    )

    await replayer.execute_step(
        step=step,
        crawler=crawler,
        session_id="sess-1",
        context={"profile": {"first_name": "Ada"}},
        cv_path=Path("/tmp/cv.pdf"),
        is_first_step=False,
    )

    _url, config = crawler.calls[-1]
    click_start_index = config.c4a_script.index("CLICK #start")
    fill_index = config.c4a_script.index('SET #first-name "Ada"')
    click_submit_index = config.c4a_script.index("CLICK #submit")
    assert click_start_index < fill_index < click_submit_index


def test_upload_targets_skips_optional_letter_when_path_missing():
    replayer = C4AIReplayer()
    step = AriadneStep(
        step_index=1,
        name="uploads",
        description="Upload docs",
        observe=AriadneObserve(),
        actions=[
            AriadneAction(
                intent=AriadneIntent.UPLOAD,
                target={"css": "#resume"},
            ),
            AriadneAction(
                intent=AriadneIntent.UPLOAD_LETTER,
                target={"css": "#letter"},
                optional=True,
            ),
        ],
    )

    uploads = replayer._upload_targets(
        step,
        cv_path=Path("/tmp/cv.pdf"),
        letter_path=None,
    )

    assert uploads == {"#resume": Path("/tmp/cv.pdf")}
