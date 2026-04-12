"""Tests for Crawl4AI executor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.automation.motors.crawl4ai.executor import Crawl4AIExecutor
from src.automation.ariadne.contracts.base import (
    BrowserOSCommand,
    CrawlCommand,
    SnapshotResult,
)


class MockCrawlerRunConfig:
    """Mock CrawlerRunConfig that accepts all parameters."""

    def __init__(self, **kwargs):
        self.c4a_script = kwargs.get("c4a_script")
        self.cache_mode = kwargs.get("cache_mode")
        self.screenshot = kwargs.get("screenshot", False)
        self.js_code = kwargs.get("js_code")


@pytest.fixture
def mock_crawler_result():
    """Create a mock Crawl4AI crawl result."""
    result = MagicMock()
    result.success = True
    result.url = "https://example.com"
    result.screenshot = "base64screenshot"
    result.js_script_result = None
    result.error_message = None
    return result


@pytest.fixture
def mock_crawler_result_with_script():
    """Create a mock Crawl4AI crawl result with script result."""
    result = MagicMock()
    result.success = True
    result.url = "https://example.com"
    result.screenshot = "base64screenshot"
    result.js_script_result = {"completed_count": 5}
    result.error_message = None
    return result


@pytest.fixture
def mock_crawler_result_with_failure():
    """Create a mock Crawl4AI crawl result with batch failure."""
    result = MagicMock()
    result.success = True
    result.url = "https://example.com"
    result.screenshot = "base64screenshot"
    result.js_script_result = {
        "failed_at": 2,
        "completed_count": 2,
        "error": "Action failed",
    }
    result.error_message = None
    return result


@pytest.fixture
def mock_crawler_result_failed():
    """Create a mock Crawl4AI crawl result that failed entirely."""
    result = MagicMock()
    result.success = False
    result.url = "https://example.com"
    result.screenshot = None
    result.js_script_result = None
    result.error_message = "Network error"
    return result


@pytest.fixture
def executor():
    """Create a Crawl4AIExecutor instance."""
    return Crawl4AIExecutor()


class TestCrawl4AIExecutorContextManager:
    """Tests for Crawl4AIExecutor async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_enters_and_creates_crawler(self):
        """Test that __aenter__ creates the persistent crawler."""
        executor = Crawl4AIExecutor()

        with patch(
            "src.automation.motors.crawl4ai.executor.AsyncWebCrawler"
        ) as mock_crawler_class:
            mock_crawler = AsyncMock()
            mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
            mock_crawler.__aexit__ = AsyncMock(return_value=None)
            mock_crawler_class.return_value = mock_crawler

            async with executor as entered_executor:
                assert entered_executor is executor
                assert executor._crawler is mock_crawler
                mock_crawler.__aenter__.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_exits_and_destroys_crawler(self):
        """Test that __aexit__ properly closes the crawler."""
        executor = Crawl4AIExecutor()

        with patch(
            "src.automation.motors.crawl4ai.executor.AsyncWebCrawler"
        ) as mock_crawler_class:
            mock_crawler = AsyncMock()
            mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
            mock_crawler.__aexit__ = AsyncMock(return_value=None)
            mock_crawler_class.return_value = mock_crawler

            async with executor as entered_executor:
                await executor.__aexit__(None, None, None)
                mock_crawler.__aexit__.assert_called_once()
                assert executor._crawler is None

    @pytest.mark.asyncio
    async def test_context_manager_session_id_set(self):
        """Test that session_id is set correctly."""
        executor = Crawl4AIExecutor()

        with patch(
            "src.automation.motors.crawl4ai.executor.AsyncWebCrawler"
        ) as mock_crawler_class:
            mock_crawler = AsyncMock()
            mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
            mock_crawler.__aexit__ = AsyncMock(return_value=None)
            mock_crawler_class.return_value = mock_crawler

            async with executor as entered_executor:
                assert executor._session_id == "ariadne-session"


class TestCrawl4AIExecutor:
    """Tests for Crawl4AIExecutor."""

    @pytest.fixture
    def setup_mocked_executor(self, executor):
        """Create executor with mocked crawler for tests."""
        mock_crawler = AsyncMock()
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        executor._crawler = mock_crawler
        return executor

    @pytest.mark.asyncio
    async def test_take_snapshot_returns_snapshot_result(
        self, mock_crawler_result, setup_mocked_executor
    ):
        """Test that take_snapshot returns a valid SnapshotResult."""
        executor = setup_mocked_executor
        executor._crawler.arun = AsyncMock(return_value=mock_crawler_result)

        with patch(
            "src.automation.motors.crawl4ai.executor.CrawlerRunConfig",
            MockCrawlerRunConfig,
        ):
            result = await executor.take_snapshot()

            assert isinstance(result, SnapshotResult)
            assert result.url == "https://example.com"
            assert result.screenshot_b64 == "base64screenshot"

    @pytest.mark.asyncio
    async def test_take_snapshot_handles_failed_crawl(
        self, mock_crawler_result_failed, setup_mocked_executor
    ):
        """Test that take_snapshot handles failed crawl gracefully."""
        executor = setup_mocked_executor
        executor._crawler.arun = AsyncMock(return_value=mock_crawler_result_failed)

        with patch(
            "src.automation.motors.crawl4ai.executor.CrawlerRunConfig",
            MockCrawlerRunConfig,
        ):
            result = await executor.take_snapshot()

            # Returns the result URL even on failure (the URL is still known)
            assert result.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_execute_crawl_command_success(
        self, mock_crawler_result_with_script, setup_mocked_executor
    ):
        """Test executing a CrawlCommand successfully."""
        executor = setup_mocked_executor
        executor._crawler.arun = AsyncMock(return_value=mock_crawler_result_with_script)

        with patch(
            "src.automation.motors.crawl4ai.executor.CrawlerRunConfig",
            MockCrawlerRunConfig,
        ):
            command = CrawlCommand(c4a_script="await page.click('button')")
            result = await executor.execute(command)

            assert result.status == "success"
            assert result.completed_count == 5

    @pytest.mark.asyncio
    async def test_execute_crawl_command_batch_failure(
        self, mock_crawler_result_with_failure, setup_mocked_executor
    ):
        """Test executing a CrawlCommand with batch failure."""
        executor = setup_mocked_executor
        executor._crawler.arun = AsyncMock(
            return_value=mock_crawler_result_with_failure
        )

        with patch(
            "src.automation.motors.crawl4ai.executor.CrawlerRunConfig",
            MockCrawlerRunConfig,
        ):
            command = CrawlCommand(c4a_script="await page.click('button')")
            result = await executor.execute(command)

            assert result.status == "failed"
            assert result.failed_at_index == 2
            assert result.completed_count == 2

    @pytest.mark.asyncio
    async def test_execute_crawl_command_full_success(
        self, mock_crawler_result, setup_mocked_executor
    ):
        """Test executing a CrawlCommand with full success (no script result)."""
        executor = setup_mocked_executor
        executor._crawler.arun = AsyncMock(return_value=mock_crawler_result)

        with patch(
            "src.automation.motors.crawl4ai.executor.CrawlerRunConfig",
            MockCrawlerRunConfig,
        ):
            command = CrawlCommand(c4a_script="await page.click('button')")
            result = await executor.execute(command)

            assert result.status == "success"

    @pytest.mark.asyncio
    async def test_execute_wrong_command_type_returns_error(self, executor):
        """Test that executing a non-CrawlCommand returns an error."""
        command = BrowserOSCommand(tool="click", selector_text=".button")

        result = await executor.execute(command)

        assert result.status == "failed"
        assert "Invalid command type" in result.error

    @pytest.mark.asyncio
    async def test_execute_crawl_failure_returns_error(
        self, mock_crawler_result_failed, setup_mocked_executor
    ):
        """Test that crawl failure is properly reported."""
        executor = setup_mocked_executor
        executor._crawler.arun = AsyncMock(return_value=mock_crawler_result_failed)

        with patch(
            "src.automation.motors.crawl4ai.executor.CrawlerRunConfig",
            MockCrawlerRunConfig,
        ):
            command = CrawlCommand(c4a_script="await page.click('button')")
            result = await executor.execute(command)

            assert result.status == "failed"
            assert "Network error" in result.error

    @pytest.mark.asyncio
    async def test_execute_exception_returns_failed_result(self, setup_mocked_executor):
        """Test that exceptions are caught and returned as failed results."""
        executor = setup_mocked_executor
        executor._crawler.arun = AsyncMock(
            side_effect=Exception("Crawl4AI connection error")
        )

        with patch(
            "src.automation.motors.crawl4ai.executor.CrawlerRunConfig",
            MockCrawlerRunConfig,
        ):
            command = CrawlCommand(c4a_script="await page.click('button')")
            result = await executor.execute(command)

            assert result.status == "failed"
            assert "Crawl4AI connection error" in result.error

    @pytest.mark.asyncio
    async def test_execute_updates_current_url_on_success(
        self, mock_crawler_result_with_script, setup_mocked_executor
    ):
        """Test that current_url is updated on successful crawl."""
        executor = setup_mocked_executor
        executor._crawler.arun = AsyncMock(return_value=mock_crawler_result_with_script)

        with patch(
            "src.automation.motors.crawl4ai.executor.CrawlerRunConfig",
            MockCrawlerRunConfig,
        ):
            executor.current_url = "about:blank"
            command = CrawlCommand(c4a_script="await page.click('button')")
            result = await executor.execute(command)

            assert executor.current_url == "https://example.com"
