import pytest

from src.automation.ariadne.thread.passive_ingest import ingest, _url_to_room_id, _best_selector
from src.automation.ariadne.thread.action import TransitionAction, PassiveAction
from src.automation.contracts.motor import MotorCommand


def recording(steps):
    return {"title": "test", "steps": steps}


def navigate_step(url):
    return {"type": "navigate", "url": url}


def click_step(selector):
    return {"type": "click", "selectors": [[selector]]}


def change_step(selector, value):
    return {"type": "change", "selectors": [[selector]], "value": value}


def scroll_step():
    return {"type": "scroll", "x": 0, "y": 500}


class TestIngest:
    def test_returns_draft_thread(self):
        thread = ingest(recording([navigate_step("https://example.com")]), "p", "m")
        assert thread.draft is True
        assert thread.portal_name == "p"
        assert thread.mission_id == "m"

    def test_navigate_creates_transition(self):
        thread = ingest(recording([navigate_step("https://example.com/jobs")]), "p", "m")
        assert len(thread._transitions) == 1
        t = thread._transitions[0]
        assert t.room_from == "start"
        assert "example.com" in t.room_to

    def test_click_after_navigate_grouped_into_next_transition(self):
        steps = [navigate_step("https://a.com"), click_step("#btn"), navigate_step("https://b.com")]
        thread = ingest(recording(steps), "p", "m")
        # First navigate: start → a.com (no pre-actions)
        # click + second navigate: a.com → b.com
        assert len(thread._transitions) == 2
        t_a_to_b = thread._transitions[1]
        actions = t_a_to_b.actions
        assert any(isinstance(a, TransitionAction) for a in actions)

    def test_change_step_becomes_fill_command(self):
        steps = [navigate_step("https://a.com"), change_step("#email", "a@b.com")]
        thread = ingest(recording(steps), "p", "m")
        # trailing actions go into .end transition
        assert len(thread._transitions) == 2
        t = thread._transitions[1]
        action = t.actions[0]
        assert isinstance(action, TransitionAction)
        assert action.commands[0].operation == "fill"
        assert action.commands[0].value == "a@b.com"

    def test_scroll_becomes_passive_action(self):
        steps = [navigate_step("https://a.com"), scroll_step()]
        thread = ingest(recording(steps), "p", "m")
        t = thread._transitions[1]
        assert isinstance(t.actions[0], PassiveAction)
        assert t.actions[0].operation == "scroll"

    def test_unknown_step_types_are_skipped(self):
        steps = [navigate_step("https://a.com"), {"type": "setViewport"}, {"type": "waitForElement"}]
        thread = ingest(recording(steps), "p", "m")
        assert len(thread._transitions) == 1  # only the navigate

    def test_empty_steps_returns_empty_thread(self):
        thread = ingest(recording([]), "p", "m")
        assert thread._transitions == []

    def test_trailing_actions_without_final_navigate(self):
        steps = [navigate_step("https://a.com"), click_step("#go")]
        thread = ingest(recording(steps), "p", "m")
        assert len(thread._transitions) == 2
        assert thread._transitions[1].room_to.endswith(".end")


class TestHelpers:
    def test_url_to_room_id_basic(self):
        assert _url_to_room_id("https://stepstone.de/jobs") == "stepstone.de.jobs"

    def test_url_to_room_id_trailing_slash(self):
        assert _url_to_room_id("https://example.com/") == "example.com"

    def test_url_to_room_id_empty(self):
        assert _url_to_room_id("") == "home"

    def test_best_selector_first_in_first_group(self):
        assert _best_selector([["#primary", ".fallback"], ["aria/label"]]) == "#primary"

    def test_best_selector_empty(self):
        assert _best_selector([]) == ""


class TestPassiveActionRoundtrip:
    def test_passive_survives_save_load(self, tmp_path):
        from unittest.mock import patch
        steps = [navigate_step("https://a.com"), scroll_step(), click_step("#btn")]
        thread = ingest(recording(steps), "portal", "mission")
        with patch("src.automation.ariadne.thread.thread.DATA_ROOT", tmp_path):
            thread.save()
            from src.automation.ariadne.thread.thread import AriadneThread
            restored = AriadneThread.load("portal", "mission")
            assert restored.draft is True
            # trailing transition has [scroll, click]
            t = restored._transitions[1]
            assert isinstance(t.actions[0], PassiveAction)
