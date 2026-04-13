import pytest
from src.automation.ariadne.core.periphery import Sensor, Motor, BrowserAdapter
from src.automation.ariadne.contracts.base import SnapshotResult, ExecutionResult, MotorCommand

class MockAdapter(BrowserAdapter):
    async def perceive(self) -> SnapshotResult:
        return SnapshotResult(url="test", dom_elements=[], screenshot_b64=None)
    
    async def act(self, command: MotorCommand) -> ExecutionResult:
        return ExecutionResult(status="success")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

def test_adapter_is_sensor_and_motor():
    adapter = MockAdapter()
    assert isinstance(adapter, Sensor)
    assert isinstance(adapter, Motor)
    assert isinstance(adapter, BrowserAdapter)

@pytest.mark.asyncio
async def test_adapter_methods():
    adapter = MockAdapter()
    snapshot = await adapter.perceive()
    assert snapshot.url == "test"
    
    result = await adapter.act(MotorCommand())
    assert result.status == "success"
