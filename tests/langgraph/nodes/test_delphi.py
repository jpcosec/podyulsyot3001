import pytest
from src.automation.langgraph.nodes.delphi import DelphiNode, MAX_FAILURES


class TestDelphiNode:
    @pytest.mark.asyncio
    async def test_increments_failure_counter(self):
        node = DelphiNode()
        result = await node({"agent_failures": 0})
        assert result["agent_failures"] == 1

    @pytest.mark.asyncio
    async def test_accumulates_failures(self):
        node = DelphiNode()
        result = await node({"agent_failures": 2})
        assert result["agent_failures"] == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_triggers_at_max(self):
        node = DelphiNode()
        result = await node({"agent_failures": MAX_FAILURES - 1})
        assert result["agent_failures"] == MAX_FAILURES
        assert any("circuit breaker" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_below_max_returns_no_errors(self):
        node = DelphiNode()
        result = await node({"agent_failures": 0})
        assert "errors" not in result or result.get("errors") == []
