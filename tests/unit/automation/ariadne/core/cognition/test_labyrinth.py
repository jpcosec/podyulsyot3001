import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.automation.ariadne.core.cognition.labyrinth import Labyrinth
from src.automation.ariadne.contracts.base import SnapshotResult
from src.automation.ariadne.models import AriadneMap
from src.automation.ariadne.exceptions import MapNotFoundError

@pytest.fixture
def mock_map_payload():
    return {
        "meta": {
            "source": "test_portal",
            "flow": "easy_apply",
            "version": "v1",
            "status": "draft"
        },
        "states": {
            "home": {
                "id": "home",
                "description": "Home Page",
                "presence_predicate": {
                    "url_contains": "home",
                    "required_elements": [{"text": "Welcome"}]
                }
            }
        },
        "edges": [],
        "success_states": ["success"],
        "failure_states": ["error"]
    }

@pytest.mark.asyncio
async def test_labyrinth_load_success(mock_map_payload):
    with patch("src.automation.ariadne.core.cognition.labyrinth.read_json_async", new_callable=AsyncMock) as mock_read:
        mock_read.return_value = mock_map_payload
        
        lab = await Labyrinth.load_from_db("test_portal")
        
        assert lab.ariadne_map.meta.source == "test_portal"
        assert "home" in lab.ariadne_map.states

@pytest.mark.asyncio
async def test_labyrinth_load_failure():
    with patch("src.automation.ariadne.core.cognition.labyrinth.read_json_async", new_callable=AsyncMock) as mock_read:
        mock_read.side_effect = FileNotFoundError()
        
        with pytest.raises(MapNotFoundError):
            await Labyrinth.load_from_db("missing_portal")

@pytest.mark.asyncio
async def test_identify_room(mock_map_payload):
    ariadne_map = AriadneMap.model_validate(mock_map_payload)
    lab = Labyrinth(ariadne_map=ariadne_map)
    
    # Matching snapshot
    snapshot = SnapshotResult(
        url="https://example.com/home",
        dom_elements=[{"text": "Welcome to my home"}]
    )
    room = await lab.identify_room(snapshot)
    assert room == "home"
    
    # Non-matching snapshot (wrong URL)
    snapshot_wrong = SnapshotResult(
        url="https://example.com/other",
        dom_elements=[{"text": "Welcome"}]
    )
    assert await lab.identify_room(snapshot_wrong) is None
