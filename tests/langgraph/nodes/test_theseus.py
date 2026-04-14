import dataclasses
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.automation.contracts.sensor import SnapshotResult
from src.automation.contracts.motor import MotorCommand, TraceEvent, ExecutionResult
from src.automation.langgraph.nodes.theseus import TheseusNode


def make_snapshot(url="https://example.com") -> SnapshotResult:
    return SnapshotResult(url=url, html="<html/>")


def make_motor(success=True) -> AsyncMock:
    motor = AsyncMock()
    cmd = MotorCommand(operation="click", selector="#btn")
    trace = TraceEvent(command=cmd, success=success, error=None if success else "timeout")
    motor.act.return_value = ExecutionResult(success=success, trace_event=trace, error=trace.error)
    return motor


def make_labyrinth(room_id=None, is_terminal=False) -> MagicMock:
    lab = MagicMock()
    lab.identify_room.return_value = room_id
    room = MagicMock()
    room.state.is_terminal = is_terminal
    lab.get_room.return_value = room if room_id else None
    return lab


def make_thread(commands=None) -> MagicMock:
    thread = MagicMock()
    thread.get_next_step.return_value = commands
    return thread


def make_commands():
    return [MotorCommand(operation="click", selector="#btn")]


class TestTheseusNode:
    @pytest.mark.asyncio
    async def test_no_snapshot_returns_error(self):
        node = TheseusNode(make_motor(), make_labyrinth(), make_thread())
        result = await node({"snapshot": None})
        assert result["errors"]

    @pytest.mark.asyncio
    async def test_unknown_room_returns_none_room_id(self):
        node = TheseusNode(make_motor(), make_labyrinth(room_id=None), make_thread())
        result = await node({"snapshot": make_snapshot()})
        assert result["current_room_id"] is None
        assert "trace" not in result or result.get("trace") == []

    @pytest.mark.asyncio
    async def test_known_room_no_step_returns_room_id_no_trace(self):
        node = TheseusNode(make_motor(), make_labyrinth("home.anon"), make_thread(commands=None))
        result = await node({"snapshot": make_snapshot()})
        assert result["current_room_id"] == "home.anon"
        assert not result.get("trace")

    @pytest.mark.asyncio
    async def test_known_room_with_step_executes_and_traces(self):
        node = TheseusNode(make_motor(success=True), make_labyrinth("home.anon"), make_thread(make_commands()))
        result = await node({"snapshot": make_snapshot()})
        assert result["current_room_id"] == "home.anon"
        assert len(result["trace"]) == 1
        assert result["trace"][0].success is True

    @pytest.mark.asyncio
    async def test_trace_event_has_room_before(self):
        node = TheseusNode(make_motor(success=True), make_labyrinth("home.anon"), make_thread(make_commands()))
        result = await node({"snapshot": make_snapshot()})
        assert result["trace"][0].room_before == "home.anon"

    @pytest.mark.asyncio
    async def test_failed_command_stops_sequence(self):
        motor = AsyncMock()
        cmd = MotorCommand(operation="click", selector="#btn")

        def act_side_effect(command):
            trace = TraceEvent(command=command, success=False, error="not found")
            return ExecutionResult(success=False, trace_event=trace, error="not found")

        motor.act = AsyncMock(side_effect=act_side_effect)
        commands = [
            MotorCommand(operation="click", selector="#btn1"),
            MotorCommand(operation="click", selector="#btn2"),
        ]
        node = TheseusNode(motor, make_labyrinth("home.anon"), make_thread(commands))
        result = await node({"snapshot": make_snapshot()})

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
        node = TheseusNode(motor, make_labyrinth("login.form"), make_thread(commands))
        result = await node({"snapshot": make_snapshot()})

        assert len(result["trace"]) == 2
        assert all(e.success for e in result["trace"])

    @pytest.mark.asyncio
    async def test_terminal_room_sets_mission_complete(self):
        node = TheseusNode(make_motor(), make_labyrinth("success.page", is_terminal=True), make_thread())
        result = await node({"snapshot": make_snapshot()})
        assert result["is_mission_complete"] is True
        assert result["current_room_id"] == "success.page"
        assert "trace" not in result
