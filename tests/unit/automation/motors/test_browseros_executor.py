"""Tests for BrowserOS executor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.automation.motors.browseros.executor import BrowserOSCliExecutor
from src.automation.ariadne.contracts.base import (
    BrowserOSCommand,
    CrawlCommand,
    SnapshotResult,
)


def create_mock_tools():
    """Create mock MCP tools."""
    click_tool = MagicMock()
    click_tool.name = "click"
    click_tool.ainvoke = AsyncMock(return_value='{"status": "clicked"}')

    fill_tool = MagicMock()
    fill_tool.name = "fill"
    fill_tool.ainvoke = AsyncMock(return_value='{"status": "filled"}')

    press_tool = MagicMock()
    press_tool.name = "press"
    press_tool.ainvoke = AsyncMock(return_value='{"status": "pressed"}')

    upload_tool = MagicMock()
    upload_tool.name = "upload"
    upload_tool.ainvoke = AsyncMock(return_value='{"status": "uploaded"}')

    snapshot_tool = MagicMock()
    snapshot_tool.name = "take_snapshot"
    snapshot_tool.ainvoke = AsyncMock(
        return_value='{"url": "https://example.com", "dom_elements": [], "screenshot_b64": "abc123"}'
    )

    return [click_tool, fill_tool, press_tool, upload_tool, snapshot_tool]


@pytest.fixture
def mock_load_mcp_tools():
    """Create a patched load_mcp_tools function."""
    mock_tools = create_mock_tools()
    with patch(
        "src.automation.motors.browseros.executor.load_mcp_tools",
        new_callable=AsyncMock,
        return_value=mock_tools,
    ) as mock_load:
        yield mock_load, mock_tools


class TestBrowserOSCliExecutor:
    """Tests for BrowserOSCliExecutor."""

    @pytest.mark.asyncio
    async def test_take_snapshot_returns_snapshot_result(self, mock_load_mcp_tools):
        """Test that take_snapshot returns a valid SnapshotResult."""
        mock_load, mock_tools = mock_load_mcp_tools
        executor = BrowserOSCliExecutor(mcp_url="http://test.local/mcp")

        result = await executor.take_snapshot()

        assert isinstance(result, SnapshotResult)
        assert result.url == "https://example.com"
        assert result.dom_elements == []
        assert result.screenshot_b64 == "abc123"

    @pytest.mark.asyncio
    async def test_take_snapshot_handles_missing_tool(self):
        """Test take_snapshot when take_snapshot tool is not available."""
        with patch(
            "src.automation.motors.browseros.executor.load_mcp_tools",
            new_callable=AsyncMock,
            return_value=[],
        ):
            executor = BrowserOSCliExecutor()

            result = await executor.take_snapshot()

            assert result.url == "error"
            assert result.dom_elements == []

    @pytest.mark.asyncio
    async def test_execute_click_command(self, mock_load_mcp_tools):
        """Test executing a click command."""
        mock_load, mock_tools = mock_load_mcp_tools
        executor = BrowserOSCliExecutor()
        command = BrowserOSCommand(tool="click", selector_text=".button")

        result = await executor.execute(command)

        assert result.status == "success"
        assert "mcp_output" in result.extracted_data

    @pytest.mark.asyncio
    async def test_execute_fill_command(self, mock_load_mcp_tools):
        """Test executing a fill command."""
        mock_load, mock_tools = mock_load_mcp_tools
        executor = BrowserOSCliExecutor()
        command = BrowserOSCommand(
            tool="fill", selector_text="#input", value="test text"
        )

        result = await executor.execute(command)

        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_execute_press_command(self, mock_load_mcp_tools):
        """Test executing a press command."""
        mock_load, mock_tools = mock_load_mcp_tools
        executor = BrowserOSCliExecutor()
        command = BrowserOSCommand(tool="press", selector_text="body", value="Enter")

        result = await executor.execute(command)

        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_execute_upload_command(self, mock_load_mcp_tools):
        """Test executing an upload command."""
        mock_load, mock_tools = mock_load_mcp_tools
        executor = BrowserOSCliExecutor()
        command = BrowserOSCommand(
            tool="upload", selector_text="input[type=file]", value="/path/to/file.pdf"
        )

        result = await executor.execute(command)

        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_execute_wrong_command_type_returns_error(self):
        """Test that executing a non-BrowserOSCommand returns an error."""
        with patch(
            "src.automation.motors.browseros.executor.load_mcp_tools",
            new_callable=AsyncMock,
        ):
            executor = BrowserOSCliExecutor()
            command = CrawlCommand(c4a_script="some script")  # Wrong type

            result = await executor.execute(command)

            assert result.status == "failed"
            assert "BrowserOSCliExecutor only handles BrowserOSCommand" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_not_found_returns_error(self):
        """Test executing when requested tool is not in the available tools."""
        # Use a tool list that doesn't include 'nonexistent'
        with patch(
            "src.automation.motors.browseros.executor.load_mcp_tools",
            new_callable=AsyncMock,
        ) as mock_load:
            click_tool = MagicMock()
            click_tool.name = "click"
            mock_load.return_value = [click_tool]

            executor = BrowserOSCliExecutor()
            # Use a valid tool name that's not in the available tools
            command = BrowserOSCommand(tool="fill", selector_text=".button")

            result = await executor.execute(command)

            assert result.status == "failed"
            assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_exception_returns_failed_result(self):
        """Test that exceptions are caught and returned as failed results."""
        with patch(
            "src.automation.motors.browseros.executor.load_mcp_tools",
            new_callable=AsyncMock,
        ) as mock_load:
            mock_tool = MagicMock()
            mock_tool.name = "click"
            mock_tool.ainvoke = AsyncMock(side_effect=Exception("Connection failed"))
            mock_load.return_value = [mock_tool]

            executor = BrowserOSCliExecutor()
            command = BrowserOSCommand(tool="click", selector_text=".button")

            result = await executor.execute(command)

            assert result.status == "failed"
            assert "Connection failed" in result.error

    @pytest.mark.asyncio
    async def test_take_snapshot_json_parse_error(self):
        """Test that take_snapshot handles non-JSON results gracefully."""
        with patch(
            "src.automation.motors.browseros.executor.load_mcp_tools",
            new_callable=AsyncMock,
        ) as mock_load:
            mock_tool = MagicMock()
            mock_tool.name = "take_snapshot"
            mock_tool.ainvoke = AsyncMock(return_value="not json")  # Non-JSON response
            mock_load.return_value = [mock_tool]

            executor = BrowserOSCliExecutor()
            result = await executor.take_snapshot()

            # Should return default values when JSON parsing fails
            assert result.url == "unknown"
            assert result.screenshot_b64 is None
