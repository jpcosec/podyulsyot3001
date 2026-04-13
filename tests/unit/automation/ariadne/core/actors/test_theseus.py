import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.automation.ariadne.core.actors import Theseus
from src.automation.ariadne.contracts.base import SnapshotResult, ExecutionResult
from src.automation.ariadne.models import AriadneMap, AriadneEdge

@pytest.fixture
def mock_cognition():
    labyrinth = MagicMock()
    labyrinth.ariadne_map = MagicMock()
    labyrinth.ariadne_map.states = {}
    labyrinth.identify_room = AsyncMock(return_value="home")
    
    thread = MagicMock()
    thread.get_next_step = MagicMock(return_value=AriadneEdge(
        from_state="home",
        to_state="job",
        intent="click",
        target="apply"
    ))
    
    return labyrinth, thread

@pytest.fixture
def mock_periphery():
    sensor = MagicMock()
    sensor.is_healthy = AsyncMock(return_value=True)
    sensor.perceive = AsyncMock(return_value=SnapshotResult(
        url="http://example.com/home",
        dom_elements=[]
    ))
    
    motor = MagicMock()
    motor.is_healthy = AsyncMock(return_value=True)
    motor.act = AsyncMock(return_value=ExecutionResult(status="success"))
    
    return sensor, motor

@pytest.mark.asyncio
async def test_theseus_observe_happy_path(mock_periphery, mock_cognition):
    sensor, motor = mock_periphery
    lab, thread = mock_cognition
    
    theseus = Theseus(sensor, motor, lab, thread)
    
    with patch("src.automation.ariadne.modes.registry.ModeRegistry.get_mode_for_url") as mock_mode:
        mock_mode.return_value = AsyncMock()
        
        updates = await theseus.observe({"portal_name": "test"}, {})
        
        assert updates["current_url"] == "http://example.com/home"
        assert updates["current_state_id"] == "home"
        sensor.perceive.assert_called_once()
        lab.identify_room.assert_called_once()

@pytest.mark.asyncio
async def test_theseus_execute_happy_path(mock_periphery, mock_cognition):
    sensor, motor = mock_periphery
    lab, thread = mock_cognition
    
    theseus = Theseus(sensor, motor, lab, thread)
    
    state = {
        "portal_name": "test",
        "current_state_id": "home"
    }
    config = {"configurable": {"motor_name": "browseros"}}
    
    with patch("src.automation.adapters.translators.registry.TranslatorRegistry.get_translator_by_name") as mock_trans:
        mock_translator = MagicMock()
        mock_translator.translate_intent.return_value = "click apply"
        mock_trans.return_value = mock_translator
        
        updates = await theseus.execute_deterministic(state, config)
        
        assert updates["current_state_id"] == "job"
        motor.act.assert_called_once()
        thread.get_next_step.assert_called_with("home")
