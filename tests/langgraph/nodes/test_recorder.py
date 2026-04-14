import pytest
from unittest.mock import MagicMock, patch

from src.automation.contracts.motor import MotorCommand, TraceEvent
from src.automation.langgraph.nodes.recorder import RecorderNode


def make_trace(success=True, room_before="home.anon") -> TraceEvent:
    cmd = MotorCommand(operation="click", selector="#btn")
    return TraceEvent(command=cmd, success=success, room_before=room_before)


def make_mocks():
    labyrinth = MagicMock()
    thread = MagicMock()
    return labyrinth, thread


class TestRecorderNode:
    @pytest.mark.asyncio
    async def test_successful_trace_calls_add_step(self):
        lab, thread = make_mocks()
        node = RecorderNode(lab, thread)
        trace = [make_trace(success=True)]
        await node({"trace": trace, "current_room_id": "results.page"})
        thread.add_step.assert_called_once_with(trace[0], "results.page")

    @pytest.mark.asyncio
    async def test_failed_trace_skips_add_step(self):
        lab, thread = make_mocks()
        node = RecorderNode(lab, thread)
        trace = [make_trace(success=False)]
        await node({"trace": trace, "current_room_id": "results.page"})
        thread.add_step.assert_not_called()

    @pytest.mark.asyncio
    async def test_saves_after_successful_trace(self):
        lab, thread = make_mocks()
        node = RecorderNode(lab, thread)
        await node({"trace": [make_trace()], "current_room_id": "results.page"})
        thread.save.assert_called_once()
        lab.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_save_on_empty_trace(self):
        lab, thread = make_mocks()
        node = RecorderNode(lab, thread)
        await node({"trace": [], "current_room_id": "results.page"})
        thread.save.assert_not_called()
        lab.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_empty_dict(self):
        lab, thread = make_mocks()
        node = RecorderNode(lab, thread)
        result = await node({"trace": [make_trace()], "current_room_id": "results.page"})
        assert result == {}

    @pytest.mark.asyncio
    async def test_multiple_events_in_trace(self):
        lab, thread = make_mocks()
        node = RecorderNode(lab, thread)
        trace = [make_trace(success=True), make_trace(success=False), make_trace(success=True)]
        await node({"trace": trace, "current_room_id": "results.page"})
        assert thread.add_step.call_count == 2  # only the two successful ones
