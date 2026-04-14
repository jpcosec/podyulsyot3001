import pytest
from src.automation.langgraph.nodes.interpreter import InterpreterNode, _parse


class TestParse:
    def test_splits_portal_and_mission(self):
        assert _parse("stepstone/easy_apply") == ("stepstone", "easy_apply")

    def test_handles_whitespace(self):
        assert _parse("  stepstone / easy_apply  ") == ("stepstone", "easy_apply")

    def test_no_slash_defaults_mission(self):
        portal, mission = _parse("stepstone")
        assert portal == "stepstone"
        assert mission == "default"

    def test_empty_string(self):
        portal, mission = _parse("")
        assert mission == "default"


class TestInterpreterNode:
    @pytest.mark.asyncio
    async def test_seeds_state(self):
        node = InterpreterNode()
        result = await node({"instruction": "stepstone/easy_apply"})
        assert result["portal_name"] == "stepstone"
        assert result["mission_id"] == "easy_apply"
        assert result["current_room_id"] is None
        assert result["agent_failures"] == 0

    @pytest.mark.asyncio
    async def test_resets_failure_counter(self):
        node = InterpreterNode()
        result = await node({"instruction": "portal/mission", "agent_failures": 99})
        assert result["agent_failures"] == 0
