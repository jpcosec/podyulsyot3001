import pytest
from unittest.mock import patch

from src.automation.contracts.motor import MotorCommand, TraceEvent
from src.automation.ariadne.thread.thread import AriadneThread
from src.automation.ariadne.thread.action import TransitionAction


def cmd(operation="click", selector="#btn") -> MotorCommand:
    return MotorCommand(operation=operation, selector=selector)


def success_event(room_before: str) -> TraceEvent:
    return TraceEvent(command=cmd(), success=True, room_before=room_before)


def failed_event(room_before: str) -> TraceEvent:
    return TraceEvent(command=cmd(), success=False, room_before=room_before, error="timeout")


class TestGetNextStep:
    def test_returns_commands_for_known_room(self):
        thread = AriadneThread("portal", "mission")
        thread._transitions = []
        event = success_event("home.anon")
        thread.add_step(event, room_after="search.results")

        commands = thread.get_next_step("home.anon")
        assert commands is not None
        assert len(commands) == 1

    def test_returns_none_for_unknown_room(self):
        thread = AriadneThread("portal", "mission")
        assert thread.get_next_step("unknown.room") is None

    def test_returns_none_for_empty_thread(self):
        thread = AriadneThread("portal", "mission")
        assert thread.get_next_step("home.anon") is None


class TestAddStep:
    def test_records_successful_transition(self):
        thread = AriadneThread("portal", "mission")
        thread.add_step(success_event("home.anon"), room_after="results.page")
        assert thread.get_next_step("home.anon") is not None

    def test_ignores_failed_event(self):
        thread = AriadneThread("portal", "mission")
        thread.add_step(failed_event("home.anon"), room_after="results.page")
        assert thread.get_next_step("home.anon") is None

    def test_ignores_event_without_room_before(self):
        thread = AriadneThread("portal", "mission")
        event = TraceEvent(command=cmd(), success=True, room_before=None)
        thread.add_step(event, room_after="results.page")
        assert thread.get_next_step("home.anon") is None

    def test_merges_duplicate_transitions(self):
        thread = AriadneThread("portal", "mission")
        thread.add_step(success_event("home.anon"), room_after="results.page")
        thread.add_step(success_event("home.anon"), room_after="results.page")

        t = thread._find_transition("home.anon", "results.page")
        assert t is not None
        assert len(t.actions) == 2  # both recorded, not deduplicated

    def test_separate_rooms_separate_transitions(self):
        thread = AriadneThread("portal", "mission")
        thread.add_step(success_event("home.anon"), room_after="results.page")
        thread.add_step(
            TraceEvent(command=cmd(selector="#other"), success=True, room_before="results.page"),
            room_after="job.detail",
        )
        assert thread.get_next_step("home.anon") is not None
        assert thread.get_next_step("results.page") is not None


class TestPersistence:
    def test_save_and_load(self, tmp_path):
        with patch("src.automation.ariadne.thread.thread.DATA_ROOT", tmp_path):
            thread = AriadneThread("portal", "mission")
            thread.add_step(success_event("home.anon"), room_after="results.page")
            thread.save()

            restored = AriadneThread.load("portal", "mission")
            assert restored.get_next_step("home.anon") is not None

    def test_load_nonexistent_returns_empty(self, tmp_path):
        with patch("src.automation.ariadne.thread.thread.DATA_ROOT", tmp_path):
            thread = AriadneThread.load("portal", "nonexistent_mission")
            assert thread.get_next_step("home.anon") is None

    def test_commands_preserved_after_roundtrip(self, tmp_path):
        with patch("src.automation.ariadne.thread.thread.DATA_ROOT", tmp_path):
            thread = AriadneThread("portal", "mission")
            thread.add_step(
                TraceEvent(command=cmd("fill", "#email"), success=True, room_before="home.anon"),
                room_after="dashboard",
            )
            thread.save()

            restored = AriadneThread.load("portal", "mission")
            commands = restored.get_next_step("home.anon")
            assert commands[0].operation == "fill"
            assert commands[0].selector == "#email"
