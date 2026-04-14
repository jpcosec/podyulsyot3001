import pytest
from unittest.mock import AsyncMock, MagicMock

from src.automation.contracts.motor import MotorCommand, TraceEvent, ExecutionResult
from src.automation.contracts.sensor import SnapshotResult
from src.automation.langgraph.nodes.delphi import DelphiNode, MAX_FAILURES, _parse_command, _build_prompt


def make_snapshot(html="<button id='go'>Go</button>", screenshot=None):
    return SnapshotResult(url="https://example.com/", html=html, screenshot_b64=screenshot)


def make_motor(success=True, error=None):
    motor = AsyncMock()
    cmd = MotorCommand(operation="click", selector="#go")
    trace = TraceEvent(command=cmd, success=success, error=error)
    motor.act.return_value = ExecutionResult(success=success, trace_event=trace, error=error)
    return motor


def make_labyrinth(dead_ends=None):
    lab = MagicMock()
    lab.known_dead_ends.return_value = dead_ends or []
    return lab


def make_llm(response='{"operation": "click", "selector": "#go"}'):
    llm = AsyncMock()
    llm.complete.return_value = response
    return llm


def make_node(success=True, llm_response='{"operation": "click", "selector": "#go"}'):
    return DelphiNode(make_motor(success), make_labyrinth(), make_llm(llm_response))


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_increments_failure_counter(self):
        result = await make_node()({"agent_failures": 0, "snapshot": make_snapshot()})
        assert result["agent_failures"] == 1

    @pytest.mark.asyncio
    async def test_accumulates_failures(self):
        result = await make_node()({"agent_failures": 2, "snapshot": make_snapshot()})
        assert result["agent_failures"] == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_triggers_at_max(self):
        result = await make_node()({"agent_failures": MAX_FAILURES - 1, "snapshot": make_snapshot()})
        assert result["agent_failures"] == MAX_FAILURES
        assert any("HITLRequired" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_no_snapshot_returns_error(self):
        result = await make_node()({"agent_failures": 0, "snapshot": None})
        assert any("no snapshot" in e for e in result["errors"])


class TestLLMReasoning:
    @pytest.mark.asyncio
    async def test_calls_llm_with_snapshot_html(self):
        llm = make_llm()
        node = DelphiNode(make_motor(), make_labyrinth(), llm)
        await node({"agent_failures": 0, "snapshot": make_snapshot()})
        llm.complete.assert_called_once()
        prompt_arg = llm.complete.call_args[0][0]
        assert "https://example.com/" in prompt_arg
        assert "<button" in prompt_arg

    @pytest.mark.asyncio
    async def test_passes_screenshot_when_present(self):
        llm = make_llm()
        node = DelphiNode(make_motor(), make_labyrinth(), llm)
        await node({"agent_failures": 0, "snapshot": make_snapshot(screenshot="abc123")})
        assert llm.complete.call_args[0][1] == "abc123"

    @pytest.mark.asyncio
    async def test_unparseable_llm_response_returns_error(self):
        result = await make_node(llm_response="no json here")({"agent_failures": 0, "snapshot": make_snapshot()})
        assert any("no parseable command" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_dead_ends_included_in_prompt(self):
        llm = make_llm()
        lab = make_labyrinth(dead_ends=["dead.room"])
        node = DelphiNode(make_motor(), lab, llm)
        await node({"agent_failures": 0, "snapshot": make_snapshot()})
        assert "dead.room" in llm.complete.call_args[0][0]


class TestExecution:
    @pytest.mark.asyncio
    async def test_successful_command_returns_trace(self):
        result = await make_node(success=True)({"agent_failures": 0, "snapshot": make_snapshot()})
        assert len(result["trace"]) == 1
        assert result["trace"][0].success is True

    @pytest.mark.asyncio
    async def test_failed_command_returns_error_and_trace(self):
        motor = make_motor(success=False, error="element not found")
        node = DelphiNode(motor, make_labyrinth(), make_llm())
        result = await node({"agent_failures": 0, "snapshot": make_snapshot()})
        assert any("element not found" in e for e in result["errors"])
        assert len(result["trace"]) == 1

    @pytest.mark.asyncio
    async def test_below_max_no_hitl_error(self):
        result = await make_node()({"agent_failures": 0, "snapshot": make_snapshot()})
        assert not any("HITLRequired" in e for e in result.get("errors", []))


class TestParseCommand:
    def test_parses_click(self):
        cmd = _parse_command('{"operation": "click", "selector": "#btn"}')
        assert cmd.operation == "click"
        assert cmd.selector == "#btn"

    def test_parses_fill_with_value(self):
        cmd = _parse_command('{"operation": "fill", "selector": "#email", "value": "a@b.com"}')
        assert cmd.value == "a@b.com"

    def test_returns_none_on_invalid_json(self):
        assert _parse_command("not json at all") is None

    def test_extracts_json_from_surrounding_text(self):
        cmd = _parse_command('Here is my suggestion:\n{"operation": "click", "selector": "#go"}\nDone.')
        assert cmd is not None
        assert cmd.operation == "click"
