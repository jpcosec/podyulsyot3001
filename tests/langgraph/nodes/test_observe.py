import pytest
from unittest.mock import AsyncMock

from src.automation.contracts.sensor import SnapshotResult
from src.automation.langgraph.nodes.observe import ObserveNode


def make_snapshot(**kwargs) -> SnapshotResult:
    defaults = dict(url="https://example.com", html="<html/>", status_code=200)
    return SnapshotResult(**{**defaults, **kwargs})


def make_sensor(healthy=True, snapshot=None) -> AsyncMock:
    sensor = AsyncMock()
    sensor.is_healthy.return_value = healthy
    sensor.perceive.return_value = snapshot or make_snapshot()
    return sensor


class TestObserveNode:
    @pytest.mark.asyncio
    async def test_healthy_sensor_returns_snapshot(self):
        snap = make_snapshot(url="https://stepstone.de")
        node = ObserveNode(make_sensor(snapshot=snap))
        result = await node({"agent_failures": 0})
        assert result["snapshot"].url == "https://stepstone.de"

    @pytest.mark.asyncio
    async def test_unhealthy_sensor_returns_fatal_error(self):
        node = ObserveNode(make_sensor(healthy=False))
        result = await node({"agent_failures": 0})
        assert any("FatalError" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_no_screenshot_on_fast_path(self):
        sensor = make_sensor()
        node = ObserveNode(sensor)
        await node({"agent_failures": 0})
        sensor.perceive.assert_called_once_with(with_screenshot=False)

    @pytest.mark.asyncio
    async def test_screenshot_requested_on_cold_path(self):
        sensor = make_sensor()
        node = ObserveNode(sensor)
        await node({"agent_failures": 1})
        sensor.perceive.assert_called_once_with(with_screenshot=True)

    @pytest.mark.asyncio
    async def test_screenshot_requested_on_repeated_failures(self):
        sensor = make_sensor()
        node = ObserveNode(sensor)
        await node({"agent_failures": 3})
        sensor.perceive.assert_called_once_with(with_screenshot=True)
