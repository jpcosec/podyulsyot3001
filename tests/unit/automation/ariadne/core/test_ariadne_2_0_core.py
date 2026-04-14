import pytest
from unittest.mock import MagicMock, AsyncMock

from src.automation.ariadne.core.periphery import Sensor, Motor
from src.automation.ariadne.core.cognition.labyrinth import Labyrinth
from src.automation.ariadne.core.cognition.thread import AriadneThread
from src.automation.ariadne.core.actors.theseus import Theseus
from src.automation.ariadne.models import AriadneMap

def test_labyrinth_structure():
    mock_map = MagicMock(spec=AriadneMap)
    mock_map.states = {}
    lab = Labyrinth(ariadne_map=mock_map)
    assert hasattr(lab, "identify_room")
    assert hasattr(lab, "expand")

def test_thread_structure():
    thread = AriadneThread(edges=[], mission_id="test")
    assert hasattr(thread, "get_next_step")
    assert hasattr(thread, "add_step")

def test_theseus_structure():
    sensor = MagicMock(spec=Sensor)
    motor = MagicMock(spec=Motor)
    lab = MagicMock(spec=Labyrinth)
    thread = MagicMock(spec=AriadneThread)
    
    theseus = Theseus(sensor, motor, lab, thread)
    assert hasattr(theseus, "observe")
    assert hasattr(theseus, "execute_deterministic")
    assert hasattr(theseus, "build_graph")

@pytest.mark.asyncio
async def test_theseus_observe_flow():
    sensor = MagicMock(spec=Sensor)
    sensor.is_healthy = AsyncMock(return_value=True)
    sensor.perceive = AsyncMock()
    
    motor = MagicMock(spec=Motor)
    lab = MagicMock(spec=Labyrinth)
    lab.identify_room = AsyncMock(return_value="home")
    lab.ariadne_map = MagicMock()
    
    thread = MagicMock(spec=AriadneThread)
    
    theseus = Theseus(sensor, motor, lab, thread)
    state = {"session_memory": {}}
    
    updates = await theseus.observe(state)
    
    assert updates["current_state_id"] == "home"
    sensor.perceive.assert_called_once()
    lab.identify_room.assert_called_once()
