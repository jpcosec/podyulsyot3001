import pytest
from unittest.mock import MagicMock

from src.automation.contracts.motor import MotorCommand, TraceEvent
from src.automation.langgraph.nodes.recorder import RecorderNode


def make_trace(success=True, room_before="home.anon") -> TraceEvent:
    cmd = MotorCommand(operation="click", selector="#btn")
    return TraceEvent(command=cmd, success=success, room_before=room_before)


def make_registry() -> MagicMock:
    lab = MagicMock()
    thread = MagicMock()
    registry = MagicMock()
    registry.get.return_value = (lab, thread)
    return registry


def state(trace, room_id="results.page", domain="example.com"):
    return {"trace": trace, "current_room_id": room_id, "domain": domain}


class TestRecorderNode:
    @pytest.mark.asyncio
    async def test_successful_trace_calls_add_step(self):
        registry = make_registry()
        node = RecorderNode(registry)
        trace = [make_trace(success=True)]
        await node(state(trace))
        _, thread = registry.get.return_value
        thread.add_step.assert_called_once_with(trace[0], "results.page")

    @pytest.mark.asyncio
    async def test_failed_trace_skips_add_step(self):
        registry = make_registry()
        node = RecorderNode(registry)
        await node(state([make_trace(success=False)]))
        _, thread = registry.get.return_value
        thread.add_step.assert_not_called()

    @pytest.mark.asyncio
    async def test_saves_after_successful_trace(self):
        registry = make_registry()
        node = RecorderNode(registry)
        await node(state([make_trace()]))
        registry.save.assert_called_once_with("example.com")

    @pytest.mark.asyncio
    async def test_no_save_on_empty_trace(self):
        registry = make_registry()
        node = RecorderNode(registry)
        await node(state([]))
        registry.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_empty_dict(self):
        node = RecorderNode(make_registry())
        result = await node(state([make_trace()]))
        assert result == {}

    @pytest.mark.asyncio
    async def test_multiple_events_in_trace(self):
        registry = make_registry()
        node = RecorderNode(registry)
        trace = [make_trace(success=True), make_trace(success=False), make_trace(success=True)]
        await node(state(trace))
        _, thread = registry.get.return_value
        assert thread.add_step.call_count == 2  # only the two successful ones

    @pytest.mark.asyncio
    async def test_uses_domain_from_state(self):
        registry = make_registry()
        node = RecorderNode(registry)
        await node(state([make_trace()], domain="emol.com"))
        registry.get.assert_called_with("emol.com")
        registry.save.assert_called_with("emol.com")
