import pytest
from src.automation.ariadne.contracts.base import (
    AriadneIntent,
    AriadneTarget,
    BrowserOSCommand,
    CrawlCommand,
)
from src.automation.ariadne.models import AriadneState
from src.automation.adapters.translators.browseros import BrowserOSTranslator
from src.automation.adapters.translators.crawl4ai import Crawl4AITranslator


@pytest.fixture
def mock_state() -> AriadneState:
    return {
        "job_id": "job-123",
        "portal_name": "xing",
        "profile_data": {"first_name": "John", "last_name": "Doe"},
        "job_data": {"job_title": "Developer"},
        "session_memory": {"app_id": "APP-999"},
        "current_state_id": "start",
        "dom_elements": [],
        "current_url": "https://example.com",
        "screenshot_b64": None,
        "errors": [],
        "history": [],
        "portal_mode": "apply",
        "path_id": None,
    }


def test_placeholder_resolution(mock_state):
    translator = BrowserOSTranslator()
    text = "Hello {{first_name}} {{last_name}}, applying for {{job_title}} (Ref: {{app_id}})"
    resolved = translator.resolve_placeholders(text, mock_state)
    assert resolved == "Hello John Doe, applying for Developer (Ref: APP-999)"


def test_browseros_translator_click(mock_state):
    translator = BrowserOSTranslator()
    target = AriadneTarget(text="Login")
    command = translator.translate_intent(AriadneIntent.CLICK, target, mock_state)
    assert isinstance(command, BrowserOSCommand)
    assert command.tool == "click"
    assert command.selector_text == "Login"


def test_browseros_translator_fill(mock_state):
    translator = BrowserOSTranslator()
    target = AriadneTarget(css="#first_name")
    command = translator.translate_intent(
        AriadneIntent.FILL, target, mock_state, value="{{first_name}}"
    )
    assert isinstance(command, BrowserOSCommand)
    assert command.tool == "fill"
    assert command.selector_text == "#first_name"
    assert command.value == "John"


def test_crawl4ai_translator_click(mock_state):
    translator = Crawl4AITranslator()
    target = AriadneTarget(css="button.submit")
    command = translator.translate_intent(AriadneIntent.CLICK, target, mock_state)
    assert isinstance(command, CrawlCommand)
    assert 'await page.click("button.submit")' in command.c4a_script


def test_crawl4ai_translator_fill(mock_state):
    translator = Crawl4AITranslator()
    target = AriadneTarget(css="input[name='q']")
    command = translator.translate_intent(
        AriadneIntent.FILL, target, mock_state, value="Python"
    )
    assert isinstance(command, CrawlCommand)
    assert 'await page.fill("input[name=\'q\']", "Python")' in command.c4a_script
