import pytest
from unittest.mock import AsyncMock, patch
from src.automation.ariadne.core.cognition.thread import AriadneThread
from src.automation.ariadne.models import AriadneMap, AriadneEdge

@pytest.fixture
def mock_thread_payload():
    return {
        "meta": {
            "source": "test_portal",
            "flow": "easy_apply",
            "version": "v1",
            "status": "draft"
        },
        "states": {},
        "edges": [
            {
                "from_state": "home",
                "to_state": "job",
                "mission_id": "apply",
                "intent": "click",
                "target": "apply_button"
            },
            {
                "from_state": "home",
                "to_state": "settings",
                "mission_id": "config",
                "intent": "click",
                "target": "settings_button"
            }
        ],
        "success_states": [],
        "failure_states": []
    }

@pytest.mark.asyncio
async def test_thread_load_mission_filtering(mock_thread_payload):
    with patch("src.automation.ariadne.core.cognition.thread.read_json_async", new_callable=AsyncMock) as mock_read:
        mock_read.return_value = mock_thread_payload
        
        # Load specific mission
        thread = await AriadneThread.load_from_db("test_portal", mission_id="apply")
        assert len(thread.edges) == 1
        assert thread.edges[0].mission_id == "apply"
        assert thread.mission_id == "apply"
        
        # Load all missions
        thread_all = await AriadneThread.load_from_db("test_portal")
        assert len(thread_all.edges) == 2
        assert thread_all.available_missions() == ["apply", "config"]

def test_thread_get_next_step(mock_thread_payload):
    ariadne_map = AriadneMap.model_validate(mock_thread_payload)
    thread = AriadneThread(edges=ariadne_map.edges, mission_id="apply")
    
    # Matching step
    step = thread.get_next_step("home")
    assert step is not None
    assert step.to_state == "job"
    
    # Non-matching step
    assert thread.get_next_step("job") is None
