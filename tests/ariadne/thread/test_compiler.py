import pytest

from src.automation.contracts.motor import MotorCommand, TraceEvent
from src.automation.ariadne.thread.thread import AriadneThread, Transition
from src.automation.ariadne.thread.action import TransitionAction, PassiveAction, ExtractionAction
from src.automation.ariadne.thread.compiler import compile
from src.automation.ariadne.thread.translators import translate_command, translate_passive, translate_extraction


def make_thread(*transitions) -> AriadneThread:
    t = AriadneThread("portal", "mission")
    t._transitions = list(transitions)
    return t


def cmd(op="click", sel="#btn", val=None) -> MotorCommand:
    return MotorCommand(operation=op, selector=sel, value=val)


class TestTranslateCommand:
    def test_click(self):
        assert translate_command(cmd("click", "#go")) == "CLICK `#go`"

    def test_submit_maps_to_click(self):
        assert translate_command(cmd("submit", "form")) == "CLICK `form`"

    def test_fill_with_value(self):
        assert translate_command(cmd("fill", "#email", "a@b.com")) == 'SET `#email` "a@b.com"'

    def test_fill_empty_value(self):
        assert translate_command(cmd("fill", "#f", None)) == 'SET `#f` ""'

    def test_navigate(self):
        c = MotorCommand(operation="navigate", selector="", value="https://example.com")
        assert translate_command(c) == "GO https://example.com"

    def test_scroll_with_value(self):
        c = MotorCommand(operation="scroll", selector="", value="300")
        assert translate_command(c) == "SCROLL DOWN 300"

    def test_scroll_default(self):
        assert translate_command(cmd("scroll")) == "SCROLL DOWN 500"

    def test_unknown_operation_is_comment(self):
        line = translate_command(cmd("teleport"))
        assert line.startswith("#")


class TestTranslatePassive:
    def test_scroll(self):
        assert translate_passive(PassiveAction(operation="scroll")) == "SCROLL DOWN 500"

    def test_wait(self):
        assert translate_passive(PassiveAction(operation="wait")) == "WAIT 1"

    def test_hover(self):
        line = translate_passive(PassiveAction(operation="hover", selector="#menu"))
        assert "EVAL" in line
        assert "#menu" in line

    def test_unknown_is_comment(self):
        line = translate_passive(PassiveAction(operation="blink"))
        assert line.startswith("#")


class TestTranslateExtraction:
    def test_returns_comment(self):
        line = translate_extraction(ExtractionAction(schema_id="jobs"))
        assert line.startswith("#")
        assert "jobs" in line


class TestCompile:
    def test_empty_thread_returns_header(self):
        t = make_thread()
        script = compile(t)
        assert "portal/mission" in script

    def test_transition_becomes_instructions(self):
        action = TransitionAction(commands=(cmd("click", "#go"),))
        t = make_thread(Transition("home", [action], "next"))
        script = compile(t)
        assert "CLICK `#go`" in script

    def test_room_labels_are_comments(self):
        action = TransitionAction(commands=(cmd(),))
        t = make_thread(Transition("home", [action], "done"))
        script = compile(t)
        assert "# home → done" in script

    def test_multi_command_transition(self):
        action = TransitionAction(commands=(cmd("fill", "#e", "a@b.com"), cmd("click", "#sub")))
        t = make_thread(Transition("form", [action], "dash"))
        lines = compile(t).splitlines()
        assert any("SET" in l for l in lines)
        assert any("CLICK" in l for l in lines)

    def test_extraction_action_becomes_comment(self):
        extract = ExtractionAction(schema_id="job_list")
        t = make_thread(Transition("search", [extract], "search"))
        script = compile(t)
        assert "ExtractionAction" in script

    def test_multiple_transitions_in_order(self):
        a1 = TransitionAction(commands=(cmd("click", "#login"),))
        a2 = TransitionAction(commands=(cmd("click", "#apply"),))
        t = make_thread(
            Transition("home", [a1], "form"),
            Transition("form", [a2], "done"),
        )
        script = compile(t)
        assert script.index("CLICK `#login`") < script.index("CLICK `#apply`")
