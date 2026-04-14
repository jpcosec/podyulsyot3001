import dataclasses
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.automation.contracts.sensor import SnapshotResult
from src.automation.contracts.motor import MotorCommand, TraceEvent, ExecutionResult
from src.automation.ariadne.thread.action import ExtractionAction
from src.automation.langgraph.nodes.theseus import TheseusNode


def make_snapshot(url="https://example.com") -> SnapshotResult:
    return SnapshotResult(url=url, html="<html/>")


def make_motor(success=True) -> AsyncMock:
    motor = AsyncMock()
    cmd = MotorCommand(operation="click", selector="#btn")
    trace = TraceEvent(command=cmd, success=success, error=None if success else "timeout")
    motor.act.return_value = ExecutionResult(success=success, trace_event=trace, error=trace.error)
    return motor


def make_registry(room_id=None, is_terminal=False, commands=None) -> MagicMock:
    lab = MagicMock()
    lab.identify_room.return_value = room_id
    room = MagicMock()
    room.state.is_terminal = is_terminal
    lab.get_room.return_value = room if room_id else None

    thread = MagicMock()
    thread.get_next_step.return_value = commands

    registry = MagicMock()
    registry.get.return_value = (lab, thread)
    return registry


def make_commands():
    return [MotorCommand(operation="click", selector="#btn")]


STATE = {"snapshot": make_snapshot(), "domain": "example.com"}


class TestTheseusNode:
    @pytest.mark.asyncio
    async def test_no_snapshot_returns_error(self):
        node = TheseusNode(make_motor(), make_registry())
        result = await node({"snapshot": None, "domain": "example.com"})
        assert result["errors"]

    @pytest.mark.asyncio
    async def test_unknown_room_returns_none_room_id(self):
        node = TheseusNode(make_motor(), make_registry(room_id=None))
        result = await node(STATE)
        assert result["current_room_id"] is None
        assert "trace" not in result or result.get("trace") == []

    @pytest.mark.asyncio
    async def test_known_room_no_step_returns_room_id_no_trace(self):
        node = TheseusNode(make_motor(), make_registry("home.anon", commands=None))
        result = await node(STATE)
        assert result["current_room_id"] == "home.anon"
        assert not result.get("trace")

    @pytest.mark.asyncio
    async def test_known_room_with_step_executes_and_traces(self):
        node = TheseusNode(make_motor(success=True), make_registry("home.anon", commands=make_commands()))
        result = await node(STATE)
        assert result["current_room_id"] == "home.anon"
        assert len(result["trace"]) == 1
        assert result["trace"][0].success is True

    @pytest.mark.asyncio
    async def test_trace_event_has_room_before(self):
        node = TheseusNode(make_motor(success=True), make_registry("home.anon", commands=make_commands()))
        result = await node(STATE)
        assert result["trace"][0].room_before == "home.anon"

    @pytest.mark.asyncio
    async def test_failed_command_stops_sequence(self):
        motor = AsyncMock()

        def act_side_effect(command):
            trace = TraceEvent(command=command, success=False, error="not found")
            return ExecutionResult(success=False, trace_event=trace, error="not found")

        motor.act = AsyncMock(side_effect=act_side_effect)
        commands = [
            MotorCommand(operation="click", selector="#btn1"),
            MotorCommand(operation="click", selector="#btn2"),
        ]
        node = TheseusNode(motor, make_registry("home.anon", commands=commands))
        result = await node(STATE)

        assert len(result["trace"]) == 1  # stopped after first failure
        assert result["errors"]

    @pytest.mark.asyncio
    async def test_multiple_commands_all_succeed(self):
        motor = AsyncMock()

        def act_side_effect(command):
            trace = TraceEvent(command=command, success=True)
            return ExecutionResult(success=True, trace_event=trace)

        motor.act = AsyncMock(side_effect=act_side_effect)
        commands = [
            MotorCommand(operation="fill",  selector="#email"),
            MotorCommand(operation="click", selector="#submit"),
        ]
        node = TheseusNode(motor, make_registry("login.form", commands=commands))
        result = await node(STATE)

        assert len(result["trace"]) == 2
        assert all(e.success for e in result["trace"])

    @pytest.mark.asyncio
    async def test_terminal_room_sets_mission_complete(self):
        node = TheseusNode(make_motor(), make_registry("success.page", is_terminal=True))
        result = await node(STATE)
        assert result["is_mission_complete"] is True
        assert result["current_room_id"] == "success.page"
        assert "trace" not in result


class TestExtractionDispatch:
    @pytest.mark.asyncio
    async def test_extraction_action_calls_extractor(self):
        extractor = AsyncMock()
        extractor.extract.return_value = [{"title": "Job A"}]
        step = [ExtractionAction(schema_id="jobs")]
        node = TheseusNode(make_motor(), make_registry("search.results", commands=step), extractor)
        result = await node(STATE)
        extractor.extract.assert_called_once()
        assert result["extracted_data"] == [{"title": "Job A"}]

    @pytest.mark.asyncio
    async def test_extraction_result_absent_when_empty(self):
        extractor = AsyncMock()
        extractor.extract.return_value = []
        step = [ExtractionAction(schema_id="jobs")]
        node = TheseusNode(make_motor(), make_registry("search.results", commands=step), extractor)
        result = await node(STATE)
        assert "extracted_data" not in result

    @pytest.mark.asyncio
    async def test_extraction_without_extractor_returns_empty(self):
        step = [ExtractionAction(schema_id="jobs")]
        node = TheseusNode(make_motor(), make_registry("search.results", commands=step))
        result = await node(STATE)
        assert "extracted_data" not in result

    @pytest.mark.asyncio
    async def test_mixed_step_runs_extraction_then_motor(self):
        extractor = AsyncMock()
        extractor.extract.return_value = [{"count": 42}]
        step = [ExtractionAction(schema_id="jobs"), MotorCommand(operation="click", selector="#next")]
        node = TheseusNode(make_motor(success=True), make_registry("search.results", commands=step), extractor)
        result = await node(STATE)
        assert result["extracted_data"] == [{"count": 42}]
        assert len(result["trace"]) == 1
