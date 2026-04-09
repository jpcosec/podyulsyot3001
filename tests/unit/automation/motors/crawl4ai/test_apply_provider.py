"""Unit tests for C4AIReplayer pure logic helpers and C4AIMotorProvider auth.

These tests do NOT import crawl4ai. They test only the pure methods
that can be called without browser infrastructure.
"""

from __future__ import annotations

import os
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
from src.automation.credentials import ResolvedPortalCredentials
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


# ─── C4AIMotorProvider auth tests ────────────────────────────────────────────────


class TestC4AIMotorProviderAuth:
    """Tests for C4AIMotorProvider persistent profile and env-secret login."""

    def test_browser_config_uses_user_data_dir_for_persistent_profile(self):
        """When effective_browser_profile_dir is set, BrowserConfig uses user_data_dir."""
        from src.automation.motors.crawl4ai.apply_engine import C4AIMotorProvider

        provider = C4AIMotorProvider()
        credentials = ResolvedPortalCredentials(
            portal_name="xing",
            matched_domain="xing.com",
            auth_strategy="persistent_profile",
            browser_profile_dir="/custom/profile/dir",
            secret_env_vars={},
            required_secret_keys=[],
            optional_secret_keys=[],
        )

        config = provider._browser_config(credentials=credentials, headless=True)

        assert config.user_data_dir == "/custom/profile/dir"
        assert config.cdp_url is None

    def test_browser_config_skips_browseros_injection_when_profile_dir_set(self):
        """Persistent profile BrowserConfig does not use BrowserOS CDP URL."""
        from src.automation.motors.crawl4ai.apply_engine import C4AIMotorProvider

        provider = C4AIMotorProvider()
        credentials = ResolvedPortalCredentials(
            portal_name="linkedin",
            matched_domain="linkedin.com",
            auth_strategy="persistent_profile",
            browser_profile_dir="/tmp/linkedin-profile",
            secret_env_vars={},
            required_secret_keys=[],
            optional_secret_keys=[],
        )

        config = provider._browser_config(credentials=credentials, headless=True)

        assert config.user_data_dir == "/tmp/linkedin-profile"
        assert config.cdp_url is None

    def test_browser_config_uses_browseros_injection_when_no_profile(self):
        """No profile dir means BrowserOS CDP injection is used."""
        from src.automation.motors.crawl4ai.apply_engine import C4AIMotorProvider

        provider = C4AIMotorProvider()
        credentials = ResolvedPortalCredentials(
            portal_name="xing",
            matched_domain="xing.com",
            auth_strategy="env_secrets",
            browser_profile_dir=None,
            secret_env_vars={"username": "XING_USER", "password": "XING_PASS"},
            required_secret_keys=["username", "password"],
            optional_secret_keys=[],
        )

        config = provider._browser_config(credentials=credentials, headless=True)

        assert config.cdp_url == "http://localhost:9101"
        assert config.user_data_dir is None

    def test_bootstrap_skips_when_required_secrets_missing(self, monkeypatch):
        """Login bootstrap silently skips when required env secrets are not set."""
        from src.automation.motors.crawl4ai.apply_engine import C4AIMotorProvider

        provider = C4AIMotorProvider()
        credentials = ResolvedPortalCredentials(
            portal_name="xing",
            matched_domain="xing.com",
            auth_strategy="env_secrets",
            login_url="https://www.xing.com/login",
            browser_profile_dir=None,
            secret_env_vars={"username": "XING_USER", "password": "XING_PASS"},
            required_secret_keys=["username", "password"],
            optional_secret_keys=[],
        )

        calls = []

        class _FakeCrawler:
            async def arun(self, url, config):
                calls.append((url, config))
                return SimpleNamespace(success=True)

        class _FakeProvider:
            def _browser_config(self, credentials, headless):
                return SimpleNamespace(user_data_dir=None)

        monkeypatch.delenv("XING_USER", raising=False)
        monkeypatch.delenv("XING_PASS", raising=False)

        import asyncio

        asyncio.run(provider._bootstrap_env_secret_login(_FakeCrawler(), credentials))

        assert calls == []

    def test_bootstrap_navigates_and_fills_when_secrets_available(self, monkeypatch):
        """Login bootstrap navigates and fills credentials when env secrets are set."""
        from src.automation.motors.crawl4ai.apply_engine import C4AIMotorProvider

        provider = C4AIMotorProvider()
        credentials = ResolvedPortalCredentials(
            portal_name="xing",
            matched_domain="xing.com",
            auth_strategy="env_secrets",
            login_url="https://www.xing.com/login",
            browser_profile_dir=None,
            secret_env_vars={"username": "XING_USER", "password": "XING_PASS"},
            required_secret_keys=["username", "password"],
            optional_secret_keys=[],
        )

        monkeypatch.setenv("XING_USER", "ada@example.com")
        monkeypatch.setenv("XING_PASS", "secretpassword")

        calls = []

        class _FakeCrawler:
            session_id = "fake-session"

            async def arun(self, url, config):
                calls.append((url, getattr(config, "c4a_script", None)))
                return SimpleNamespace(success=True)

        import asyncio

        asyncio.run(provider._bootstrap_env_secret_login(_FakeCrawler(), credentials))

        assert len(calls) >= 3
        assert calls[0][0] == "https://www.xing.com/login"

    def test_bootstrap_uses_default_url_when_login_url_not_set(self, monkeypatch):
        """When login_url is None, uses default portal URL."""
        from src.automation.motors.crawl4ai.apply_engine import C4AIMotorProvider

        provider = C4AIMotorProvider()
        credentials = ResolvedPortalCredentials(
            portal_name="linkedin",
            matched_domain="linkedin.com",
            auth_strategy="env_secrets",
            login_url=None,
            browser_profile_dir=None,
            secret_env_vars={"username": "LI_USER", "password": "LI_PASS"},
            required_secret_keys=["username", "password"],
            optional_secret_keys=[],
        )

        monkeypatch.setenv("LI_USER", "ada@linkedin.com")
        monkeypatch.setenv("LI_PASS", "secretpassword")

        calls = []

        class _FakeCrawler:
            session_id = "fake-session"

            async def arun(self, url, config):
                calls.append(url)
                return SimpleNamespace(success=True)

        import asyncio

        asyncio.run(provider._bootstrap_env_secret_login(_FakeCrawler(), credentials))

        assert "https://linkedin.com/login" in calls
